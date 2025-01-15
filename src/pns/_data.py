from collections.abc import Mapping
from types import SimpleNamespace
from collections.abc import Iterable


class NamespaceDict(dict[str, object]):
    def __getattr__(self, key: str):
        try:
            val = self[key]
            if isinstance(val, dict) and not isinstance(val, NamespaceDict):
                val = NamespaceDict(val)
            return val
        except KeyError:
            return super().__getattribute__(key)


class Namespace(SimpleNamespace):
    _active = True

    def __init__(
        self,
        name: str,
        parent: "Namespace" = None,
        root: "Namespace" = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.__name__ = name
        self.__ = parent
        self._root = root
        # Aliases for this namespace
        self._alias = set()
        # Namespaces underneath this namespace
        self._nest = {}

    @property
    def _(self):
        return self._root

    def __getattr__(self, name: str):
        """Dynamic attribute access for children and module."""
        item = get_alias(name, self._nest)
        if item:
            return item

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

    def __iadd__(self, other: str | tuple):
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

    def __len__(self):
        return len(self._nest)

    def __bool__(self):
        """
        True if the namespace has leaves, else false
        """
        return self._active

    def _add_child(self, name: str, cls=None):
        """Add a new child to the parent"""
        if cls is None:
            cls = Namespace
        current = self
        parts = name.split(".")
        for part in parts:
            if part not in current._nest:
                current._nest[part] = cls(part, root=self._, parent=self)

            current = current._nest[part]

        return current

    @property
    def __ref__(self):
        """Construct a reference string that traverses from the root to the current node."""
        parts = []
        finder = self
        # Traverse up until we reach the root
        while finder.__ is not None:
            # Add the root name
            parts.append(finder.__name__)
            finder = finder.__

        # Reverse parts to start from the root
        return ".".join(reversed(parts))

    def __repr__(self):
        return f"{self.__class__.__name__.split('.')[-1]}({self.__ref__})"


def get_alias(name: str, collection: dict[str, object]) -> Namespace:
    """
    Iterate over a dictionary of Namespace objects and return the one that matches the name or alias.
    """
    for check, ns in collection.items():
        if name == check and getattr(ns, "_active", True):
            return ns
        elif not isinstance(ns, Namespace):
            continue
        if name in ns._alias and ns._active:
            return ns


def update(dest, upd, recursive_update: bool = True, merge_lists: bool = False):
    """
    Recursive version of the default dict.update
    Merges upd recursively into dest
    If recursive_update=False, will use the classic dict.update, or fall back
    on a manual merge (helpful for non-dict types like FunctionWrapper)
    If merge_lists=True, will aggregate list object types instead of replace.
    The list in ``upd`` is added to the list in ``dest``, so the resulting list
    is ``dest[key] + upd[key]``. This behavior is only activated when
    recursive_update=True. By default merge_lists=False.
    """
    keys = set(list(upd.keys()) + list(dest.keys()))
    NONE = object()

    if recursive_update:
        for key in keys:
            val = upd.get(key, NONE)
            dest_subkey = dest.get(key, NONE)
            if isinstance(dest_subkey, Mapping) and isinstance(val, Mapping):
                ret = update(dest_subkey, val, merge_lists=merge_lists)
                dest[key] = ret
            elif (
                isinstance(dest_subkey, list) and isinstance(val, list) and merge_lists
            ):
                merged = dest_subkey[:]
                merged.extend(x for x in val if x not in merged)
                dest[key] = merged
            elif val is not NONE:
                dest[key] = val
            elif dest is NONE:
                dest[key] = None
    else:
        for key in keys:
            dest[key] = upd[key]

    return dest
