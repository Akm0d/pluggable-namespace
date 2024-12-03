import asyncio
import importlib.machinery
import os
import secrets
import signal
import sys
import warnings
from collections.abc import Awaitable, Iterable
from contextvars import copy_context
from types import ModuleType

import cpns.contract
import cpns.data
import pns.dirs
import pns.exc
import pns.loader
import pns.ref
import pns.scanner
import pns.verify


def ex_path(path):
    """
    Take a path that is sent to the Sub and expand it if it is a string or not
    """
    if isinstance(path, str):
        return path.split(",")
    elif isinstance(path, list):
        return path
    else:
        return []


SHUTDOWN_SIGNAL = object()

class Hub(cpns.data.PnsMeta):
    """
    The redistributed pns central hub. All components of the system are
    rooted to the Hub.
    """

    _last_ref = None
    _last_call = None
    _loop = None

    def __init__(
        self,
        *,
        load_all_dynes: bool = True,
        load_all_subdirs: bool = True,
        recurse_subdirs: bool = True,
        pns_mods: list[str] = None,
        cli: str = None,
        logs: bool = True,
        load_config: bool = True,
    ):
        self._hub = self
        self.__init_kwargs = {k: v for k, v in locals().items() if k != "self" and not k.startswith("_")}
        subs = {}
        sub_alias = {}
        imports = {}
        cpns.data.PnsMeta.__init__(self, [subs, sub_alias, imports], parent=self)
        self._subs = subs
        self._sub_alias = sub_alias
        self._imports = imports
        self._dynamic = None
        self._dscan = False
        # Set up the conf OPT structure so it is always available
        self._opt = None
        self._task_count = 0

    async def __aenter__(
        self,
    ):
        self._tasks = asyncio.Queue()
        self._loop = asyncio.get_running_loop()

        # Add the dyne for python imports to live in to the hub
        if "lib" not in self._subs:
            self._subs["lib"] = await AsyncSub(
                self,
                subname="lib",
                dyne_name="lib",
            )
            # Allow the sub to find python modules dynamically
            self._subs["lib"] += sys.modules

        pns_mods = self.__init_kwargs["pns_mods"]
        if pns_mods is None:
            pns_mods = ["pns.mods"]
        if "pns" not in self._subs:
            # Add the pns sub to the hub, this should always use pypath and
            # Should never be made dynamic. This is a core system sub and should
            # NOT be app-merged
            self._subs["pns"] = await AsyncSub(self, subname="pns", pypath=pns_mods)
            await self._subs["pns"]._load_all()

        # Add passthrough sig handlers to the running loop.
        # Their behavior can be modified with contracts
        sigint = self.pns.task.sigint
        self._loop.add_signal_handler(signal.SIGINT, lambda s=signal.SIGINT: self._loop.create_task(sigint(s)))
        sigterm = self.pns.task.sigterm
        self._loop.add_signal_handler(signal.SIGTERM, lambda s=signal.SIGTERM: self._loop.create_task(sigterm(s)))

        self._load_all_dynes = self.__init_kwargs["load_all_dynes"]
        self._load_all_subdirs = self.__init_kwargs["load_all_subdirs"]
        self._recurse_subdirs = self.__init_kwargs["recurse_subdirs"]
        await self._scan_dynamic()
        await self.pns.sub.add(dyne_name="config")
        await self._subs["config"]._load_all()

        # Set up config first
        if self.__init_kwargs["load_config"]:
            # Overwrite opt with config data
            self._opt = await self.config.load(cli=self.__init_kwargs["cli"], **self._dynamic.config)

        await self.pns.sub.add(dyne_name="log")
        await self._subs["log"]._load_all()

        # Set up a logger
        if self.__init_kwargs["logs"]:
            await self.pns.sub.load_subdirs(self._subs["log"])
            await self.log.init.setup(**self._opt.log.copy())

        # Load all other dynes
        if self._load_all_dynes:
            # Load dynes after config so they can use hub.OPT in their __init__s
            await self._load_all()

        return self

    async def __aexit__(self, *args, **kwargs):
        await self._tasks.put(SHUTDOWN_SIGNAL)
        await asyncio.sleep(0)
        await self.pns.task.gather()
        self._loop = None

    @property
    def OPT(self):  # noqa
        return self._opt

    @property
    def _(self):
        """
        Return the parent of the last contract
        """
        # Remove the entry from the call stack
        if not self._last_ref:
            return self
        last_mod = self._last_ref.rsplit(".", maxsplit=1)[0]
        return pns.ref.last(self, last_mod)

    async def _load_all(self):
        for base, imp in self._dynamic.imports__.items():
            self._subs["lib"]._imports[base] = imp

        # Load all dynamic subs onto the hub
        for dyne in self._dynamic.dyne:
            if dyne in self._subs:
                continue
            await self.pns.sub.add(dyne_name=dyne)
            if not self._load_all_subdirs:
                continue
            await self.pns.sub.load_subdirs(self._subs[dyne], recurse=self._recurse_subdirs)

    async def _holder(self):
        """
        Just a sleeping while loop to hold the loop open while it runs until
        complete
        """
        while True:
            complete = await self._tasks.get()
            if complete is SHUTDOWN_SIGNAL:
                break
            await complete["task"]
            if complete["cb"]:
                await self._auto(complete["cb"])
            self._task_count -= 1

    def _auto(self, coro: Awaitable, cb_coro: Awaitable = None) -> asyncio.Future:
        """
        Start a task that will be automatically awaited

        coro: An unscheduled coroutine object to run
        cb_coro: An unscheduled coroutine to run when the main coroutine completes
        """
        current_context = copy_context()

        if not asyncio.iscoroutine(coro):
            warnings.warn(  # noqa
                f"Expected a coroutine, got {type(coro)}: {coro}"
            )
            return coro
        if cb_coro and not asyncio.iscoroutine(cb_coro):
            warnings.warn(  # noqa
                f"Expected a cb coroutine, got {type(cb_coro)}: {cb_coro}"
            )

        self._task_count += 1

        task = asyncio.create_task(coro, context=current_context)

        def _callback(task):
            original_context = copy_context()
            original_context.run(self._tasks.put_nowait, {"task": task, "cb": cb_coro})
            # This will re-raise any exception caught by the task
            task.result()

        task.add_done_callback(_callback)
        return task

    def __getstate__(self) -> dict:
        attrs = {}
        for k, v in self._attrs.items():
            if isinstance(v, pns.loader.BASE_TYPES):
                attrs[k] = v
            elif isinstance(v, dict):
                if all(isinstance(v2, pns.loader.BASE_TYPES) for v2 in v.values()):
                    attrs[k] = v
            elif isinstance(v, Iterable):
                if all(isinstance(v2, pns.loader.BASE_TYPES) for v2 in v):
                    attrs[k] = v
        state = {
            "init_kwargs": self.__init_kwargs,
            "subs": {name: sub.__getstate__() for name, sub in self._subs.items()},
            "aliases": self._sub_alias,
            "OPT": cpns.data.unfreeze(self._opt),
            "imports": {subname: mod.__name__ for subname, mod in self._imports.items()},
            "attrs": attrs,
        }
        return state

    def __reduce__(self):
        return Hub, (), self.__getstate__()

    def __setstate__(self, state: dict):
        subs = state["subs"]
        opt = state["OPT"]
        aliases = state["aliases"]

        for subname, modname in state["imports"].items():
            try:
                self._imports[subname] = importlib.import_module(modname)
            except ModuleNotFoundError:
                ...
        self._attrs.update(state["attrs"])
        self._sub_alias.update(aliases)
        self._opt = cpns.data.freeze(opt)

        # Schedule the hub's async init function to run later
        self._auto(self.__aenter__())
        for name, data in subs.items():
            if name in self._subs:
                sub = self._subs[name]
            else:
                sub = Sub(hub=self, root=self, **data["init_kwargs"])
                self._subs[name] = sub

            sub.__setstate__(data)

    async def _scan_dynamic(self):
        """
        Refresh the dynamic roots data used for loading app merge module roots
        """
        self._clear()
        self._dynamic = await pns.dirs.dynamic_dirs()
        self._dscan = True


class Sub(cpns.data.PnsMeta):
    """
    The pns object that contains the loaded module data
    """

    def __init__(
        self,
        hub: Hub,
        *,
        subname: str,
        root: cpns.data.PnsMeta = None,
        pypath: list[str] = None,
        static: list[str] = None,
        contracts_pypath: list[str] = None,
        contracts_static: list[str] = None,
        default_contracts: list[str] = None,
        virtual: bool = True,
        dyne_name: str = None,
        omit_start: tuple[str] = ("_",),
        omit_end: tuple[str] = (),
        omit_func: bool = False,
        omit_class: bool = False,
        omit_vars: bool = False,
        mod_basename: str = "",
        stop_on_failures: bool = False,
        init: bool = True,
        is_contract: bool = False,
        sub_virtual: bool = True,
        recursive_contracts_static: list[str] = None,
        default_recursive_contracts: list[str] = None,
        parent: object = None,
    ):
        """
        :param hub: The redistributed pns central hub
        :param subname: The name that the sub is going to take on the hub
            if nothing else is passed, it is used as the pypath
        :param pypath: One or many python paths which will be imported
        :param static: Directories that can be explicitly passed
        :param contracts_pypath: Load additional contract paths
        :param contracts_static: Load additional contract paths from a specific directory
        :param default_contracts: Specifies that a specific contract plugin will be applied as a default to all plugins
        :param virtual: Toggle whether or not to process __virtual__ functions
        :param dyne_name: The dynamic name to use to look up paths to find plugins -- linked to conf.py
        :param omit_start: Allows you to pass in a tuple of characters that would omit the loading of any object
            I.E. Any function starting with an underscore will not be loaded onto a plugin
            (You should probably never change this)
        :param omit_end:Allows you to pass in a tuple of characters that would omit the loading of an object
            (You should probably never change this)
        :param omit_func: bool: Don't load any functions
        :param omit_class: bool: Don't load any classes
        :param omit_vars: bool: Don't load any vars
        :param mod_basename: str: Manipulate the location in sys.modules that the plugin will be loaded to.
            Allow plugins to be loaded into a separate namespace.
        :param stop_on_failures: If any module fails to load for any reason, stacktrace and do not continue
            loading this sub
        :param init: bool: determine whether or not we process __init__ functions
        :param is_contract: Specify whether or not this sub is a contract
        :param sub_virtual: bool: Recursively ignore this sub and it's subs
        """
        self.__init_kwargs = {
            k: v for k, v in locals().items() if k not in ("self", "hub", "root") and not k.startswith("_")
        }
        subs = {}
        sub_alias = {}
        imports = {}
        loaded = {}

        _root = root or hub
        self._parent = parent or _root

        super().__init__([loaded, imports, subs, sub_alias], parent=self._parent)
        self._subs = subs
        self._sub_alias = sub_alias
        self._imports = imports
        self._loaded = loaded
        self._reload_mods = {}
        self._alias = []
        self._loaded_all = False
        self._load_errors = {}
        self._vmap = {}
        self._hub = hub
        self._root = _root
        self.__name__ = self._subname = subname
        self._pypath = ex_path(pypath)
        self._static = ex_path(static)
        self._contracts_pypath = ex_path(contracts_pypath)
        self._contracts_static = ex_path(contracts_static)
        self._recursive_contracts_static = ex_path(recursive_contracts_static)
        self._default_recursive_contracts = default_recursive_contracts or []
        self._default_contracts = default_contracts or ()
        self._dyne_name = dyne_name
        self._virtual = virtual
        self._omit_start = omit_start
        self._sub_virtual = sub_virtual
        self._omit_end = omit_end
        self._omit_func = omit_func
        self._omit_class = omit_class
        self._omit_vars = omit_vars
        self._mod_basename = mod_basename
        self._stop_on_failures = stop_on_failures
        self._is_contract = is_contract
        self._process_init = init

    async def __ainit__(self, *args, **kwargs):
        await self._prepare()

    async def _prepare(self):
        self._dirs = await pns.dirs.dir_list(
            self._pypath,
            self._static,
        )

        if self._dyne_name:
            await self._load_dyne()
        self._contract_dirs = await pns.dirs.dir_list(
            self._contracts_pypath,
            self._contracts_static,
        )
        self._contract_dirs.extend(await pns.dirs.inline_dirs(self._dirs, "contracts"))
        self._recursive_contract_dirs = await pns.dirs.dir_list(
            [],
            self._recursive_contracts_static,
        )
        self._recursive_contract_dirs.extend(await pns.dirs.inline_dirs(self._dirs, "recursive_contracts"))

        self._contract_subs = []
        for i in range(len(self._contract_dirs)):
            sub = await AsyncSub(
                hub=self._hub,
                parent=self,
                subname=f"{self._subname}._contract_subs[{i}]",
                static=[self._contract_dirs[i]],
                is_contract=True,
            )
            await sub._load_all()
            self._contract_subs.append(sub)

        self._recursive_contract_subs = []
        if self._recursive_contract_dirs:
            self._recursive_contract_dirs += getattr(self._root, "_recursive_contract_dirs", [])
            # child Subs look at the parent's _recursive_contract_dirs, so we can't modify it
            filtered_recursive_contract_dirs = sorted(set(self._recursive_contract_dirs) - set(self._contract_dirs))
            for i in range(len(filtered_recursive_contract_dirs)):
                sub = await AsyncSub(
                    hub=self._hub,
                    parent=self,
                    subname=f"{self._subname}._recursive_contract_subs[{i}]",
                    static=[filtered_recursive_contract_dirs[i]],
                    is_contract=True,
                )
                await sub._load_all()
                self._recursive_contract_subs.append(sub)
        else:
            # copy parent's recursive contracts
            self._recursive_contract_dirs = getattr(self._root, "_recursive_contract_dirs", [])
            self._recursive_contract_subs = getattr(self._root, "_recursive_contract_subs", [])

        self._name_root = self._load_name_root()
        self._scan = pns.scanner.scan(self._dirs)

    async def _load_dyne(self):
        """
        Load up the dynamic dirs for this sub
        """
        if not self._hub._dscan:
            await self._hub._scan_dynamic()
        for path in self._hub._dynamic.dyne.get(self._dyne_name, {}).get("paths", []):
            if path not in self._dirs:
                self._dirs.append(path)

        self._clear()

    def _load_name_root(self):
        """
        Generate the root of the name to be used to apply to the loaded modules
        """
        if self._pypath:
            return self._pypath[0]
        elif self._dirs:
            return secrets.token_hex()

    def __getstate__(self):
        attrs = {}
        for k, v in self._attrs.items():
            if isinstance(v, dict):
                if all(isinstance(v2, pns.loader.BASE_TYPES) for v2 in v.values()):
                    attrs[k] = v
            elif isinstance(v, Iterable):
                if all(isinstance(v2, pns.loader.BASE_TYPES) for v2 in v):
                    attrs[k] = v
            elif isinstance(v, pns.loader.BASE_TYPES):
                attrs[k] = v

        init_kwargs = self.__init_kwargs.copy()

        return {
            "init_kwargs": init_kwargs,
            "loaded": {
                item: {"iface": iface, "bname": bname, "state": self._loaded[item].__getstate__()}
                for item, (iface, bname) in self._reload_mods.items()
            },
            "subs": {name: sub.__getstate__() for name, sub in self._subs.items()},
            "aliases": self._sub_alias,
            "imports": {subname: mod.__name__ for subname, mod in self._imports.items()},
            "attrs": attrs,
        }

    def __reduce__(self):
        return AsyncSub, (), self.__getstate__()

    def __setstate__(self, state: dict):
        """
        Only a hub can truly restore a sub because of their interdependency
        """
        subs = state["subs"]
        aliases = state["aliases"]
        imports = state["imports"]
        loaded = state["loaded"]

        self._sub_alias.update(aliases)
        # self._attrs.update(state["attrs"])

        for subname, modname in imports.items():
            try:
                self._imports[subname] = importlib.import_module(modname)
            except ModuleNotFoundError:
                ...

        for name, data in subs.items():
            sub = Sub(hub=self._hub, root=self, **data["init_kwargs"])
            sub.__setstate__(data)
            self._subs[name] = sub

        # Initialize the Sub, put these functions on the hub to be gathered
        self._hub._auto(self.__ainit__())
        self._hub._auto(self._load_all())

        # Make sure all unique items make it back onto the loaded mod
        for item, data in loaded.items():
            try:
                self._loaded[item].__setstate__(data["state"])
            except KeyError:
                ...

    async def _sub_init(self):
        """
        Run load init.py for the sub, running '__init__' function if present
        """
        await self._find_mod("init", match_only=True)

    def _process_load_error(
        self,
        mod: ModuleType,
    ) -> bool:
        if not isinstance(mod, pns.loader.LoadError):
            # This is not a LoadError, return now!
            return False

        if mod.edict["verror"]:
            return False

        return True

    async def _find_mod(self, item: str, *, match_only: bool = False):
        """
        Find the module named item
        :param item: The module to search for (then load) from any scanned interface
        :param match_only: return the loaded module
        :return a loaded mod_dict
        """
        for iface in self._scan:
            for bname in self._scan[iface]:
                if os.path.basename(bname) == item:
                    await self._load_item(iface, bname)
            if item in self._loaded:
                self._reload_mods[item] = (iface, bname)
                return self._loaded[item]
        if not match_only:
            for iface in self._scan:
                for bname in self._scan[iface]:
                    if self._scan[iface][bname].get("loaded"):
                        continue
                    await self._load_item(iface, bname)
                    if item in self._loaded:
                        self._reload_mods[item] = (iface, bname)
                        return self._loaded[item]
        # Let's see if the module being lookup is in the load errors dictionary
        if item in self._load_errors:
            # Return the LoadError
            return self._load_errors[item]

    async def _load_item(self, iface: str, bname: str):
        """
        Load the named basename
        :param iface: A scanned directory type
        :param bname: The base name of the python path of a module
        """
        # The mname is the name to give the module in python's sys.modules
        # This name must be unique for every loaded module, so we use the full
        # module path sans the file extention
        mname = self._scan[iface][bname]["path"].replace(os.sep, ".")
        mname = mname[mname.index(".") + 1 : mname.rindex(".")].strip(".")
        mod = pns.loader.load_mod(
            mname,
            iface,
            self._scan[iface][bname]["path"],
        )
        await self._prep_mod(mod, iface, bname)

    def _process_vret(self, vret: dict[str, object]) -> bool:
        """
        :param vret: The return from a __virtual__ or __sub_virtual__ function
        :return: True if there was an error, else false
        """
        if "error" in vret:
            # Virtual Errors should not full stop pns
            self._process_load_error(vret["error"])
            # Store the LoadError under the __virtualname__ if defined
            self._load_errors[vret["vname"]] = vret["error"]
            return True
        else:
            return False

    async def _prep_mod(self, mod: ModuleType, iface: str, bname: str):
        """
        Prepare the module!
        :param mod: A python module containing data
        :param iface: A scanned directory type
        :param bname: The base name of the python path of a module
        """
        if not self._sub_virtual:
            return
        else:
            vret = await pns.loader.load_sub_virtual(self._hub, mod, bname, self._ref)
            if self._process_vret(vret):
                self._sub_virtual = False
                return

        vret = await pns.loader.load_virtual(self._hub, mod, bname, self._ref)

        if self._process_vret(vret):
            return

        contracts = []
        for contract_sub in self._contract_subs:
            contracts.extend(cpns.contract.load_contract(contract_sub, self._default_contracts, mod, vret["name"]))
        recursive_contracts = []
        for recursive_contract_sub in self._recursive_contract_subs:
            recursive_contracts.extend(
                cpns.contract.load_contract(
                    recursive_contract_sub,
                    self._default_recursive_contracts,
                    mod,
                    vret["name"],
                )
            )
        name = vret["name"]
        mod_dict = await pns.loader.prep_loaded_mod(self, mod, name, contracts, recursive_contracts)
        if name == "init":
            # Add the init attrs to its parent sub's search path
            self += mod_dict._attrs
        else:
            pns.verify.contract(contracts + recursive_contracts, mod_dict)

        if name not in self._loaded:
            self._loaded[name] = mod_dict
        else:
            self._loaded[name]._attrs += mod_dict._attrs
            self._loaded[name]._attrs._clear()

        self._vmap[mod.__file__] = name
        # Let's mark the module as loaded
        self._scan[iface][bname]["loaded"] = True
        if self._process_init:
            # Now that the module has been added to the sub, call mod_init
            await pns.loader.mod_init(self, mod, name)

    async def _load_all(self):
        """
        Load all modules found during the scan.

        .. attention:: This completely disables the lazy loader behavior of pns
        """
        if self._loaded_all is True:
            return
        for iface in self._scan:
            ifaces = self._scan[iface]
            for bname in sorted(ifaces, reverse=True):
                if self._scan[iface][bname].get("loaded"):
                    continue
                await self._load_item(iface, bname)
        self._loaded_all = True

    @property
    def _ref(self) -> str:
        """
        Return a full path on the hub to this sub
        """
        ref = self._subname
        root = self._parent
        while hasattr(root, "_subname"):
            ref = f"{root._subname}.{ref}"
            root = root._parent
        return ref


class AsyncInitWrapper:
    def __init__(self, cls: cpns.data.PnsMeta):
        self.cls = cls

    async def __call__(self, *args, **kwargs):
        instance: cpns.data.PnsMeta = self.cls(*args, **kwargs)
        await instance.__ainit__(*args, **kwargs)
        return instance


AsyncSub = AsyncInitWrapper(Sub)
