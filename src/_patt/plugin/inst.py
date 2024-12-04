"""
Inst - The instance pattern
===========================

Overview
--------

In POP, you don't use classes and polymorphism in the same ways that you may be accustomed to.
Classes should primarily be used to define types - something we rarely need - or they are used
to build abstractions on top of the hub.  All data stored on the hub should use basic,
JSON-serializable types, which makes interfaces simple, clean, and portable.

This pattern allows you to define, create, and manage instances of your sub with predictable attributes,
ensuring type safety and consistency.  Instances are stored on the hub in a structure that is easy to
access and manipulate.

Why Use This Pattern
---------------------

- **Consistency**: Ensure that instances have a predefined set of attributes with specified types.
- **Type Safety**: Automatically validate the types of values assigned to instance attributes.
- **Simplicity**: Leverage basic Python data structures, making the system easy to understand and extend.
- **Flexibility**: Dynamically create and manage instances based on your needs.

How It Works
------------

Define an Instance
~~~~~~~~~~~~~~~~~~

First, define what an instance of your sub is. This can be as simple as:

    await hub.patt.inst.init(
        key1=str,
        key2=int,
        key3=dict[str, list[int]],
        key4=None,
        key5=hub.lib.typing.Literal["value1", "value2"]
    )

If called from a function within your sub, the base_sub will be inferred. Otherwise, you can name it explicitly:

    await hub.patt.inst.init(
        "my_base",
        key1=str,
        key2=int,
        key3=dict[str, list[int]],
        key4=None,
        key5=hub.lib.typing.Literal["value1", "value2"]
    )

Create an Instance
~~~~~~~~~~~~~~~~~~

Now you can create instances of an object with predictable attributes on your sub:

    await hub.patt.inst.create(name="my_instance", key1="", key2=0, key3={"":[0]}, key4=object())

Retrieve an Instance
~~~~~~~~~~~~~~~~~~~~

To retrieve this instance, just use its name:

    instance = await hub.patt.inst.get("my_instance")

You can access the keys of the instance with the namespace:

    instance.key1

Changes made to the instance will be persistent:

    instance.key1 = "asdf"

If a type was defined for a key, it will be type-checked when the value is changed.
"""

# Control keys for an instance's behavior
RESTRICT_NEW_KEYS = "__restrict_new_keys__"
VALIDATE_KEYS = "__validate_keys__"
KEYS = "__keys__"


async def __init__(hub):
    """
    Initialize the INSTANCES structure as a defaultdict of dictionaries.
    The structure will be INSTANCES[base_sub][name] = {<keys>}
    """
    hub.patt.inst.INSTANCES = hub.lib.collections.defaultdict(dict)


async def init(
    hub,
    _base_sub: str = None,
    *,
    validate_keys: bool = True,
    restrict_new_keys: bool = True,
    **kwargs: dict[str, type],
):
    """
    Define what makes an instance of "base_sub".

    Args:
        _base_sub (str): The base sub name. If None, it will be inferred.
        validate_keys (bool): Whether to validate values when they are added to an instance.
        restrict_new_keys (bool): Whether to prevent dynamic creation of new keys.
        kwargs (dict[str, type]): A dictionary defining the keys and their types for the instance.

    Raises:
        KeyError: If the base_sub is already defined.
    """

    if _base_sub is None:
        _base_sub = _get_base_sub(hub)

    if _base_sub in hub.patt.inst.INSTANCES:
        msg = f"'{_base_sub}' is already defined"
        raise KeyError(msg)

    hub.patt.inst.INSTANCES[_base_sub][KEYS] = dict(kwargs)
    hub.patt.inst.INSTANCES[_base_sub][VALIDATE_KEYS] = validate_keys
    hub.patt.inst.INSTANCES[_base_sub][RESTRICT_NEW_KEYS] = restrict_new_keys


async def create(hub, _name: str, _base_sub: str = None, **kwargs):
    """
    Make an instance of the base_sub with the given key/value pairs.

    Args:
        _name (str): The name of the instance.
        _base_sub (str): The base sub name. If None, it will be inferred.
        kwargs (dict): Key/value pairs to initialize the instance.

    Raises:
        ValueError: If an instance with the same name already exists.
    """
    if _base_sub is None:
        _base_sub = _get_base_sub(hub)

    if _name in hub.patt.inst.INSTANCES[_base_sub]:
        msg = f"'{_name}' instance of '{_base_sub}' already exists"
        raise ValueError(msg)

    # "init" hasn't been run yet, guess what it should be based on "create" parameters
    if _base_sub not in hub.patt.inst.INSTANCES:
        keys = {k: type(v) for k, v in kwargs.items()}
        await hub.patt.inst.init(_base_sub, **keys)

    keys = hub.patt.inst.INSTANCES[_base_sub].get(KEYS, {})

    values = hub.lib.cpop.data.NamespaceDict(
        {key: await hub.patt.inst.initialize_value(typ) for key, typ in keys.items()}
    )
    validate_keys = hub.patt.inst.INSTANCES[_base_sub].get(VALIDATE_KEYS)
    restrict_new_keys = hub.patt.inst.INSTANCES[_base_sub].get(RESTRICT_NEW_KEYS)

    class PattInstance(hub.lib.cpop.data.NamespaceDict):
        __name__ = _name

        def __setitem__(self, key: str, value):
            if key in keys:
                expected_type = keys[key]
                if expected_type is not None and validate_keys:
                    _validate_type(hub, value, expected_type)
                dict.__setitem__(self, key, value)
            elif restrict_new_keys:
                msg = f"Key '{key}' not found in instance definition"
                raise KeyError(msg)
            else:
                # This is a new key
                keys[key] = type(value) if validate_keys else None
            dict.__setitem__(self, key, value)

    instance = PattInstance(**values)
    for k, v in kwargs.items():
        instance[k] = v
    hub.patt.inst.INSTANCES[_base_sub][_name] = instance


async def get(hub, name: str, base_sub: str = None):
    """
    Retrieve the named instance of the base_sub.

    Args:
        name (str): The name of the instance to retrieve.
        base_sub (str): The base sub name. If None, it will be inferred.

    Returns:
        Any: The requested instance.

    Raises:
        KeyError: If the instance is not found.
    """
    if base_sub is None:
        base_sub = _get_base_sub(hub)
    return hub.patt.inst.INSTANCES[base_sub][name]


async def delete(hub, name: str, base_sub: str = None):
    """
    Delete the named instance of the base_sub.

    Args:
        name (str): The name of the instance to delete.
        base_sub (str): The base sub name. If None, it will be inferred.
    """
    if base_sub is None:
        base_sub = _get_base_sub(hub)

    hub.patt.inst.INSTANCES[base_sub].pop(name, None)

    if base_sub is None:
        base_sub = _get_base_sub(hub)

    hub.patt.inst.INSTANCES[base_sub].pop(name, None)


async def initialize_value(hub, typ):
    """
    Find the empty value for the given type and return it.

    Args:
        typ: The type for which to find the empty value.

    Returns:
        Any: The empty value corresponding to the given type.
    """
    if typ is None:
        return None
    origin = hub.lib.typing.get_origin(typ)
    if origin is list:
        return []
    if origin is dict:
        return {}
    if typ in {int, float, str, bool}:
        return typ()

    return None


def _get_base_sub(hub) -> str:
    """
    Get the base sub of the last thing on the hub's call stack.
    This will be used as the default instance type.

    Returns:
        str: The base sub name of the caller.
    """
    return hub._last_call._last_call.ref.rsplit(".")[0]


def _validate_type(hub, value, expected):
    """
    Ensure that the given value matches the expected type.

    Args:
        value: The value to validate.
        expected: The expected type of the value.

    Raises:
        TypeError: If the value does not match the expected type.
    """
    origin = hub.lib.typing.get_origin(expected)

    if origin is list:
        if not isinstance(value, list):
            msg = f"Expected a list for key, got {type(value)}"
            raise TypeError(msg)
        inner_type = hub.lib.typing.get_args(expected)[0]
        for item in value:
            _validate_type(hub, item, inner_type)
    elif origin is dict:
        if not isinstance(value, dict):
            msg = f"Expected a dict for key, got {type(value)}"
            raise TypeError(msg)
        key_type, val_type = hub.lib.typing.get_args(expected)
        for k, v in value.items():
            _validate_type(hub, k, key_type)
            _validate_type(hub, v, val_type)
    elif origin is hub.lib.typing.Literal:
        if value not in hub.lib.typing.get_args(expected):
            msg = f"Expected one of {hub.lib.typing.get_args(expected)} for value, got {value}"
            raise TypeError(msg)
    elif not isinstance(value, expected) and value is not None:
        msg = f"Expected {expected} for value, got {type(value)}"
        raise TypeError(msg)
