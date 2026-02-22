import ast
import logging
from collections.abc import Mapping
from functools import lru_cache
from types import MappingProxyType
from typing import Any

from django_unicorn.typer import CASTERS

logger = logging.getLogger(__name__)


class InvalidKwargError(Exception):
    pass


def _get_expr_string(expr: ast.expr) -> str:
    """
    Builds a string based on traversing `ast.Attribute` and `ast.Name` expressions.

    Args:
        expr: Expression node of the the AST tree. Only handles `ast.Attribute` and `ast.Name` expressions.

    Returns:
        String based on the expression nodes.
    """

    current_expr = expr
    expr_str = ""

    while current_expr:
        if isinstance(current_expr, ast.Name):
            if not expr_str:
                expr_str = current_expr.id
            else:
                expr_str = f"{current_expr.id}.{expr_str}"

            break
        elif isinstance(current_expr, ast.Attribute):
            if not expr_str:
                expr_str = current_expr.attr
            else:
                expr_str = f"{current_expr.attr}.{expr_str}"

            current_expr = current_expr.value
        else:
            break

    return expr_str


def _cast_value(value):
    """
    Try to cast a value based on a list of casters.
    """

    for caster in CASTERS.values():
        try:
            casted_value = caster(value)

            if casted_value:
                value = casted_value
                break
        except ValueError:
            pass

    return value


@lru_cache(maxsize=128, typed=True)
def eval_value(value):
    """
    Uses `ast.literal_eval` to parse strings into an appropriate Python primitive.

    Also returns an appropriate object for strings that look like they represent datetime,
    date, time, duration, or UUID.
    """

    try:
        value = ast.literal_eval(value)
    except SyntaxError:
        value = _cast_value(value)

    return value


@lru_cache(maxsize=128, typed=True)
def parse_kwarg(kwarg: str, *, raise_if_unparseable=False) -> dict[str, Any]:
    """
    Parses a potential kwarg as a string into a dictionary.

    Example:
        `parse_kwarg("test='1'")` == `{"test": "1"}`

    Args:
        kwarg: Potential kwarg as a string. e.g. "test='1'".
        raise_if_unparseable: Raise an error if the `kwarg` cannot be parsed. Defaults to `False`.

    Returns:
        Dictionary of key-value pairs.
    """

    try:
        tree = ast.parse(kwarg, "eval")

        if tree.body and isinstance(tree.body[0], ast.Assign):
            assign = tree.body[0]

            try:
                target = assign.targets[0]
                key = _get_expr_string(target)

                return {key: eval_value(assign.value)}
            except ValueError:
                if raise_if_unparseable:
                    raise

                # The value can be a template variable that will get set from the
                # context when the templatetag is rendered, so just return the expr
                # as a string.
                value = _get_expr_string(assign.value)
                return {key: value}  # type: ignore
        else:
            raise InvalidKwargError(f"'{kwarg}' is invalid")
    except SyntaxError as e:
        raise InvalidKwargError(f"'{kwarg}' could not be parsed") from e


@lru_cache(maxsize=128, typed=True)
def parse_call_method_name(
    call_method_name: str,
) -> tuple[str, tuple[Any, ...], Mapping[str, Any]]:
    """
    Parses the method name from the request payload into a set of parameters to pass to
    a method.

    Args:
        param call_method_name: String representation of a method name with parameters,
            e.g. "set_name('Bob')"

    Returns:
        Tuple of method_name, a list of arguments and a dict of keyword arguments
    """

    is_special_method = False
    args: list[Any] = []
    kwargs: dict[str, Any] = {}
    method_name = call_method_name

    # Deal with special methods that start with a "$"
    if method_name.startswith("$"):
        is_special_method = True
        method_name = method_name[1:]

    tree = ast.parse(method_name, "eval")
    statement = tree.body[0].value  # type: ignore

    if tree.body and isinstance(statement, ast.Call):
        call = tree.body[0].value  # type: ignore
        method_name = _get_expr_string(call.func)
        args = [eval_value(arg) for arg in call.args]
        kwargs = {kw.arg: eval_value(kw.value) for kw in call.keywords}

    # Add "$" back to special functions
    if is_special_method:
        method_name = f"${method_name}"

    # conversion to immutable types - tuple and MappingProxyType
    return method_name, tuple(args), MappingProxyType(kwargs)
