from datetime import datetime, timezone

from django import forms
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.forms import ValidationError
from django.shortcuts import redirect

from django_unicorn.components import (
    HashUpdate,
    LocationUpdate,
    PollUpdate,
    UnicornView,
)
from example.books.models import Book
from example.coffee.models import Flavor


class FakeComponent(UnicornView):
    template_name = "templates/test_component.html"
    dictionary = {"name": "test"}  # noqa: RUF012
    method_count = 0
    check = False
    nested = {"check": False, "another": {"bool": False}}  # noqa: RUF012
    method_arg = ""

    def test_method(self):
        self.method_count += 1

    def test_method_args(self, count):
        self.method_count = count

    def test_method_string_arg(self, param):
        self.method_count += 1
        self.method_arg = param

    def test_method_kwargs(self, count=-1):
        self.method_count = count

    def test_redirect(self):
        return redirect("/something-here")

    def test_refresh_redirect(self):
        return LocationUpdate(redirect("/something-here"), title="new title")

    def test_hash_update(self):
        return HashUpdate("#test=1")

    def test_return_value(self):
        return "booya"

    def test_poll_update(self):
        return PollUpdate(timing=1000, disable=True, method="new_method")

    def test_validation_error(self):
        raise ValidationError({"check": "Check is required"}, code="required")

    def test_validation_error_no_code(self):
        raise ValidationError({"check": "Check is required"})

    def test_validation_error_string(self):
        raise ValidationError("Check is required", code="required")

    def test_validation_error_string_no_code(self):
        raise ValidationError("Check is required")

    def test_validation_error_list(self):
        raise ValidationError([ValidationError({"check": "Check is required"})], code="required")

    def test_validation_error_list_no_code(self):
        raise ValidationError([ValidationError({"check": "Check is required"})])


class FakeModelForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ("title", "date_published", "type")


class FakeModelFormComponent(UnicornView):
    template_name = "templates/test_component.html"
    form_class = FakeModelForm

    title = None
    date_published = None
    type = None


class FakeModelComponent(UnicornView):
    template_name = "templates/test_component.html"
    flavors = Flavor.objects.all()

    def hydrate(self):
        self.flavors = Flavor.objects.all()


class FakeValidationForm(forms.Form):
    text = forms.CharField(min_length=3, max_length=10)
    date_time = forms.DateTimeField()
    number = forms.IntegerField()
    permanent = forms.BooleanField()


class FakeValidationComponent(UnicornView):
    template_name = "templates/test_component.html"
    form_class = FakeValidationForm

    text = "hello"
    number = ""
    date_time = datetime(2020, 9, 13, 17, 45, 14, tzinfo=timezone.utc)
    permanent = True

    def set_text_no_validation(self):
        self.text = "no validation"

    def set_text_with_validation(self):
        self.text = "validation 33"
        self.validate()

    def set_number(self, number):
        self.number = number


class FakeAuthenticationComponent(UnicornView):
    template_name = "templates/test_component.html"
    form_class = AuthenticationForm

    username = ""
    password = ""


class FakeComponentWithDictionary(UnicornView):
    template_name = "templates/test_component.html"
    dictionary: dict | None = None

    def test_method(self):
        pass


class FakeComponentWithMessage(UnicornView):
    template_name = "templates/test_component_with_message.html"

    def test_message(self):
        assert self.request, "Expect a request in action methods"
        messages.success(self.request, "test success")

    def test_redirect_with_message(self):
        assert self.request, "Expect a request in action methods"
        messages.success(self.request, "test success")
        return redirect("/something-here")


class FakeComponentWithError(UnicornView):
    template_name = "templates/test_component.html"

    def mount(self):
        print(self.not_a_valid_attribute)  # type: ignore # noqa: T201


count_updating = 0
count_updated = 0


class FakeComponentWithUpdateMethods(UnicornView):
    template_name = "templates/test_component.html"

    count = 0

    def updating_count(self, _):
        global count_updating  # noqa: PLW0603
        count_updating += 1

        if count_updating >= 2:
            raise Exception("updating_count called more than once")

        assert count_updating == 1

    def updated_count(self, _):
        global count_updated  # noqa: PLW0603
        count_updated += 1

        if count_updated >= 2:
            raise Exception("count_updated called more than once")

        assert count_updated == 1


count_resolved = 0


class FakeComponentWithResolveMethods(UnicornView):
    template_name = "templates/test_component.html"

    count = 0

    def resolved_count(self, _):
        global count_resolved  # noqa: PLW0603
        count_resolved += 1

        assert count_resolved == 1, "count_resolved called more than once"


class BugComponent(UnicornView):
    template_name = "templates/test_component.html"
    flavor: str = "initial"

    def set_flavor(self, value: str = ""):
        self.flavor = value


class FakeBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ("title", "date_published")


class FakeFormClassesComponent(UnicornView):
    """Component that uses ``form_classes`` to validate an object field."""

    template_name = "templates/test_component.html"
    form_classes = {"book": FakeBookForm}  # noqa: RUF012

    book: Book = None  # type: ignore[assignment]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.book is None:
            self.book = Book()

    def save(self):
        self.validate()

