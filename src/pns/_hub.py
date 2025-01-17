import asyncio
import pns.data
import pns.loop
import pns.verify
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
            item = pns.data.get_alias(name, self._mod)

            # If attribute not found, attempt to load the module dynamically
            if not item:
                pns.loop.run(self._load_mod(name))
                item = pns.data.get_alias(name, self._mod)

            if item:
                return item

            raise

    async def _load_all(self, *, merge: bool = True):
        for d in self._dir:
            for _, name, _ in pkgutil.iter_modules([d]):
                await self._load_mod(name, [d], merge=merge)

    async def _load_mod(
        self, name: str, dirs: list[str] = None, *, merge: bool = False
    ):
        if not dirs:
            dirs = self._dir

        for path in dirs:
            mod = pns.mod.load_from_path(name, path)
            if not mod:
                raise AttributeError(f"Module '{name}' not found in {path}")

            try:
                loaded_mod = await pns.mod.prep(self._, self, name, mod)
            except NotImplementedError:
                continue

            # Account for a name change with a virtualname
            name = loaded_mod.__name__
            if name not in self._mod:
                self._mod[name] = loaded_mod
            elif merge:
                # Merge the two modules
                old_mod = self._mod.pop(name)
                loaded_mod._var.update(old_mod._var)
                loaded_mod._func.update(old_mod._func)
                loaded_mod._class.update(old_mod._class)
                self._mod[name] = loaded_mod
            else:
                # Add the second module
                loaded_mod._alias.add(name)
                self._mod[str(path)] = loaded_mod

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
