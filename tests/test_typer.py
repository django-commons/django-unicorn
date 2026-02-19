import datetime
from dataclasses import dataclass
from typing import get_type_hints as typing_get_type_hints

from pydantic import BaseModel

from django_unicorn.components import UnicornView
from django_unicorn.typer import cast_attribute_value, cast_value, get_type_hints
from example.coffee.models import Flavor


def test_get_type_hints():
    def test_func(input_str: str):
        return input_str

    expected = {"input_str": str}
    actual = get_type_hints(test_func)
    assert actual == expected


def test_get_type_hints_missing_type_hints():
    def test_func(input_str):
        return input_str

    expected = {}
    actual = get_type_hints(test_func)
    assert actual == expected


def test_get_type_hints_gh_639():
    class MyComponentView(UnicornView):
        a_date: datetime.date

    actual = get_type_hints(MyComponentView(component_name="test", component_id="test_get_type_hints_gh_639"))

    assert "a_date" in actual
    assert actual["a_date"] == datetime.date


class TestClass:
    integer: int
    boolean: bool


def test_cast_attribute_value_int():
    expected = 1
    actual = cast_attribute_value(TestClass(), "integer", "1")

    assert expected == actual


def test_cast_attribute_value_bool_true():
    expected = True
    actual = cast_attribute_value(TestClass(), "boolean", "True")

    assert expected == actual


def test_cast_attribute_value_bool_false():
    expected = False
    actual = cast_attribute_value(TestClass(), "boolean", "False")

    assert expected == actual


def test_cast_attribute_value_bool_invalid():
    expected = False
    actual = cast_attribute_value(TestClass(), "boolean", "asdf")

    assert expected == actual


class ExampleClass:
    a_model: Flavor
    optional_model: Flavor | None


def test_cast_value_model_none():
    example_class = ExampleClass()
    type_hints = typing_get_type_hints(example_class)
    type_hint = type_hints["a_model"]

    actual = cast_value(type_hint, None)

    assert actual is None


def test_cast_value_model_dict():
    example_class = ExampleClass()
    type_hints = typing_get_type_hints(example_class)
    type_hint = type_hints["a_model"]

    actual = cast_value(type_hint, {"id": 1})

    assert actual == {"id": 1}


def test_cast_value_optional():
    type_hints = typing_get_type_hints(ExampleClass())
    type_hint = type_hints["optional_model"]

    actual = cast_value(type_hint, None)

    assert actual is None


def test_cast_value_model_int():
    example_class = ExampleClass()
    example_class.a_model = Flavor()

    type_hints = typing_get_type_hints(example_class)
    type_hint = type_hints["optional_model"]

    actual = cast_value(type_hint, 1)

    assert actual == 1


@dataclass
class DataClass:
    name: str


class PydanticBaseModel(BaseModel):
    name: str


class AnotherExampleClass:
    data: DataClass
    list_data: list[DataClass]
    pydantic_data: PydanticBaseModel
    pydantic_list_data: list[PydanticBaseModel]


def test_cast_value_dataclass():
    example_class = AnotherExampleClass()
    test_data = DataClass(name="foo")
    example_class.data = test_data
    type_hints = typing_get_type_hints(example_class)
    type_hint = type_hints["data"]
    actual = cast_value(type_hint, {"name": "foo"})
    assert actual == test_data


def test_cast_value_pydantic():
    example_class = AnotherExampleClass()
    test_data = PydanticBaseModel(name="foo")
    example_class.pydantic_data = test_data
    type_hints = typing_get_type_hints(example_class)
    type_hint = type_hints["pydantic_data"]
    actual = cast_value(type_hint, {"name": "foo"})
    assert actual == test_data


def test_cast_value_list_dataclass():
    example_class = AnotherExampleClass()
    test_data = DataClass(name="foo")
    example_class.list_data = [test_data]
    type_hints = typing_get_type_hints(example_class)
    type_hint = type_hints["list_data"]
    actual = cast_value(type_hint, [{"name": "foo"}])
    assert actual == [test_data]


def test_cast_value_list_pydantic():
    example_class = AnotherExampleClass()
    test_data = PydanticBaseModel(name="foo")
    example_class.pydantic_list_data = [test_data]
    type_hints = typing_get_type_hints(example_class)
    type_hint = type_hints["pydantic_list_data"]
    actual = cast_value(type_hint, [{"name": "foo"}])
    assert actual == [test_data]

class ComponentWithRanks:
    ranks: tuple[dict[str, float | str]]


def test_cast_value_tuple_of_dicts_gh641():
    """cast_value restores float values inside tuple[dict[str, float|str]] (#641)."""
    type_hints = typing_get_type_hints(ComponentWithRanks)
    type_hint = type_hints["ranks"]

    # Simulates data arriving from browser: floats were stringified by _fix_floats
    value = [{"name": "abc", "score": "3.4"}]
    actual = cast_value(type_hint, value)

    # Result must be a tuple (not a list)
    assert isinstance(actual, tuple)
    assert len(actual) == 1
    # String "3.4" must be cast back to float 3.4 via the float|str value type hint
    assert actual[0]["name"] == "abc"
    assert actual[0]["score"] == 3.4
    assert isinstance(actual[0]["score"], float)


def test_cast_value_dict_float_str_gh641():
    """cast_value casts string float values inside dict[str, float|str] (#641)."""
    from typing import get_type_hints as typing_get_type_hints

    class ComponentWithDict:
        data: dict[str, float | str]

    type_hints = typing_get_type_hints(ComponentWithDict)
    type_hint = type_hints["data"]

    actual = cast_value(type_hint, {"name": "abc", "score": "3.4"})

    assert actual["name"] == "abc"
    assert actual["score"] == 3.4
    assert isinstance(actual["score"], float)


class ComponentWithTupleOfDataclasses:
    items: tuple[DataClass]


def test_cast_value_tuple_of_dataclasses_gh641():
    """cast_value recursively casts items inside a tuple[Dataclass] (#641)."""
    type_hints = typing_get_type_hints(ComponentWithTupleOfDataclasses)
    type_hint = type_hints["items"]

    value = [{"name": "foo"}, {"name": "bar"}]
    actual = cast_value(type_hint, value)

    assert isinstance(actual, tuple)
    assert actual == (DataClass(name="foo"), DataClass(name="bar"))
