import json
import uuid
from datetime import timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import cast

import pytest
from django.db import models
from django.db.models import Model
from django.utils.timezone import now
from pydantic import BaseModel

from django_unicorn import serializer
from django_unicorn.serializer import InvalidFieldAttributeError, InvalidFieldNameError
from django_unicorn.utils import dicts_equal
from example.coffee.models import Flavor, NewFlavor, Taste


class SimpleTestModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "tests"


class SubclassSimpleTestModel(SimpleTestModel):
    subclass_name = models.CharField(max_length=10)

    class Meta:
        app_label = "tests"


class ComplicatedTestModel(models.Model):
    name = models.CharField(max_length=10)
    datetime = models.DateTimeField(auto_now=True, auto_now_add=True)
    float_value = models.FloatField(default=0.583)
    decimal_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.984)
    uuid = models.UUIDField(default=uuid.uuid4)
    date = models.DateField(auto_now=True, auto_now_add=True)
    time = models.TimeField(auto_now=True, auto_now_add=True)
    duration = models.DurationField(default="-1 day, 19:00:00")

    class Meta:
        app_label = "tests"


class SubclassComplicatedTestModel(ComplicatedTestModel):
    subclass_name = models.CharField(max_length=10)

    class Meta:
        app_label = "tests"


class ForeignKeyTestModel(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = "tests"


class SubclassForeignKeyTestModel(ForeignKeyTestModel):
    subclass_name = models.CharField(max_length=10)

    class Meta:
        app_label = "tests"


class ManyToManyTestModel(models.Model):
    name = models.CharField(max_length=10)
    parents = models.ManyToManyField("self")

    class Meta:
        app_label = "tests"


class SubclassManyToManyTestModel(ManyToManyTestModel):
    subclass_name = models.CharField(max_length=10)

    class Meta:
        app_label = "tests"


def assert_dicts(expected: dict, serialized_dumps: str) -> None:
    actual = json.loads(serialized_dumps)

    assert dicts_equal(expected, actual)


def test_int():
    expected = '{"name":123}'
    actual = serializer.dumps({"name": 123})

    assert expected == actual


def test_decimal():
    expected = '{"name":"123.1"}'
    actual = serializer.dumps({"name": Decimal("123.1")})

    assert expected == actual


def test_mapping_proxy_type():
    expected = '{"name":{"id":"123.1"}}'
    actual = serializer.dumps({"name": MappingProxyType({"id": Decimal("123.1")})})

    assert expected == actual


def test_string():
    expected = '{"name":"abc"}'
    actual = serializer.dumps({"name": "abc"})

    assert expected == actual


def test_list():
    expected = '{"name":["abc","def"]}'
    actual = serializer.dumps(
        {
            "name": [
                "abc",
                "def",
            ]
        }
    )

    assert expected == actual


def test_simple_model():
    expected = {"name": "abc", "pk": 1}

    simple_test_model = SimpleTestModel(id=1, name="abc")
    actual = serializer.dumps(simple_test_model)

    assert_dicts(expected, actual)


def test_subclass_simple_model():
    expected = {"subclass_name": "def", "pk": 2, "name": "abc"}

    subclass_simple_test_model = SubclassSimpleTestModel(id=2, name="abc", subclass_name="def")
    actual = serializer.dumps(subclass_simple_test_model)

    assert_dicts(expected, actual)


def test_complicated_model():
    now_dt = now()
    duration = timedelta(days=-1, seconds=68400)

    model = ComplicatedTestModel(
        id=2,
        name="abc",
        datetime=now_dt,
        date=now_dt.date(),
        time=now_dt.time(),
        duration=duration,
    )

    expected = {
        "date": str(model.date),
        "datetime": model.datetime.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "decimal_value": "0.984",
        "duration": "-1 19:00:00",
        "float_value": "0.583",
        "name": "abc",
        "pk": 2,
        "time": str(model.time)[:-3],
        "uuid": str(model.uuid),
    }

    actual = serializer.dumps(model)

    assert_dicts(expected, actual)


def test_subclass_complicated_model():
    now_dt = now()
    duration = timedelta(days=-1, seconds=68400)

    model = SubclassComplicatedTestModel(
        id=2,
        name="abc",
        subclass_name="def",
        datetime=now_dt,
        date=now_dt.date(),
        time=now_dt.time(),
        duration=duration,
    )

    expected = {
        "subclass_name": "def",
        "pk": 2,
        "name": "abc",
        "datetime": model.datetime.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "float_value": "0.583",
        "decimal_value": "0.984",
        "uuid": str(model.uuid),
        "date": str(model.date),
        "time": str(model.time)[:-3],
        "duration": "-1 19:00:00",
    }

    actual = serializer.dumps(model)

    assert_dicts(expected, actual)


def test_model_with_timedelta(db):  # noqa: ARG001
    now_dt = now()
    duration = timedelta(days=-1, seconds=68400)

    flavor = Flavor(
        id=8,
        name="name1",
        datetime=now_dt,
        date=now_dt.date(),
        time=now_dt.time(),
        duration=duration,
    )

    expected = {
        "flavor": {
            "name": "name1",
            "label": "",
            "parent": None,
            "float_value": None,
            "decimal_value": None,
            "uuid": str(flavor.uuid),
            "date": str(now_dt.date()),
            "datetime": now_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "time": str(now_dt.time())[:-3],
            "duration": "-1 19:00:00",
            "pk": 8,
            "taste_set": [],
            "origins": [],
        }
    }

    actual = serializer.dumps({"flavor": flavor})

    assert_dicts(expected, actual)


def test_model_with_datetime_as_string(db):  # noqa: ARG001
    datetime = now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    flavor = Flavor(name="name1", datetime=datetime)

    expected = {
        "flavor": {
            "name": "name1",
            "label": "",
            "parent": None,
            "float_value": None,
            "decimal_value": None,
            "uuid": str(flavor.uuid),
            "date": None,
            "datetime": datetime.replace(".000", ""),
            "time": None,
            "duration": None,
            "pk": None,
            "taste_set": [],
            "origins": [],
        }
    }

    actual = serializer.dumps({"flavor": flavor})

    assert_dicts(expected, actual)


def test_model_with_time_as_string(db):  # noqa: ARG001
    time = now().strftime("%H:%M:%S.%f")[:-3]
    flavor = Flavor(name="name1", time=time)

    expected = {
        "flavor": {
            "name": "name1",
            "label": "",
            "parent": None,
            "float_value": None,
            "decimal_value": None,
            "uuid": str(flavor.uuid),
            "date": None,
            "datetime": None,
            "time": time,
            "duration": None,
            "pk": None,
            "taste_set": [],
            "origins": [],
        }
    }

    actual = serializer.dumps({"flavor": flavor})

    assert_dicts(expected, actual)


def test_model_with_duration_as_string(db):  # noqa: ARG001
    duration = "-1 day, 19:00:00"
    flavor = Flavor(name="name1", duration=duration)

    expected = {
        "flavor": {
            "name": "name1",
            "label": "",
            "parent": None,
            "float_value": None,
            "decimal_value": None,
            "uuid": str(flavor.uuid),
            "date": None,
            "datetime": None,
            "time": None,
            "duration": "-1 19:00:00",
            "pk": None,
            "taste_set": [],
            "origins": [],
        }
    }

    actual = serializer.dumps({"flavor": flavor})

    assert_dicts(expected, actual)


def test_model_foreign_key():
    test_model_one = ForeignKeyTestModel(id=1, name="abc")
    test_model_two = ForeignKeyTestModel(id=2, name="def", parent=test_model_one)
    expected = {"test_model_two": {"name": "def", "parent": 1, "pk": 2}}

    actual = serializer.dumps({"test_model_two": test_model_two})

    assert_dicts(expected, actual)


def test_model_foreign_key_subclass():
    test_model_one = ForeignKeyTestModel(id=1, name="abc")
    test_model_two = SubclassForeignKeyTestModel(id=2, name="def", subclass_name="ghi", parent=test_model_one)
    expected = {"name": "def", "parent": 1, "pk": 2, "subclass_name": "ghi"}

    actual = serializer.dumps(test_model_two)

    assert_dicts(expected, actual)


@pytest.mark.django_db
def test_model_inherited_model_with_many_to_many_and_foreign_key():
    flavor_one = Flavor(id=3, name="name0")
    flavor_one.save()

    flavor_two = NewFlavor(id=4, new_name="new_name_1", name="name_1", parent=flavor_one)
    flavor_two.save()

    taste1 = Taste(name="Bitter1")
    taste1.save()
    flavor_two.taste_set.add(taste1)  # type: ignore

    expected = {
        "new_name": "new_name_1",
        "pk": 4,
        "taste_set": [1],
        "origins": [],
        "name": "name_1",
        "label": "",
        "parent": 3,
        "float_value": "null",
        "decimal_value": "null",
        "uuid": str(flavor_two.uuid),
        "datetime": "null",
        "date": "null",
        "time": "null",
        "duration": "null",
    }

    actual = serializer.dumps(flavor_two)

    assert_dicts(expected, actual)


def test_model_foreign_key_recursive_parent():
    test_model_one = ForeignKeyTestModel(id=1, name="abc")
    test_model_two = ForeignKeyTestModel(id=2, name="def", parent=test_model_one)
    test_model_one.parent = test_model_two
    expected = '{"test_model_two":{"name":"def","parent":1,"pk":2}}'

    actual = serializer.dumps({"test_model_two": test_model_two})

    assert expected == actual


@pytest.mark.django_db
def test_model_many_to_many(django_assert_num_queries):
    flavor_one = Flavor(name="name1", label="label1")
    flavor_one.save()

    taste1 = Taste(name="Bitter1")
    taste1.save()
    taste2 = Taste(name="Bitter2")
    taste2.save()
    taste3 = Taste(name="Bitter3")
    taste3.save()

    flavor_one.taste_set.add(taste1)  # type: ignore
    flavor_one.taste_set.add(taste2)  # type: ignore
    flavor_one.taste_set.add(taste3)  # type: ignore

    with django_assert_num_queries(2):
        actual = json.loads(serializer.dumps(flavor_one))

    expected = {
        "name": "name1",
        "label": "label1",
        "parent": None,
        "float_value": None,
        "decimal_value": None,
        "uuid": str(flavor_one.uuid),
        "datetime": None,
        "date": None,
        "time": None,
        "duration": None,
        "pk": 1,
        "taste_set": [taste1.pk, taste2.pk, taste3.pk],
        "origins": [],
    }

    assert dicts_equal(expected, actual)


@pytest.mark.django_db
def test_model_many_to_many_with_excludes(django_assert_num_queries):
    flavor_one = Flavor(name="name1", label="label1")
    flavor_one.save()

    taste1 = Taste(name="Bitter1")
    taste1.save()
    taste2 = Taste(name="Bitter2")
    taste2.save()
    taste3 = Taste(name="Bitter3")
    taste3.save()

    flavor_one.taste_set.add(taste1)  # type: ignore
    flavor_one.taste_set.add(taste2)  # type: ignore
    flavor_one.taste_set.add(taste3)  # type: ignore

    flavor_one = Flavor.objects.prefetch_related("taste_set", "origins").get(pk=flavor_one.pk)

    # This shouldn't make any database calls because of the prefetch_related
    with django_assert_num_queries(0):
        actual = serializer.dumps(
            {"flavor": flavor_one},
            exclude_field_attributes=(
                "flavor.taste_set",
                "flavor.origins",
            ),
        )
        actual = json.loads(actual)

    expected = {
        "flavor": {
            "name": "name1",
            "label": "label1",
            "parent": None,
            "float_value": None,
            "decimal_value": None,
            "uuid": str(flavor_one.uuid),
            "datetime": None,
            "date": None,
            "time": None,
            "duration": None,
            "pk": 1,
        }
    }

    assert dicts_equal(expected, actual)


@pytest.mark.django_db
def test_dumps_queryset(db):  # noqa: ARG001
    flavor_one = Flavor(name="name1", label="label1")
    flavor_one.save()

    flavor_two = Flavor(name="name2", label="label2", parent=flavor_one)
    flavor_two.save()

    flavors = Flavor.objects.all()

    expected = {
        "flavors": [
            {
                "name": "name1",
                "label": "label1",
                "parent": None,
                "float_value": None,
                "decimal_value": None,
                "uuid": str(flavor_one.uuid),
                "date": None,
                "datetime": None,
                "time": None,
                "duration": None,
                "pk": 1,
                "taste_set": [],
                "origins": [],
            },
            {
                "name": "name2",
                "label": "label2",
                "parent": 1,
                "float_value": None,
                "decimal_value": None,
                "uuid": str(flavor_two.uuid),
                "date": None,
                "datetime": None,
                "time": None,
                "duration": None,
                "pk": 2,
                "taste_set": [],
                "origins": [],
            },
        ]
    }

    actual = json.loads(serializer.dumps({"flavors": flavors}))
    assert dicts_equal(expected, actual)


def test_get_model_dict():
    flavor_one = Flavor(name="name1", label="label1")
    actual = serializer._get_model_dict(flavor_one)

    expected = {
        "pk": None,
        "name": "name1",
        "label": "label1",
        "parent": None,
        "decimal_value": None,
        "float_value": None,
        "uuid": str(flavor_one.uuid),
        "date": None,
        "datetime": None,
        "time": None,
        "duration": None,
        "taste_set": [],
        "origins": [],
    }

    assert dicts_equal(expected, actual)


@pytest.mark.django_db
def test_get_model_dict_many_to_many_is_referenced(django_assert_num_queries):
    flavor_one = Flavor(name="name1", label="label1")
    flavor_one.save()

    taste1 = Taste(name="Bitter")
    taste1.save()
    taste2 = Taste(name="Bitter2")
    taste2.save()
    taste3 = Taste(name="Bitter3")
    taste3.save()

    flavor_one.taste_set.add(taste1)  # type: ignore
    flavor_one.taste_set.add(taste2)  # type: ignore
    flavor_one.taste_set.add(taste3)  # type: ignore

    expected = {
        "pk": 1,
        "name": "name1",
        "label": "label1",
        "parent": None,
        "decimal_value": None,
        "float_value": None,
        "uuid": str(flavor_one.uuid),
        "date": None,
        "datetime": None,
        "time": None,
        "duration": None,
        "taste_set": [taste1.pk, taste2.pk, taste3.pk],
        "origins": [],
    }

    flavor_one = Flavor.objects.filter(id=flavor_one.id).first()  # type: ignore

    with django_assert_num_queries(2):
        actual = serializer._get_model_dict(cast(Model, flavor_one))

    assert dicts_equal(expected, actual)


@pytest.mark.django_db
def test_get_model_dict_many_to_many_is_referenced_prefetched(
    django_assert_num_queries,
):
    flavor_one = Flavor(name="name1", label="label1")
    flavor_one.save()

    taste1 = Taste(name="Bitter")
    taste1.save()
    taste2 = Taste(name="Bitter2")
    taste2.save()
    taste3 = Taste(name="Bitter3")
    taste3.save()

    flavor_one.taste_set.add(taste1)  # type: ignore
    flavor_one.taste_set.add(taste2)  # type: ignore
    flavor_one.taste_set.add(taste3)  # type: ignore

    expected = {
        "pk": 1,
        "name": "name1",
        "label": "label1",
        "parent": None,
        "decimal_value": None,
        "float_value": None,
        "uuid": str(flavor_one.uuid),
        "date": None,
        "datetime": None,
        "time": None,
        "duration": None,
        "taste_set": [taste1.pk, taste2.pk, taste3.pk],
        "origins": [],
    }

    flavor_one = Flavor.objects.prefetch_related("taste_set").filter(pk=flavor_one.pk).first()

    # prefetch_related should reduce the database calls
    with django_assert_num_queries(1):
        actual = serializer._get_model_dict(cast(Model, flavor_one))

    assert dicts_equal(expected, actual)


@pytest.mark.django_db
def test_get_model_dict_many_to_many_references_model():
    taste = Taste(name="Bitter")
    taste.save()
    flavor_one = Flavor(name="name1", label="label1")
    flavor_one.save()
    flavor_one.taste_set.add(taste)  # type: ignore
    actual = serializer._get_model_dict(taste)

    expected = {"name": taste.name, "flavor": [flavor_one.pk], "pk": taste.pk}

    assert dicts_equal(expected, actual)


def test_float():
    expected = '{"name":"0.0"}'
    actual = serializer.dumps({"name": 0.0})

    assert expected == actual


def test_dict_float():
    expected = '{"name":{"another":"0.0"}}'
    actual = serializer.dumps({"name": {"another": 0.0}})

    assert expected == actual


def test_list_float():
    expected = '{"name":[1,2,"0.0"]}'
    actual = serializer.dumps({"name": [1, 2, 0.0]})

    assert expected == actual


def test_nested_list_float():
    expected = '{"name":{"blob":[1,2,"0.0"]}}'
    actual = serializer.dumps({"name": {"blob": [1, 2, 0.0]}})

    assert expected == actual


def test_nested_list_float_complicated():
    expected = '{"another":[{"great":"1.0","ok":["1.6","0.0",4]}],"more":["1.9",2,5],"name":{"blob":[1,2,"0.0"]}}'
    actual = serializer.dumps(
        {
            "name": {"blob": [1, 2, 0.0]},
            "more": [1.9, 2, 5],
            "another": [{"great": 1.0, "ok": [1.6, 0.0, 4]}],
        }
    )

    assert expected == actual


def test_nested_list_float_less_complicated():
    expected = '{"another":[{"great":"1.0","ok":["1.6","0.0",4]}]}'
    actual = serializer.dumps(
        {
            "another": [{"great": 1.0, "ok": [1.6, 0.0, 4]}],
        }
    )

    assert expected == actual


def test_pydantic():
    class Book(BaseModel):
        title: str = "The Grapes of Wrath"
        author: str = "John Steinbeck"

    expected = '{"author":"John Steinbeck","title":"The Grapes of Wrath"}'
    actual = serializer.dumps(Book())

    assert expected == actual


def test_exclude_field_attributes():
    expected = '{"book":{"title":"The Grapes of Wrath"}}'

    actual = serializer.dumps(
        {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}},
        exclude_field_attributes=("book.author",),
    )

    assert expected == actual


def test_exclude_field_attributes_no_fix_floats():
    expected = '{"book":{"title":"The Grapes of Wrath"}}'

    actual = serializer.dumps(
        {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}},
        fix_floats=False,
        exclude_field_attributes=("book.author",),
    )

    assert expected == actual


def test_exclude_field_attributes_nested():
    expected = '{"classic":{"book":{"title":"The Grapes of Wrath"}}}'

    actual = serializer.dumps(
        {"classic": {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}}},
        exclude_field_attributes=("classic.book.author",),
    )

    assert expected == actual


def test_exclude_field_attributes_invalid_field_attribute():
    expected = '{"book":{"author":"John Steinbeck","title":"The Grapes of Wrath"}}'

    actual = serializer.dumps(
        {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}},
        exclude_field_attributes=("blob",),
    )

    assert expected == actual


def test_exclude_field_attributes_empty_string():
    expected = '{"book":{"author":"John Steinbeck","title":"The Grapes of Wrath"}}'

    actual = serializer.dumps(
        {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}},
        exclude_field_attributes=("",),
    )

    assert expected == actual


def test_exclude_field_attributes_none():
    expected = '{"book":{"author":"John Steinbeck","title":"The Grapes of Wrath"}}'

    actual = serializer.dumps(
        {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}},
        exclude_field_attributes=None,
    )

    assert expected == actual


def test_exclude_field_attributes_invalid_name():
    with pytest.raises(InvalidFieldNameError) as e:
        serializer.dumps(
            {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}},
            exclude_field_attributes=("blob.monster",),
        )

    assert e.exconly() == "django_unicorn.serializer.InvalidFieldNameError: Cannot resolve 'blob'. Choices are: book"


def test_exclude_field_attributes_invalid_attribute():
    with pytest.raises(InvalidFieldAttributeError) as e:
        serializer.dumps(
            {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}},
            exclude_field_attributes=("book.blob",),
        )

    assert (
        e.exconly()
        == "django_unicorn.serializer.InvalidFieldAttributeError: Cannot resolve 'blob'. Choices on 'book' are: title, author"  # noqa: E501
    )


def test_exclude_field_attributes_invalid_type():
    with pytest.raises(AssertionError):
        serializer.dumps(
            {"book": {"title": "The Grapes of Wrath", "author": "John Steinbeck"}},
            exclude_field_attributes=("book.blob"),  # type: ignore
        )


def test_dictionary_with_int_keys_as_strings():
    # Browsers will sort a dictionary that has stringified integers as if they the keys
    # were integers which messes up checksum calculation
    expected = '{"1":"a","2":"b","4":"c","11":"d","24":"e"}'

    actual = serializer.dumps(
        {
            "11": "d",
            "4": "c",
            "1": "a",
            "24": "e",
            "2": "b",
        }
    )

    assert expected == actual


def test_dictionary_with_int_keys_as_strings_no_sort():
    expected = '{"11":"d","4":"c","1":"a","24":"e","2":"b"}'

    actual = serializer.dumps(
        {
            "11": "d",
            "4": "c",
            "1": "a",
            "24": "e",
            "2": "b",
        },
        sort_dict=False,
    )

    assert expected == actual


def test_tuple_float():
    """Float inside a tuple is stringified for safe JS transmission (#641)."""
    import json

    actual = serializer.dumps({"ranks": ({"name": "abc", "score": 3.4},)})
    data = json.loads(actual)

    assert data["ranks"][0]["score"] == "3.4"


def test_tuple_of_dicts_mixed_types():
    """Multiple floats and non-floats inside a tuple of dicts are handled (#641)."""
    import json

    actual = serializer.dumps(
        {
            "ranks": (
                {"name": "abc", "score": 3.4},
                {"name": "def", "score": 1.0},
                {"name": "ghi", "score": 5},
            )
        }
    )
    data = json.loads(actual)

    assert data["ranks"][0]["score"] == "3.4"
    assert data["ranks"][1]["score"] == "1.0"
    assert data["ranks"][2]["score"] == 5  # int stays as int
