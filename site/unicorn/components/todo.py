from typing import ClassVar

from django_unicorn.components import UnicornView


class TodoView(UnicornView):
    task = ""
    tasks: ClassVar[list] = []

    def add(self):
        self.tasks.append(self.task)
        self.task = ""
