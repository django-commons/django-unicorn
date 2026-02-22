# File Uploads

`Unicorn` supports file uploads through Django's standard form infrastructure. File inputs are detected automatically and transmitted as `multipart/form-data` instead of JSON, so Django's `request.FILES` and `FileField` validation work exactly as they do in normal Django views.

## Basic usage

### 1. Define a model and form

```python
# models.py
from django.db import models

class Document(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to="documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
```

```python
# forms.py
from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["description", "document"]
```

### 2. Create a component

Set `form_class` to your form and declare a component property that matches the file field name. Call `is_valid()` before saving so that Django validates the upload.

```python
# upload.py
from django_unicorn.components import UnicornView
from .forms import DocumentForm

class UploadView(UnicornView):
    form_class = DocumentForm

    document = None

    def upload(self):
        if self.is_valid():
            self.form.save()
            self.document = None  # clear after a successful save
```

### 3. Add the template

Wrap the file input in a `<form>` with `u:submit.prevent` pointing at your upload method.

```html
<!-- upload.html -->
<div>
  <form u:submit.prevent="upload">
    <input type="file" u:model="document" />
    <button type="submit">Upload</button>
  </form>
  <div u:loading>Uploading…</div>
</div>
```

When the user submits the form, `Unicorn` automatically:

1. Detects the `FileList` on the file input.
2. Packages the entire component payload as `multipart/form-data`.
3. Sends the file alongside the normal action queue.
4. Passes `request.FILES` to the form constructor for validation.

## Multiple files

Use the `multiple` attribute on the file input and a `MultipleFileField` (or equivalent) in your form.

```html
<!-- multi-upload.html -->
<div>
  <form u:submit.prevent="upload">
    <input type="file" u:model="photos" multiple />
    <button type="submit">Upload all</button>
  </form>
</div>
```

The individual files are appended to the request as `photos[0]`, `photos[1]`, etc. and resolved automatically before reaching your component method.

## Validation errors

Because `form_class` is used, validation errors surface the same way as with any other `Unicorn` form. See [Forms and Validation](validation.md) for all display options.

```html
<!-- upload-with-errors.html -->
<div>
  <form u:submit.prevent="upload">
    <input type="file" u:model="document" />
    <span class="error">{{ unicorn.errors.document.0.message }}</span>
    <button type="submit">Upload</button>
  </form>
</div>
```

## Deferred sync

By default a `syncInput` fires as soon as the user picks a file, then a second request fires when the form is submitted. Both requests carry the file, so the upload always succeeds.

If you want to avoid the first request you can use the `defer` modifier so the file is only sent once, together with the submit action:

```html
<!-- upload-defer.html -->
<div>
  <form u:submit.prevent="upload">
    <input type="file" u:model.defer="document" />
    <button type="submit">Upload</button>
  </form>
</div>
```

## Configuring media files

Django must be configured to store uploaded files. Add the following to `settings.py`:

```python
# settings.py
import os

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
```

And serve media files during development by updating your root `urls.py`:

```python
# urls.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # … your URL patterns …
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Security considerations

```{warning}
Always validate the file type, extension, and size on the server. Never trust client-supplied filenames or MIME types.
```

Django's `FileField` and `ImageField` provide built-in validation that you can extend:

```python
# forms.py
from django import forms
from django.core.exceptions import ValidationError

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]

class DocumentForm(forms.Form):
    document = forms.FileField()

    def clean_document(self):
        f = self.cleaned_data["document"]
        if f.size > MAX_UPLOAD_SIZE:
            raise ValidationError("File too large. Maximum size is 5 MB.")
        if f.content_type not in ALLOWED_TYPES:
            raise ValidationError("Unsupported file type.")
        return f
```

## State considerations

```{note}
HTML `<input type="file">` elements are read-only for security reasons — the browser never pre-fills a file input from JavaScript. This means `Unicorn` cannot restore a previously selected file after a re-render.
```

The recommended pattern is to clear the component's file property after a successful save (as shown in the examples above) and let the user re-select if they need to upload again.
