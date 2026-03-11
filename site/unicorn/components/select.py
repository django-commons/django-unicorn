from typing import ClassVar

from django_unicorn.components import UnicornView


class SelectView(UnicornView):
    selected_fruit = ""
    fruits: ClassVar[list] = [
        "Apple",
        "Grape",
        "Banana",
    ]

    class Meta:
        javascript_exclude = ("fruits",)
