from nonexistent_package_xyz_abc import SomeClass  # noqa: F401  # type: ignore[import]

from django_unicorn.components import UnicornView


class FakeComponentWithBrokenImport(UnicornView):
    template_name = "templates/test_component.html"
