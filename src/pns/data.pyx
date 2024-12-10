# cython: language_level=3

import asyncio
from collections.abc import Mapping
from collections.abc import Iterable
import pns.contract


class Namespace(Mapping):
    def __init__(self, name: str, module=None, tree: "Namespace" = None, root: "Namespace" = None):
        self.name = name
        self.__ = tree or self
        self._ = root or self
        self.data = {}
        self.mod = module

    def __getattr__(self, name: str):
        """Dynamic attribute access for children and module."""
        if name in self.data:
            return self.data[name]
        elif hasattr(self.mod, name):
            return getattr(self.mod, name)
        else:
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
        Add a leaf to the namespace.

        ns += (name, module_path)

        is the same as

        ns.add(name, module_path)
        """
        if isinstance(other, str):
            self.add(other)
        elif isinstance(other, Iterable):
            self.add(*other)
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
        yield from self.data
        if self.mod:
            yield from self.mod

    def __bool__(self):
        """
        True if the namespace has leaves or a mod, else false
        """
        return bool(self.data) or bool(self.mod)

    def add(self, name: str, module_path: str = None):
        """Add a new leaf to the tree with optional module import."""
        current = self
        for part in name.split("."):
            current.data[part] = Namespace(part, root=self._, tree=self, module=module_path)
            current = current.data[part]

        # Only add the module to the final place in the path
        current.mod = module_path

        return current

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

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)


class NamespaceDict(dict[str, object]):
    def __getattr__(self, key: str):
        try:
            val = self[key]
            if isinstance(val, dict) and not isinstance(val, NamespaceDict):
                val = NamespaceDict(val)
            return val
        except KeyError:
            return super().__getattribute__(key)


class LoadedMod(Namespace):
    def __getattr__(self, name: str):
        obj = getattr(self.mod, name)
        if asyncio.iscoroutinefunction(obj):
            func = obj
            return pns.contract.create_contracted(
                self._,
                contracts=self.__.contracts,
                func=func,
                ref=self.ref,
                parent=self.__,
                name=func.__name__,
                # Add the root hub to the function call if "hub" is an argument to the function
                implicit_hub=func.__code__.co_varnames and (func.__code__.co_varnames[0] == "hub"),
            )
        return obj


cpdef update(dest, upd, bint recursive_update=True, bint merge_lists=False):
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
    cdef:
        set keys = set(list(upd.keys()) + list(dest.keys()))
        object key, val, dest_subkey

    NONE = object()
    if recursive_update:
        for key in keys:
            val = upd.get(key, NONE)
            dest_subkey = dest.get(key, NONE)
            if isinstance(dest_subkey, Mapping) and isinstance(val, Mapping):
                ret = update(dest_subkey, val, merge_lists=merge_lists)
                dest[key] = ret
            elif isinstance(dest_subkey, list) and isinstance(val, list) and merge_lists:
                merged = dest_subkey[:]
                merged.extend([x for x in val if x not in merged])
                dest[key] = merged
            elif val is not NONE:
                dest[key] = val
            elif dest is NONE:
                dest[key] = None
    else:
        for key in keys:
            dest[key] = upd[key]
    return dest
