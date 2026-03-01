import uuid

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.dateparse import parse_duration
from django.utils.timezone import now

from django_unicorn import serializer
from tests.utils import dicts_equal


class SimpleTestModel(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "benchmarks_tests"


class SubclassSimpleTestModel(SimpleTestModel):
    subclass_name = models.CharField(max_length=10)

    class Meta:
        app_label = "benchmarks_tests"


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
        app_label = "benchmarks_tests"


class SubclassComplicatedTestModel(ComplicatedTestModel):
    subclass_name = models.CharField(max_length=10)

    class Meta:
        app_label = "benchmarks_tests"


def test_get_model_dict_simple_model(benchmark):
    model = SimpleTestModel(id=2, name="abc")
    expected = {"pk": 2, "name": "abc"}

    actual = benchmark(serializer._get_model_dict, model)

    assert dicts_equal(expected, actual)


def test_get_model_dict_complicated_model(benchmark):
    now_datetime = now()
    model = ComplicatedTestModel(
        id=2,
        name="abc",
        datetime=now_datetime,
        date=now_datetime.date(),
        time=now_datetime.time(),
    )
    expected = {
        "pk": 2,
        "name": "abc",
        "datetime": now_datetime.isoformat()[:-3],
        "date": str(now_datetime.date()),
        "time": str(now_datetime.time())[:-3],
        "uuid": str(model.uuid),
        "float_value": 0.583,  # will be converted from float to string by _fix_floats
        "decimal_value": 0.984,  # will be converted from float to string by _fix_floats
        "duration": "-1 19:00:00",
    }

    actual = benchmark(serializer._get_model_dict, model)

    assert dicts_equal(expected, actual)


def test_get_model_dict_subclass_simple_model(benchmark):
    model = SubclassSimpleTestModel(id=2, name="abc", subclass_name="def")
    expected = {"subclass_name": "def", "pk": 2, "name": "abc"}

    actual = benchmark(serializer._get_model_dict, model)

    assert dicts_equal(expected, actual)


def test_get_model_dict_subclass_complicated_model(benchmark):
    now_datetime = now()
    model = SubclassComplicatedTestModel(
        id=2,
        name="abc",
        subclass_name="def",
        datetime=now_datetime,
        date=now_datetime.date(),
        time=now_datetime.time(),
    )

    duration_str = DjangoJSONEncoder().encode(parse_duration(model.duration))[1:-1]
    expected = {
        "subclass_name": "def",
        "pk": 2,
        "name": "abc",
        "datetime": now_datetime.isoformat()[:-3],
        "date": str(now_datetime.date()),
        "float_value": "0.583",
        "decimal_value": "0.984",
        "uuid": str(model.uuid),
        "time": str(now_datetime.time())[:-3],
        "duration": duration_str,
    }

    actual = benchmark(serializer._get_model_dict, model)

    assert dicts_equal(expected, actual)
