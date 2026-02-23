# Signals

`Unicorn` emits [Django signals](https://docs.djangoproject.com/en/stable/topics/signals/)
for each component lifecycle event.  You can connect receivers to observe component
activity without monkey-patching internal methods — useful for debug toolbars, logging,
analytics, or custom auditing.

## Connecting to a signal

```python
from django.dispatch import receiver
from django_unicorn.signals import component_rendered

@receiver(component_rendered)
def on_render(sender, component, html, **kwargs):
    print(f"{component.component_name} rendered {len(html)} bytes")
```

`sender` is always the component **class** (not an instance).  Every signal also
passes the live `component` instance as a keyword argument, plus any event-specific
kwargs documented below.

## Available signals

All signals are importable from `django_unicorn.signals`.

---

### `component_mounted`

Sent when a component is first created (mirrors the {meth}`mount` hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |

---

### `component_hydrated`

Sent when a component's data is hydrated (mirrors the {meth}`hydrate` hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |

---

### `component_completed`

Sent after all component actions have been executed (mirrors the {meth}`complete` hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |

---

### `component_rendered`

Sent after a component is rendered during an AJAX request (mirrors the {meth}`rendered`
hook).  Not fired for the initial server-side page render via the template tag.

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |
| `html` | `str` | The rendered HTML string |

---

### `component_parent_rendered`

Sent after a child component's parent is rendered (mirrors the {meth}`parent_rendered`
hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The **child** component instance |
| `html` | `str` | The rendered parent HTML string |

---

### `component_property_updating`

Sent before a component property is updated (mirrors the {meth}`updating` hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |
| `name` | `str` | Property name being updated |
| `value` | `Any` | The incoming new value |

---

### `component_property_updated`

Sent after a component property is updated (mirrors the {meth}`updated` hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |
| `name` | `str` | Property name that was updated |
| `value` | `Any` | The new value |

---

### `component_property_resolved`

Sent after a component property value is resolved (mirrors the {meth}`resolved` hook).
Unlike `component_property_updating` / `component_property_updated`, this signal fires
**only once** per sync cycle.

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |
| `name` | `str` | Property name that was resolved |
| `value` | `Any` | The resolved value |

---

### `component_method_calling`

Sent before a component method is called (mirrors the {meth}`calling` hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |
| `name` | `str` | Method name about to be called |
| `args` | `tuple` | Positional arguments |

---

### `component_method_called`

Sent after a component method is invoked — on both **success and failure**.
This signal includes the return value and exception info, making it more complete
than the `called()` hook.

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |
| `method_name` | `str` | Method name that was called |
| `args` | `tuple` | Positional arguments |
| `kwargs` | `dict` | Keyword arguments |
| `result` | `Any` | Return value of the method, or `None` on failure |
| `success` | `bool` | `True` if the method completed without raising an exception |
| `error` | `Exception \| None` | The exception raised, or `None` on success |

```python
from django.dispatch import receiver
from django_unicorn.signals import component_method_called

@receiver(component_method_called)
def log_method(sender, component, method_name, result, success, error, **kwargs):
    if success:
        print(f"[unicorn] {component.component_name}.{method_name}() → {result!r}")
    else:
        print(f"[unicorn] {component.component_name}.{method_name}() raised {error!r}")
```

---

### `component_pre_parsed`

Sent before the incoming request data is parsed and applied to the component
(mirrors the {meth}`pre_parse` hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |

---

### `component_post_parsed`

Sent after the incoming request data is parsed and applied to the component
(mirrors the {meth}`post_parse` hook).

| kwarg | type | description |
|-------|------|-------------|
| `component` | `UnicornView` | The component instance |

---

## Overriding hooks vs. connecting signals

The existing lifecycle hook methods (`mount`, `hydrate`, `rendered`, etc.) and signals
serve different purposes:

- **Hook methods** — override in your component subclass to run logic *inside* the
  component (e.g. `def mount(self): self.items = Items.objects.all()`).
- **Signals** — connect a receiver anywhere in your project to observe *any* component
  without modifying component code.

```{note}
If you override a hook method in your component class and do **not** call
``super()``, the corresponding signal will **not** fire because the default
implementation (which sends the signal) is bypassed.
```
