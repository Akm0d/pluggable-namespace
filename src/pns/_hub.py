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
            # If attribute not found, attempt to load the module dynamically
            if name not in self._mod:
                pns.loop.run(self._load_mod(name))

            if name in self._mod:
                return self._mod[name]

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
