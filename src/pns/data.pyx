# cython: language_level=3

from collections.abc import Mapping
from cpython cimport dict
import pns.ref


cdef frozenset DICT_ATTRS = frozenset(dir(dict))

cdef class NamespaceDict(dict[str, object]):
    def __getattr__(self, key: str):
        if key.startswith("__") and key.endswith("__"):
            self.__getattribute__(key)
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, key: str, value: object):
        if isinstance(value, dict):
            value = NamespaceDict(value)
        self[key] = value


cdef class MultidictCache:
    cdef:
        dict[str, object] _cache
        list[dict[str, object]] _base_dicts
        dict[str, list[str]] _split_cache
        object _root

    def __init__(self, base_dicts: list[dict[str, object]] = None, parent: object = None):
        if base_dicts is None:
            base_dicts = []
        self._base_dicts = base_dicts
        self._cache = dict[str, object]()
        self._split_cache = dict[str, list[str]]()
        self._root = parent or self

    @property
    def __(self):
        """
        Let any instance of MultidictCache access its parent in this way
        """
        return self._root

    cpdef _clear(self):
        self._cache.clear()
        self._split_cache.clear()

    def __add__(self, search_path):
        """
        Add the new dictionary to the search base
        """
        self._base_dicts.append(search_path)
        return self

    def __getitem__(self, key: (str , DocumentedValue)):
        key = str(key)
        if key in self._cache:
            return self._cache[key]

        if key not in self._split_cache:
            self._split_cache[key] = key.split(".")

        parts = self._split_cache[key]
        for base_dict in self._base_dicts:
            finder = base_dict
            try:
                for part in parts:
                    try:
                        finder = finder[part]
                    except TypeError:
                        # Module's are not subscriptable, so we have to try to getattribute
                        try:
                            finder = getattr(finder, part)
                        except AttributeError as e:
                            raise KeyError from e
                self._cache[key] = finder
                return finder
            except KeyError:
                continue

        raise KeyError(f"Item '{key}' not found in any base dictionary")

    def __iter__(self):
        return iter({k for base_dict in self._base_dicts for k in base_dict})

    def __contains__(self, item):
        return any(item in base_dict for base_dict in self._base_dicts)

    def get(self, item: str, default=None):
        try:
            return self[item]
        except KeyError:
            return default


def wrap_value(name: str, value, docstring: str):
    """
    Add a docstring and name to an arbitrary python variable
    """
    t = type(value)
    if t is bool or value is None:
        t = object

    class DocumentedValue(t):
        def __init__(self):
            f"""{docstring}"""

        def __getattribute__(self, att):
            if att == "__name__":
                return name
            if att == "__doc__":
                return docstring
            if att == "__class__":
                return value.__class__
            return getattr(value, att)

        def __repr__(self):
            return repr(value)

        def __str__(self):
            return str(value)

        def __bool__(self):
            return bool(value)

        def __eq__(self, other):
            return value == other

        def __ne__(self, other):
            return value != other

        def __lt__(self, other):
            return value < other

        def __le__(self, other):
            return value <= other

        def __gt__(self, other):
            return value > other

        def __ge__(self, other):
            return value >= other

        def __add__(self, other):
            return value + other

        def __sub__(self, other):
            return value - other

        def __mul__(self, other):
            return value * other

        def __truediv__(self, other):
            return value / other

        def __floordiv__(self, other):
            return value // other

        def __mod__(self, other):
            return value % other

        def __and__(self, other):
            return value & other

        def __or__(self, other):
            return value | other

        def __xor__(self, other):
            return value ^ other

        def __lshift__(self, other):
            return value << other

        def __rshift__(self, other):
            return value >> other

        def __neg__(self):
            return -value

        def __pos__(self):
            return +value

        def __abs__(self):
            return abs(value)

        def __invert__(self):
            return ~value

        def __complex__(self):
            return complex(value)

        def __int__(self):
            return int(value)

        def __float__(self):
            return float(value)

        def __iter__(self):
            return iter(value)

        def __len__(self):
            return len(value)

        def __getitem__(self, item):
            return value[item]

        def __contains__(self, item):
            return item in value

        def __hash__(self):
            return hash(value)

        def __isinstance__(self, other):
            return isinstance(other, type(value))

        def __issubclass__(self, other):
            return issubclass(other, type(value))

    return DocumentedValue()


class PnsMeta(MultidictCache):
    _hub = None
    _subs = None
    _parent = None

    def __init__(self, data: list[dict[str, any]], parent: object):
        attrs = {}
        data.append(attrs)
        super().__init__(data, parent=parent)
        object.__setattr__(self, "_attrs", attrs)

    def __setitem__(self, key: str, value):
        # Recurse the dotted reference and set the value on the last part of the reference
        if "." in key:
            parts = key.split(".")
            finder = self
            for p in parts[:-1]:
                if not p:
                    continue
                if p not in finder:
                    finder[p] = NamespaceDict()
                finder = finder[p]

            finder[parts[len(parts) - 1]] = value
        else:
            self._attrs[key] = value

    def __setattr__(self, key: str, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self[key] = value
            self._clear()

    def __getattr__(self, item: str):
        """
        If the item should be loaded, load it, else serve it
        """
        if item.startswith("_"):
            return object.__getattribute__(self, item)
        elif "." in item:
            return pns.ref.last(self._hub, item)

        try:
            return self[item]
        except KeyError as e:
            name = getattr(self, "_subname", "hub")
            msg = f"'{name}' has no attribute '{item}'"
            raise AttributeError(msg) from e


class LoadedModGetAttr:
    """
    A cython abstraction for the LoadedMod's getattr function so that pns doesn't step into it while debugging
    and instead jumps straight to the function being called.
    """
    _attrs = None

    def __getattr__(self, item: str):
        if item == "__":
            return self._attrs.__
        elif item.startswith("_"):
            return self.__getattribute__(item)
        try:
            return self._attrs[item]
        except KeyError as e:
            raise AttributeError(e) from e


cdef class ImmutableNamespaceDict:
    cdef readonly dict __data

    def __init__(self, data=None):
        if isinstance(data, ImmutableNamespaceDict):
            self.__data = data.__data
        elif isinstance(data, dict):
            self.__data = {key: freeze(value) for key, value in data.items()}
        else:
            self.__data = {}

    def __getitem__(self, key):
        try:
            return self.__data[key]
        except KeyError:
            return ImmutableNamespaceDict()

    def __getattr__(self, key):
        if key in self.__data:
            return self.__data[key]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        if key == "_ImmutableNamespaceDict__data":
            object.__setattr__(self, key, value)
        else:
            raise TypeError("ImmutableNamespaceDict does not support attribute assignment")

    def __setitem__(self, key, value):
        raise TypeError("ImmutableNamespaceDict does not support item assignment")

    def __call__(self):
        return unfreeze(self.__data)

    def __len__(self):
        return len(self.__data)

    def __iter__(self):
        return iter(self.__data)

    def __bool__(self):
        return bool(self.__data)

    def __contains__(self, key):
        return key in self.__data

    def __repr__(self):
        return f"{self.__data}"

    def __eq__(self, other):
        if isinstance(other, ImmutableNamespaceDict):
            return self.__data == other.__data
        elif isinstance(other, dict):
            return self.__data == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def keys(self):
        return self.__data.keys()

    def values(self):
        return self.__data.values()

    def items(self):
        return self.__data.items()

    def get(self, key, default=None):
        return self.__data.get(key, default)

    def copy(self):
        return unfreeze(self.__data)


def freeze(data):
    if isinstance(data, ImmutableNamespaceDict):
        return data
    elif isinstance(data, dict):
        return ImmutableNamespaceDict({key: freeze(value) for key, value in data.items()})
    elif isinstance(data, list):
        return tuple(freeze(value) for value in data)
    elif isinstance(data, set):
        return frozenset(freeze(value) for value in data)
    else:
        return data


def unfreeze(data):
    if isinstance(data, ImmutableNamespaceDict):
        return {key: unfreeze(value) for key, value in data.items()}
    elif isinstance(data, frozenset):
        return {unfreeze(value) for value in data}
    elif isinstance(data, tuple):
        return [unfreeze(value) for value in data]
    else:
        return data


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
