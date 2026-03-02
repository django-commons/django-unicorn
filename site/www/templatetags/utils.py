from django import template

from cache_memoize import cache_memoize


register = template.Library()


@cache_memoize(60 + 10)
@register.simple_tag
def code_include(file_name):
    file_contents = ""

    if file_name.endswith(".html"):
        file_contents = f"<!-- {file_name} -->\n"
    elif file_name.endswith(".py"):
        file_contents = f"# {file_name}\n"

    with open(file_name) as f:
        file_contents += f.read()

    return file_contents
