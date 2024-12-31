import asyncio
from collections.abc import Mapping
from collections.abc import Iterable
import pns.contract
import pns.dir
import pns.loop
import pkgutil
from types import ModuleType
import inspect

INIT = "__init__"

class Namespace(Mapping):
    _omit_start=("_",)
    _omit_end=()
    _omit_func=False
    _omit_class=False
    _omit_vars=False
    _virtual = True
    
    def __init__(
        self,
        name: str,
        pypath:list[str]=(),
        static:list[str]=(),
        parent: "Namespace" = None,
        root: "Namespace" = None,
    ):
        self.__name__ = name
        self.__ = parent or self
        self._ = root or parent or self
        self._alias = []
        self._nest = {}
        self._mod = {}
        self._contracts = []
        self._rcontracts = []
        self._dirs = pns.dir.walk(pypath, static)
        
    @property
    def contracts(self):
        return self._contracts + self._rcontracts

    def __getattr__(self, name: str):
        """Dynamic attribute access for children and module."""
        if name in self._nest:
            sub = self._nest[name]
            if getattr(sub, "_virtual", True):
                return sub
            
        if name[0] in self._omit_start or name[-1] in self._omit_end:
            return self.__getattribute__(name)
        
        # Check if a sub is aliased to this name
        for sub in self._nest:
            if name in sub._alias and getattr(sub,  "_virtual", True):
                return sub
            
        # If attribute not found, attempt to load the module dynamically
        if name not in self._mod:
            pns.loop.run(self._load_mod(name))
        
        if name in self._mod:
            return self._mod[name]

        # Finally, fall back on the default attribute access
        return self.__getattribute__(name)


    def __getitem__(self, name: str):
        """
        Get full references by parsing the ref
        """
        finder = self
        for part in name.split("."):
            finder = getattr(finder, part)
        return finder

    def __iadd__(self, other: [str or tuple]):
        """
        Add a child to the namespace.

        ns += (name, ["pypath"], ["static"])

        is the same as

        ns._add_child(name, ["pypath"], ["static"])
        """
        if isinstance(other, str):
            self._add_child(other)
        elif isinstance(other, Iterable):
            self._add_child(*other)
        return self

    def __div__(self, name: str):
        """
        Traverse the namespace

        ns.sub.sub.mod

        is the same as

        ns / "sub" / "sub" / "mod"
        """
        return self[name]

    def __gt__(self, name: str):
        """
        Traverse the namespace

        ns.sub.sub.mod

        is the same as

        ns > "sub" > "sub" > "mod"
        """
        return self[name]

    def __floordiv__(self, name: str):
        """
        Traverse the parent of the namespace

        ns.sub.__.mod

        is the same as

        ns / "sub" // "mod"

        is the same as

        ns.mod
        """
        return self.__[name]

    def __lt__(self, name: str):
        """
        Traverse the parent of the namespace

        ns.sub.__.mod

        is the same as

        ns / "sub" < "mod"

        is the same as

        ns.mod
        """
        return self.__[name]

    def __iter__(self):
        """
        Iterate the leaves first, then if there is a module on this namespace, iterate that too
        """
        yield from self._nest
        yield from self._mod

    def __len__(self):
        return len(self._nest) + len(self._mod)

    def __bool__(self):
        """
        True if the namespace has leaves or a mod, else false
        """
        return bool(self._nest) or bool(self._mod)

    def _add_child(self, name: str, pypath: list[str] = (), static:list[str] = ()):
        """Add a new child to the parent"""
        current = self
        parts = name.split(".")
        for part in parts[:-1]:  # Iterate over all parts except the last one
            if part not in current._nest:
                current._nest[part] = Namespace(part, root=self._, parent=self)

            current = current._nest[part]

        # Only in the last iteration, use pypath and static
        last_part = parts[-1]
        current._nest[last_part] = Namespace(
            last_part, root=self._, parent=self, pypath=pypath, static=static
        )
        return current._nest[last_part]

    @property
    def __ref__(self):
        """Construct a reference string that traverses from the root to the current node."""
        parts = []
        finder = self
        while finder != self._:  # Traverse up until we reach the root
            parts.append(finder.__name__)  # Add the root name
            finder = finder.__

        # Reverse parts to start from the root
        return ".".join(reversed(parts))

    def __repr__(self):
        return f"Namespace({self.__ref__})"
    
    async def _load_mod(self, name: str, *, recurse:bool = True):
        for pypath in self._dirs:
            mod = pns.mod.load_from_path(name, pypath)
            if mod:
                break
        else:
            mod = pns.mod.load(name)
            
        try:
            loaded_mod = await pns.mod.prep(self._, self, name, mod)
        except NotImplementedError:
            self._nest.pop(name)
            return

        self.mod[name] = loaded_mod

        # Execute the __init__ function if present
        if hasattr(mod, INIT):
            func = getattr(mod, INIT)
            if asyncio.iscoroutinefunction(func):
                init = pns.contract.Contracted(
                    self.hub,
                    contracts=[],
                    func=func,
                    ref=f"{self.__ref__}.{name}",
                    parent=mod,
                    name=INIT,
                )
                ret = init()
                if asyncio.iscoroutine(ret):
                    await ret

        if not recurse or not getattr(mod, "__path__", None):
            return

        module_paths = mod.__path__._path
        for _, modname, _ in pkgutil.iter_modules(module_paths):
            # Add a namespace to this one for every submodule in the module
            await self._load_mod(
                name=modname, pypath=f"{name}.{modname}", recurse=recurse
            )



class LoadedMod(Namespace):
    def __init__(self, mod: ModuleType, **kwargs):
        super().__init__(**kwargs)
        self._var = {}
        self._func = {}
        self._class = {}
        
        # Sort attributes from the module
        self._populate(mod)

    def _populate(self, mod: ModuleType):
        # Iterate over all attributes in the module
        for name, obj in vars(mod).items():
            if name[0] in self._omit_start or name[-1] in self._omit_end:
                continue
            if inspect.isfunction(obj) and not self._omit_func:
                if asyncio.iscoroutinefunction(obj):
                    func = obj
                else:
                    func = pns.loop.make_async(obj)
                
                self._func[name] = pns.contract.create_contracted(
                    self._,
                    contracts=self.__.contracts,
                    func=func,
                    ref=self.__ref__,
                    parent=self.__,
                    name=func.__name__,
                    # Add the root hub to the function call if "hub" is an argument to the function
                    implicit_hub=func.__code__.co_varnames
                    and (func.__code__.co_varnames[0] == "hub"),
                )
            elif inspect.isclass(obj) and not self._omit_class:
                self._class[name] = obj
            elif not self._omit_vars:
                # Consider remaining objects as variables
                self._var[name] = obj
        
    @property
    def _attr(self):
        return {**self._class, **self._var, **self._func}
        
    def __getattr__(self, name: str):
        obj = getattr(self.__module__, name)
        if asyncio.iscoroutinefunction(obj):
            func = obj
            return pns.contract.create_contracted(
                self._,
                contracts=self.__.contracts,
                func=func,
                ref=self.__ref__,
                parent=self.__,
                name=func.__name__,
                # Add the root hub to the function call if "hub" is an argument to the function
                implicit_hub=func.__code__.co_varnames
                and (func.__code__.co_varnames[0] == "hub"),
            )
        return obj

