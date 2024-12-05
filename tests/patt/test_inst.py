import pytest


async def test_init(hub):
    """
    Test the init function to ensure it initializes the instances structure correctly.
    """
    await hub.test.init.init(key1=str, key2=int, key3=dict[str, list[int]], key4=None)
    assert "test" in hub.patt.inst.INSTANCES


async def test_create_instance(hub):
    """
    Test creating an instance and verify its attributes and type checking.
    """
    await hub.test.init.init(key1=str, key2=int, key3=dict[str, list[int]], key4=None)
    await hub.test.init.create("my_instance", key1="", key2=0, key3={"": [0]}, key4=object())

    instance = await hub.test.init.get("my_instance")
    assert instance.key1 == ""
    assert instance.key2 == 0
    assert instance.key3 == {"": [0]}
    assert isinstance(instance.key4, object)

    with pytest.raises(TypeError):
        instance.key1 = 123  # Should raise a TypeError


async def test_retrieve_instance(hub):
    """
    Test retrieving an instance and verifying its attributes.
    """
    await hub.test.init.init(key1=str, key2=int, key3=dict[str, list[int]], key4=None)
    await hub.test.init.create("my_instance", key1="test", key2=42, key3={"numbers": [1, 2]}, key4=None)

    instance = await hub.test.init.get("my_instance")
    assert instance.key1 == "test"
    assert instance.key2 == 42
    assert instance.key3 == {"numbers": [1, 2]}
    assert instance.key4 is None


async def test_update_instance(hub):
    """
    Test updating an instance and verifying the changes.
    """
    await hub.test.init.init(key1=str, key2=int, key3=dict[str, list[int]], key4=None)
    await hub.test.init.create("my_instance", key1="initial", key2=5, key3={}, key4=None)

    instance = await hub.test.init.get("my_instance")
    instance.key1 = "updated"
    instance.key2 = 10
    instance.key3 = {"new_key": [3, 4]}

    assert instance.key1 == "updated"
    assert instance.key2 == 10
    assert instance.key3 == {"new_key": [3, 4]}


async def test_delete_instance(hub):
    """
    Test deleting an instance and verifying it no longer exists.
    """
    await hub.test.init.init(key1=str, key2=int, key3=dict[str, list[int]], key4=None)
    await hub.test.init.create("my_instance", key1="value", key2=99, key3={}, key4=None)

    await hub.test.init.delete("my_instance")

    with pytest.raises(KeyError):
        await hub.test.init.get("my_instance")


async def test_create_without_init(hub):
    """
    Test creating an instance without calling init and ensure the keys are inferred correctly.
    """
    await hub.test.init.create("inferred_instance", key1="inferred", key2=100)

    instance = await hub.test.init.get("inferred_instance")
    assert instance.key1 == "inferred"
    assert instance.key2 == 100


async def test_dynamic_key_creation(hub):
    """
    Test creating an instance and adding dynamic keys if restrict_new_keys is False.
    """
    await hub.test.init.init(
        key1=str,
        key2=int,
        key3=dict[str, list[int]],
        key4=None,
        restrict_new_keys=False,
    )
    await hub.test.init.create("dynamic_instance", key1="dynamic", key2=50, key3={}, key4=None)

    instance = await hub.test.init.get("dynamic_instance")
    instance.new_key = "new_value"
    assert instance.new_key == "new_value"

    instance.new_key2 = 123
    assert instance.new_key2 == 123


async def test_type_validation(hub):
    """
    Test type validation to ensure that values assigned to keys are of the correct type.
    """
    await hub.test.init.init(
        key1=str,
        key2=int,
        key3=dict[str, list[int]],
        key4=None,
        key5=hub.lib.typing.Literal["1", "2"],
        validate_keys=True,
    )
    await hub.test.init.create(
        "validation_instance",
        key1="validate",
        key2=20,
        key3={"check": [1, 2]},
        key4=None,
        key5="1",
    )

    instance = await hub.test.init.get("validation_instance")

    with pytest.raises(TypeError):
        instance.key2 = "should fail"  # Should raise TypeError because key2 is expected to be int

    with pytest.raises(TypeError):
        instance.key3 = {
            "check": "should fail"
        }  # Should raise TypeError because key3 is expected to be dict[str, list[int]]


async def test_no_type_validation(hub):
    """
    Test type validation being disabled
    """
    await hub.test.init.init(key1=str, key2=int, key3=dict[str, list[int]], key4=None, validate_keys=False)
    await hub.test.init.create(
        "validation_instance",
        key1="validate",
        key2=20,
        key3={"check": [1, 2]},
        key4=None,
    )

    instance = await hub.test.init.get("validation_instance")

    instance.key2 = "should succeed"

    instance.key3 = {"check": "should succeed"}


async def test_restrict_new_keys(hub):
    """
    Test restricting new key creation and ensure that keys not defined in init cannot be added.
    """
    await hub.test.init.init(key1=str, key2=int, restrict_new_keys=True)
    await hub.test.init.create("restricted_instance", key1="restricted", key2=10)

    instance = await hub.test.init.get("restricted_instance")

    with pytest.raises(KeyError):
        instance.new_key = "new value"  # Should raise KeyError because new keys are restricted


async def test_no_restrict_new_keys(hub):
    """
    Test permitting new keys to be added
    """
    await hub.test.init.init(key1=str, key2=int, restrict_new_keys=False)
    await hub.test.init.create("restricted_instance", key1="restricted", key2=10)

    instance = await hub.test.init.get("restricted_instance")

    instance.new_key = "new value"
