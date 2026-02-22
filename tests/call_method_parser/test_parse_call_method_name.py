from django_unicorn.call_method_parser import parse_call_method_name


def setup_function():
    """Clears lru_cache before every test in the module."""
    parse_call_method_name.cache_clear()


def test_single_int_arg():
    expected = ("set_name", (1,), {})
    actual = parse_call_method_name("set_name(1)")

    assert actual == expected


def test_single_dict_arg():
    expected = ("set_name", ({"1": 2, "3": 4},), {})
    actual = parse_call_method_name('set_name({"1": 2, "3": 4})')

    assert actual == expected


def test_multiple_args():
    expected = ("set_name", (0, {"1": 2}), {})
    actual = parse_call_method_name('set_name(0, {"1": 2})')

    assert actual == expected


def test_multiple_args_2():
    expected = ("set_name", (1, 2), {})
    actual = parse_call_method_name("set_name(1, 2)")

    assert actual == expected


def test_var_with_curly_braces():
    expected = (
        "set_name",
        ("{}",),
        {},
    )
    actual = parse_call_method_name('set_name("{}")')

    assert actual == expected


def test_one_arg():
    expected = (
        "set_name",
        ("1",),
        {},
    )
    actual = parse_call_method_name('set_name("1")')

    assert actual == expected


def test_kwargs():
    expected = ("set_name", (), {"kwarg1": "wow"})
    actual = parse_call_method_name("set_name(kwarg1='wow')")

    assert actual == expected


def test_args_and_kwargs():
    expected = ("set_name", (8, 9), {"kwarg1": "wow"})
    actual = parse_call_method_name("set_name(8, 9, kwarg1='wow')")

    assert actual == expected


def test_special_method_without_parens():
    expected = ("$reset", (), {})
    actual = parse_call_method_name("$reset")

    assert actual == expected


def test_special_method_with_parens():
    expected = ("$reset", (), {})
    actual = parse_call_method_name("$reset()")

    assert actual == expected


def test_string_with_single_quotes():
    expected = ("set_name", ("It's a test",), {})
    actual = parse_call_method_name("set_name('It\\'s a test')")

    assert actual == expected


def test_string_with_double_quotes():
    expected = ("set_name", ('He said "hello"',), {})
    actual = parse_call_method_name("set_name('He said \"hello\"')")

    assert actual == expected


def test_string_with_backslashes():
    expected = ("set_name", ("C:\\Users\\test",), {})
    actual = parse_call_method_name("set_name('C:\\\\Users\\\\test')")

    assert actual == expected


def test_complex_chemical_name_issue_607():
    """Test for issue #607: string values with single quotes break function calls"""
    chemical_name = "Chloro(2-dicyclohexylphosphino-3,6-dimethoxy-2',4',6'-tri-i-propyl-1,1'-biphenyl)(2'-amino-1,1'-biphenyl-2-yl)palladium(II)"  # noqa: E501
    expected = ("set_new_catalyst", (chemical_name,), {})
    actual = parse_call_method_name(
        "set_new_catalyst('Chloro(2-dicyclohexylphosphino-3,6-dimethoxy-2\\',"
        "4\\',6\\'-tri-i-propyl-1,1\\'-biphenyl)(2\\'-amino-1,1\\'-biphenyl-2-yl)palladium(II)')"
    )

    assert actual == expected


def test_string_with_mixed_quotes_and_parentheses():
    expected = ("set_name", ("test(with 'quotes' and \"double\")",), {})
    actual = parse_call_method_name("set_name('test(with \\'quotes\\' and \"double\")')")

    assert actual == expected


def test_parent_method_call():
    expected = ("$parent.next", (), {})
    actual = parse_call_method_name("$parent.next()")

    assert actual == expected
