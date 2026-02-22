# Forms and Validation

`Unicorn` has two options for validation. It can either use the standard Django `forms` infrastructure for re-usability or `ValidationError` can be raised for simpler use-cases.

## Forms

`Unicorn` can use the Django `forms` infrastructure for validation. This means that a form could be re-used between any other Django views and a `Unicorn` component.

```{note}
There are many [built-in fields available for Django form fields](https://docs.djangoproject.com/en/stable/ref/forms/fields/#built-in-field-classes) which can be used to validate text inputs.
```

```python
# book_form.py
from django_unicorn.components import UnicornView
from django import forms

class BookForm(forms.Form):
    title = forms.CharField(max_length=100, required=True)
    publish_date = forms.DateField(required=True)

class BookView(UnicornView):
    title = ""
    publish_date = ""

    class Meta:
        form_class = BookForm
```

```html
<!-- book-form.html -->
<div>
  <input unicorn:model="title" type="text" id="title" /><br />
  <input unicorn:model="publish_date" type="text" id="publish-date" /><br />
  <button unicorn:click="$validate">Validate</button>
</div>
```

Because of the `Meta.form_class = BookForm` defined on the `UnicornView` above, `Unicorn` will automatically validate that the title has a value and is less than 100 characters. The `publish_date` will also be converted into a `datetime` from the string representation in the text input.

```{note}
Setting `form_class` directly as a class attribute also works and is supported for backwards compatibility.
```

### Validate the entire component

The magic action method `$validate` can be used to validate the whole component using the specified form.

```html
<!-- validate.html -->
<div>
  <input unicorn:model="publish_date" type="text" id="publish-date" /><br />
  <button unicorn:click="$validate">Validate</button>
</div>
```

The `validate` method can also be used inside of the component.

```python
# validate.py
from django_unicorn.components import UnicornView
from django import forms

class BookForm(forms.Form):
    title = forms.CharField(max_length=6, required=True)

class BookView(UnicornView):
    text = "hello"

    class Meta:
        form_class = BookForm

    def set_text(self):
        self.text = "hello world"
        self.validate()
```

The `is_valid` method can also be used inside of the component to check if a component is valid.

```python
# validate.py
from django_unicorn.components import UnicornView
from django import forms

class BookForm(forms.Form):
    title = forms.CharField(max_length=6, required=True)

class BookView(UnicornView):
    text = "hello"

    class Meta:
        form_class = BookForm

    def set_text(self):
        if self.is_valid():
            self.text = "hello world"
```

## Showing validation errors

There are a few ways to show the validation messages.

### Highlighting the invalid form

When a model form is invalid, a special `unicorn:error` attribute is added to the element. Depending on whether it is an `invalid` or `required` error code, the attribute will be `unicorn:error:invalid` or `unicorn:error:required`. The value of the attribute will be the validation message.

:::{code} html
:force: true

<!-- highlight-input-errors.html -->
<div>
  <style>
    [unicorn\:error\:invalid] {
      border: 1px solid red !important;
    }
    [unicorn\:error\:required] {
      border: 1px solid red !important;
    }
  </style>

<input
  unicorn:model="publish_date"
  type="text"
  id="publish-date"
  unicorn:error:invalid="Enter a valid date/time."
/><br />

</div>
:::

### Showing a specific error message

```html
<!-- show-error-message.html -->
<div>
  <input unicorn:model="publish_date" type="text" id="publish-date" /><br />
  <span class="error">{{ unicorn.errors.publish_date.0.message }}</span>
</div>
```

### Showing all the error messages

There is a `unicorn_errors` template tag that shows all errors for the component. It provides an example of how to display component errors in a more specific way if needed.

```html
<!-- show-all-error-messages.html -->
{% load unicorn %}

<div>
  {% unicorn_errors %}

  <input unicorn:model="publish_date" type="text" id="publish-date" /><br />
</div>
```

## ValidationError

If you do not want to create a form class or you want to specifically target a nested field you can raise a `ValidationError` inside of an action method. The `ValidationError` can be instantiated with a `dict` with the model name as the key and error message as the value. A `code` keyword argument must also be passed in. The typical error codes used are `required` or `invalid`.

```python
# book_validation_error.py
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django_unicorn.components import UnicornView

class BookView(UnicornView):
    book: Book

    def publish(self):
        if not self.book.title:
            raise ValidationError({"book.title": "Books must have a title"}, code="required")
        
        self.publish_date = now()
        self.book.save()
```

```html
<!-- book-validation-error.html -->
<div>
  <input unicorn:model="book.title" type="text" id="title" /><br />
  <button unicorn:click="publish">Publish Book</button>
</div>
```