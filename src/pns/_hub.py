import asyncio
import pns.data
import pns.loop
import pkgutil

INIT = "__init__"
SUB_ALIAS = "__sub_alias__"


class DynamicNamespace(pns.data.Namespace):
    """
    A namespace that can dynamically load modules from a directory.
    """

    def __init__(self, locations: list[str] = (), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dir = pns.dir.walk(locations)
        self._mod = {}

    def __getattr__(self, name: str):
        try:
            return super().__getattr__(name)
        except AttributeError:
            for check, ns in self._mod.items():
                if name == check and getattr(ns, "_active", True):
                    return ns
                elif not isinstance(ns, pns.data.Namespace):
                    continue
                if name in ns._alias and ns._active:
                    return ns

            # If attribute not found, attempt to load the module dynamically
            pns.loop.run(self._load_mod(name))

            for check, ns in self._mod.items():
                if name == check and getattr(ns, "_active", True):
                    return ns
                elif not isinstance(ns, pns.data.Namespace):
                    continue
                if name in ns._alias and ns._active:
                    return ns

            raise

    async def _load_all(self):
        for _, name, _ in pkgutil.iter_modules(self._dir):
            await self._load_mod(name)

    async def _load_mod(self, name: str):
        for path in self._dir:
            mod = pns.mod.load_from_path(name, path)
            if mod:
                break
        else:
            mod = pns.mod.load(name)

        try:
            loaded_mod = await pns.mod.prep(self._, self, name, mod)
        except NotImplementedError:
            return

        self._mod[name] = loaded_mod

        if hasattr(mod, SUB_ALIAS):
            self._alias.update(getattr(mod, SUB_ALIAS))

        # Execute the __init__ function if present
        if hasattr(mod, INIT):
            func = getattr(mod, INIT)
            if asyncio.iscoroutinefunction(func):
                init = pns.contract.Contracted(
                    name=INIT, func=func, parent=loaded_mod, root=self._
                )
                await init()

    def __iter__(self):
        yield from self._nest
        yield from self._mod
