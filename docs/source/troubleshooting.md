# Troubleshooting

## Disallowed MIME type error on Windows

Apparently Windows system-wide MIME type configuration sometimes won't load up JavaScript modules in certain browsers. The errors would be something like `Loading module from “http://127.0.0.1:8000/static/js/unicorn.js” was blocked because of a disallowed MIME type (“text/plain”)` or `Failed to load module script: The server responded with a non-JavaScript MIME type of "text/plain".`

One suggested solution is to add the following to the bottom of the settings file:

```python
# settings.py

if DEBUG:
    import mimetypes
    mimetypes.add_type("application/javascript", ".js", True)
```

See this [Windows MIME type detection pitfalls](https://www.taricorp.net/2020/windows-mime-pitfalls/) article, this [StackOverflow answer](https://stackoverflow.com/a/16355034), or [issue #201](https://github.com/adamghill/django-unicorn/issues/201) for more details.

## Missing CSRF token or 403 Forbidden errors

`Unicorn` uses CSRF to protect its endpoint from malicious actors. The two parts that are required for CSRF are `"django.middleware.csrf.CsrfViewMiddleware"` in `MIDDLEWARE` and `{% csrf_token %}` in the template that includes any `Unicorn` components.

```python
# settings.py

...
MIDDLEWARE = [
    ...
    "django.middleware.csrf.CsrfViewMiddleware",
    ...
]
```

```html
<!-- template.html -->
{% load unicorn %}

<html>
  <head>
    {% unicorn_scripts %}
  </head>
  <body>
    {% csrf_token %}

    {% unicorn 'hello-world' %}
  </body>
</html>
```

## Tables and invalid HTML

Browsers are very strict about table structure (e.g. `<tr>` can only be a direct child of `<tbody>`, `<thead>`, `<tfoot>`, or `<table>`, and `<div>` is not allowed as a direct child of `<tr>`). If you have a component that renders a table row, unexpected behavior can occur because the browser will "foster parent" invalid elements out of the table structure before `Unicorn` can seemingly react to them.

For example, this valid-looking component template will cause issues:

```html
<!-- invalid-table-row.html -->
<tr>
  <td>{{ name }}</td>
  {% if show_modal %}
    <div class="modal">...</div>
  {% endif %}
</tr>
```

The browser will move the `div` out of the `tr` (and likely out of the `table` entirely), so when `Unicorn` tries to update the component, it will be confused by the missing element.

To fix this, ensure that all content is inside a valid table element, like a `td`:

```html
<!-- valid-table-row.html -->
<tr>
  <td>{{ name }}</td>
  <td>
    {% if show_modal %}
      <div class="modal">...</div>
    {% endif %}
  </td>
</tr>
```

