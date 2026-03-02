from django_unicorn.components import UnicornView

from django import forms
from django.utils import timezone


class ValidationForm(forms.Form):
    text = forms.CharField(min_length=3, max_length=10)
    now = forms.DateTimeField()
    number = forms.IntegerField()


class ValidationView(UnicornView):
    form_class = ValidationForm

    text = "hello"
    number = ""

    _now = None

    @property
    def now(self):
        self._now = timezone.now()
        return self._now

    @now.setter
    def now(self, val):
        self._now = val

    def set_text_no_validation(self):
        self.text = "no validation"

    def set_text_with_validation(self):
        self.text = "validation"
        self.validate()

    def set_number(self, number):
        self.number = number
