from collections import UserDict

class NamespaceDict(UserDict):
    def __getattr__(self, key: str):
        if key in self.data:
            return self.data[key]
        return super().__getattribute__(key)

def update(dest:dict, upd:dict, recursive_update:bool=True, merge_lists:bool=False):
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
            if isinstance(dest_subkey, dict) and isinstance(val, dict):
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
