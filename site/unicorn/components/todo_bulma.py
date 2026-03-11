from typing import ClassVar

from django import forms

from django_unicorn.components import UnicornView


class TodoForm(forms.Form):
    task = forms.CharField(min_length=2, max_length=20, required=True)


class TodoBulmaView(UnicornView):
    form_class = TodoForm

    task = ""
    tasks: ClassVar[list] = []

    def add(self):
        if self.is_valid():
            self.tasks.append(self.task)
            self.task = ""
