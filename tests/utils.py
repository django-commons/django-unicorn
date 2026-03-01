from pprint import pprint

from django.utils.html import _json_script_escapes  # type: ignore
from django.utils.safestring import SafeText, mark_safe


def dicts_equal(dictionary_one: dict, dictionary_two: dict) -> bool:
    """
    Return True if all keys and values are the same between two dictionaries.
    """

    is_valid = all(k in dictionary_two and dictionary_one[k] == dictionary_two[k] for k in dictionary_one) and all(
        k in dictionary_one and dictionary_one[k] == dictionary_two[k] for k in dictionary_two
    )

    if not is_valid:
        print("dictionary_one:")  # noqa: T201
        pprint(dictionary_one)  # noqa: T203
        print()  # noqa: T201
        print("dictionary_two:")  # noqa: T201
        pprint(dictionary_two)  # noqa: T203

    return is_valid


def sanitize_html(html: str) -> SafeText:
    """
    Escape all the HTML/XML special characters with their unicode escapes, so
    value is safe to be output in JSON.

    This is the same internals as `django.utils.html.json_script` except it takes a string
    instead of an object to avoid calling DjangoJSONEncoder.
    """

    html = html.translate(_json_script_escapes)
    return mark_safe(html)  # noqa: S308
