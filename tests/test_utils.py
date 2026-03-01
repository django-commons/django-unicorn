import pytest
from django.template.backends.django import Template

from django_unicorn.utils import (
    create_template,
    generate_checksum,
    get_method_arguments,
    is_non_string_sequence,
    parse_meta,
)
from tests.utils import sanitize_html


def test_generate_checksum_bytes(settings):
    settings.SECRET_KEY = "asdf"

    expected = "TfxFqcQL"
    actual = generate_checksum(b'{"name": "test"}')

    assert expected == actual


def test_generate_checksum_str(settings):
    settings.SECRET_KEY = "asdf"

    expected = "TfxFqcQL"
    actual = generate_checksum('{"name": "test"}')

    assert expected == actual


def test_generate_checksum_dict(settings):
    settings.SECRET_KEY = "asdf"

    # This is different than the above because `str(dict)` turns `{"name": "test"}` into `"{'name': 'test'}"`
    expected = "JaV4PeA6"
    actual = generate_checksum({"name": "test"})

    assert expected == actual


def test_generate_checksum_invalid(settings):
    settings.SECRET_KEY = "asdf"

    with pytest.raises(TypeError) as e:
        generate_checksum([])  # type: ignore

    assert e.exconly() == "TypeError: Invalid type: <class 'list'>"


def test_get_method_arguments():
    def test_func(input_str):
        return input_str

    expected = [
        "input_str",
    ]
    actual = get_method_arguments(test_func)
    assert actual == expected


def test_get_method_arguments_with_type_annotation():
    def test_func(input_str: str):
        return input_str

    expected = [
        "input_str",
    ]
    actual = get_method_arguments(test_func)
    assert actual == expected


def test_sanitize_html():
    expected = '{"id":"abcd123","name":"text-inputs","key":"asdf","data":{"name":"World","testing_thing":"Whatever \\u003C/script\\u003E \\u003Cscript\\u003Ealert(\'uh oh\')\\u003C/script\\u003E"},"calls":[],"hash":"hjkl"}'  # noqa: E501
    data = '{"id":"abcd123","name":"text-inputs","key":"asdf","data":{"name":"World","testing_thing":"Whatever </script> <script>alert(\'uh oh\')</script>"},"calls":[],"hash":"hjkl"}'  # noqa: E501
    actual = sanitize_html(data)
    assert actual == expected


def test_is_non_string_sequence_list():
    assert is_non_string_sequence(
        [
            "",
        ]
    )


def test_is_non_string_sequence_tuple():
    assert is_non_string_sequence(("",))


def test_is_non_string_sequence_set():
    assert is_non_string_sequence(
        {
            "",
        }
    )


def test_is_non_string_sequence_string():
    assert not is_non_string_sequence("")


def test_is_non_string_sequence_bytes():
    assert not is_non_string_sequence(b"")


def test_create_template_str():
    actual = create_template("<div>test string template</div>")

    assert actual
    assert isinstance(actual, Template)


def test_create_template_callable():
    def _get_template():
        return "<div>test callable template</div>"

    actual = create_template(_get_template)

    assert actual
    assert isinstance(actual, Template)


def test_parse_meta_one_part():
    actual = parse_meta("checksum")

    assert actual == ("checksum", "", "")


def test_parse_meta_two_parts():
    actual = parse_meta("checksum:hash")

    assert actual == ("checksum", "hash", "")


def test_parse_meta_three_parts():
    actual = parse_meta("checksum:hash:epoch")

    assert actual == ("checksum", "hash", "epoch")
