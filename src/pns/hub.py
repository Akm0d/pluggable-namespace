import sys
import pkgutil
import pns.data
import pns.dir
import pns.load



class Sub(pns.data.Namespace):
    def __init__(self, name: str, parent: pns.data.Namespace, root: 'Hub'):
        super().__init__(name, tree=parent, root=root)
        self.hub = root or parent
        self.contracts = []
        self.rcontracts = []

    async def add_sub(self, name: str, module_ref: str = None, recurse:bool = True):
        if name in self.leaf:
            return
        mod = None
        sub = Sub(name=name, parent=self, root=self.hub)
        self.leaf[name]  = sub
        if not module_ref:
            return

        mod = pns.load.load_module(module_ref)
        loaded_mod = await pns.load.prep_mod(self.hub, self, name, mod)
        sub.mod = loaded_mod

        if not recurse or not getattr(mod, "__path__", None):
            return

        module_paths = mod.__path__._path
        for _, subname, _ in pkgutil.iter_modules(module_paths):
            # Add a sub to this one for every submodule in the module
            await sub.add_sub(name=subname, module_ref = f"{module_ref}.{subname}", recurse=recurse)



class Hub(Sub):
    _last_ref = None
    _last_call = None
    dynamic = None

    def __init__(hub):
        super().__init__(name="hub", parent=None, root=None)
        # Add a place for sys modules to live
        hub += "lib"
        hub.lib.leaf = sys.modules
        hub.dynamic = pns.dir.dynamic()



async def new(*args, **kwargs):
    # Set up the hub
    hub = Hub()

    # Add essential pns modules
    await hub.add_sub("pns", "pns.mods")

    # Load the config
    await hub.add_sub("config", "pns.config")
    opt = await hub.pns.config.load()
    hub.OPT = pns.data.NamespaceDict(opt)

    await hub.add_sub("log", "pns.log")
    await hub.log.init.setup(**opt.log.copy())


    # This is for testing until the rest is working
    await hub.add_sub("cli", "hub.plugin")
    return hub
