import sys
import asyncio
import importlib.util
import yaml
import pns.contract
from pathlib import Path

# Assuming pns.data.NamespaceDict exists and is defined elsewhere
class NamespaceDict(dict):
    """A mockup for missing pns.data.NamespaceDict"""
    pass

VIRTUAL = "__virtual__"
INIT = "__init__"
CONFIG = "conf.yaml"

class Namespace:
    _last_ref = None
    _last_call = None
    def __init__(self, name: str, module=None, tree: 'Namespace' = None, root: 'Namespace' = None):
        self.name = name
        self.__ = tree or self
        self._ = root or self
        self.leaf = {}
        self.mod = module
        self.contracts = []
        self.OPT = NamespaceDict()

    def __getattr__(self, name: str):
        """Dynamic attribute access for children and module."""
        if name in self.leaf:
            return self.leaf[name]
        if self.mod:
            func = getattr(self.mod, name)
            if asyncio.iscoroutinefunction(func):
                return pns.contract.create_contracted(
                    self._,
                    contracts=self.contracts,
                    func=func,
                    ref=self.ref,
                    parent=self.__,
                    name=func.__name__,
                    implicit_hub=func.__code__.co_varnames and (func.__code__.co_varnames[0] == "hub"),
                )
            return func

        return self.__getattribute__(name)

    async def add_leaf(self, name: str, module_path: str = None):
        """Add a new leaf to the tree with optional module import."""
        mod = None
        ret = None
        if module_path:
            mod = load_module(module_path)

            # Load the config if exists
            try:
                module_file = Path(mod.__file__).parent
                config_path = module_file / CONFIG
            except (AttributeError, TypeError):
                config_path= None
            if config_path and config_path.is_file():
                with config_path.open('r') as file:
                    config = yaml.safe_load(file)
                print(f"Parsed config for {module_path}: {config}")

            # Execute the __virtual__ function if present
            if hasattr(mod, VIRTUAL):
                virtual = pns.contract.Contracted(
                    self._,
                    contracts=[],
                    func=getattr(mod, VIRTUAL),
                    ref=f"{self.ref}.{name}",
                    parent=mod,
                    name=VIRTUAL,
                )
                ret = virtual()
                if asyncio.iscoroutine(ret):
                    ret = await ret

            leaf = Namespace(name, module=mod, root=self._)
            self.leaf[name] = leaf

            # Execute the __init__ function if present
            if hasattr(mod, INIT):
                func = getattr(mod, INIT)
                if asyncio.iscoroutinefunction(func):
                    init = pns.contract.Contracted(
                        self._,
                        contracts=[],
                        func=func,
                        ref=f"{self.ref}.{name}",
                        parent=self,
                        name=INIT,
                    )
                    ret = init()
                    if asyncio.iscoroutine(ret):
                        ret = await ret
        else:
            leaf = Namespace(name, module=mod, root=self._)
            self.leaf[name] = leaf

        return ret

    @property
    def ref(self):
        """Construct a reference string that traverses from the root to the current node."""
        parts = []
        finder = self
        while finder.name != self.__.name:  # Traverse up until we reach the root
            parts.append(finder.name)
            finder = finder.__
        parts.append(finder.name)  # Add the root name

        # Reverse parts to start from the root
        return ".".join(reversed(parts))


    def __repr__(self):
        return f"Namespace({self.ref})"

    def __iter__(self):
        return iter(self.leaf)


def load_module(path: str):
    """Load a module by name and file path into sys.modules."""
    ret = None
    if path in sys.modules:
        return sys.modules[path]

    print(path)
    builder = []
    for part in path.split("."):
        builder.append(part)
        print(".".join(builder))
        try:
            ret = importlib.import_module(".".join(builder))
        except ModuleNotFoundError:
            ret = getattr(ret, part)

    return ret


async def new(*args, **kwargs):
    hub = Namespace(name="hub")
    await hub.add_leaf("pns", "pns.mods")
    await hub.pns.add_leaf("sub", "pns.mods.sub")
    await hub.add_leaf("lib", "sys.modules")
    await hub.lib.add_leaf("logging", "logging")
    await hub.lib.add_leaf("asyncio", "asyncio")
    await hub.lib.add_leaf("aiologger", "aiologger")
    await hub.lib.add_leaf("pns", "pns")
    await hub.add_leaf("log", "pns.log")
    await hub.log.add_leaf("init", "pns.log.init")
    await hub.add_leaf("cli")
    await hub.cli.add_leaf("init", "hub.plugin.init")
    print(hub.log.init)
    print("YES!")
    hub.OPT.cli = NamespaceDict()
    hub.OPT.cli.watch=False
    hub.OPT.cli.monitor=False
    hub.OPT.cli.init=[]
    return hub
