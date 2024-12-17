import asyncio
import sys
import pkgutil
import pns.data
import pns.dir
import pns.load


INIT = "__init__"

class Sub(pns.data.Namespace):
    def __init__(self, name: str, parent: pns.data.Namespace, root: 'Hub'):
        super().__init__(name, parent=parent, root=root)
        self.hub = root or parent
        self._contracts = []
        self._rcontracts = []
        self.contracts = self._contracts + self._rcontracts

    async def add_sub(self, name: str, module_ref: str = None, recurse:bool = True):
        if name in self.__data__:
            return
        mod = None
        sub = Sub(name=name, parent=self, root=self.hub)
        self.__data__[name]  = sub
        if not module_ref:
            return

        mod = pns.load.load_module(module_ref)
        try:
            loaded_mod = await pns.load.prep_mod(self.hub, self, name, mod)
        except NotImplementedError:
            self.__data__.pop(name)
            return

        sub.__module__ = loaded_mod

        # Execute the __init__ function if present
        if hasattr(mod, INIT):
            func = getattr(mod, INIT)
            if asyncio.iscoroutinefunction(func):
                init = pns.contract.Contracted(
                    self.hub,
                    contracts=[],
                    func=func,
                    ref=f"{sub.__ref__}.{name}",
                    parent=mod,
                    name=INIT,
                )
                ret = init()
                if asyncio.iscoroutine(ret):
                    await ret

        if not recurse or not getattr(mod, "__path__", None):
            return

        module_paths = mod.__path__._path
        for _, subname, _ in pkgutil.iter_modules(module_paths):
            # Add a sub to this one for every submodule in the module
            await sub.add_sub(name=subname, module_ref = f"{module_ref}.{subname}", recurse=recurse)



class Hub(Sub):
    _last_ref = None
    _last_call = None
    _dynamic = None

    def __init__(hub):
        super().__init__(name="hub", parent=None, root=None)
        hub.hub = hub
        # Add a place for sys modules to live
        hub += "lib"
        hub.lib.__data__ = sys.modules
        hub._dynamic = pns.dir.dynamic()



async def new(cli:str="cli", *args, **kwargs):
    # Set up the hub
    hub = Hub()

    # Add essential pns modules
    await hub.add_sub("pns", "pns.mods")

    # Load the config
    await hub.add_sub("config", "pns.config")
    opt = await hub.pns.config.load(cli=cli, **hub._dynamic.config)
    hub.OPT = pns.data.NamespaceDict(opt)

    # Setup the logger
    await hub.add_sub("log", "pns.log")
    await hub.log.init.setup(**hub.OPT.log.copy())

    # Add other core modules
    await hub.add_sub("patt", "_patt.plugin")
    await hub.patt.sh.add_sub()

    # This is for testing until the rest is working
    # TODO Add "_load_all" and integrate pop.sub.add
    await hub.add_sub("cli", "hub.plugin")
    return hub
