# Templates

Templates are normal Django HTML templates, so anything you could normally do in a Django template will still work, including template tags, filters, loops, if statements, etc.

```{warning}
`Unicorn` requires there to be one root element that contains the component HTML. Valid HTML and a wrapper element is required for the DOM diffing algorithm to work correctly, so `Unicorn` will try to log a warning message if they seem invalid.

One common issue is when a component is a table row (`tr`). Since `tr` elements can only contain `td` or `th` elements, any other element (like a `div`) will be "foster parented" out of the table structure by the browser. This will cause the DOM diffing to fail since the element structure is not what `Unicorn` expects.

For example, this is an **invalid** template:
:::{code} html
:force: true
<input unicorn:model="name"></input><br />
Name: {{ name }}
:::

This template is **valid**:
:::{code} html
:force: true
<div>
  <input unicorn:model="name"></input><br />
  Name: {{ name }}
</div>
:::

```

## Unicorn attributes

`Unicorn` element attributes usually start with `unicorn:`, however the shortcut `u:` is also supported. So, for example, `unicorn:model` could also be written as `u:model`.

`unicorn:bind` can also be used as a synonym for `unicorn:model` (and `u:bind` for `u:model`).

## Accessing nested fields

Fields in a `dictionary` or Django model can be accessed similarly to the Django template language with "dot notation".

```python
# hello_world.py
from django_unicorn.components import UnicornView
from book.models import Book

class HelloWorldView(UnicornView):
    book: Book
    book_ratings: dict[str[dict[str, str]]]

    def mount(self):
        book = Book.objects.get(title='American Gods')
        book_ratings = {'excellent': {'title': 'American Gods'}}
```

```html
<!-- hello-world.html -->
<div>
  <input unicorn:model="book.title" type="text" id="model" />
  <input
    unicorn:model="book_ratings.excellent.title"
    type="text"
    id="dictionary"
  />
</div>
```

```{note}
[Django models](django-models.md) has many more details about using Django models in `Unicorn`.
```

## Model modifiers

### Lazy

To prevent updates from happening on _every_ input, you can append a `lazy` modifier to the end of `unicorn:model`. That will only update the component when a `blur` event happens.

:::{code} html
:force: true

<!-- waits-for-blur.html -->
<div>
  <input unicorn:model.lazy="name" type="text" id="name" />
  Hello {{ name|title }}
</div>
:::

### Debounce

The `debounce` modifier configures how long to wait to fire an event. The time is always specified in milliseconds, for example: `unicorn:model.debounce-1000` would wait for 1000 milliseconds (1 second) before firing the message.

:::{code} html
:force: true

<!-- waits-1-second.html -->
<div>
  <input unicorn:model.debounce-1000="name" type="text" id="name" />
  Hello {{ name|title }}
</div>
:::

### Defer

The `defer` modifier will store and save model changes until the next action gets triggered. This is useful to prevent additional network requests until an action is triggered.

:::{code} html
:force: true

<!-- defer.html -->
<div>
  <input unicorn:model.defer="task" type="text" id="task" />
  <button unicorn:click="add">Add task</button>
  <ul>
    {% for task in tasks %}
    <li>{{ task }}</li>
    {% endfor %}
  </ul>
</div>
:::

### Chaining modifiers

`Lazy` and `debounce` modifiers can even be chained together.

:::{code} html
:force: true

<!-- waits-for-blur-and-then-5-seconds.html -->
<div>
  <input unicorn:model.lazy.debounce-5000="name" type="text" id="text" />
  Hello {{ name|title }}
</div>
:::

## Key

### Smooth updates

Setting a unique `id` on elements with `unicorn:model` will prevent changes to an input from being choppy when there are lots of updates in quick succession.

```html
<!-- choppy-updates.html -->
<input type="text" unicorn:model="name"></input>
```

```html
!-- smooth-updates.html -->
<input type="text" id="someFancyId" unicorn:model="name"></input>
```

The `unicorn:key` attribute can be used when multiple elements have the same `id`.

```html
<!-- missing-updates.html -->
<input type="text" id="someFancyId" unicorn:model="name"></input>
<input type="text" id="someFancyId" unicorn:model="name"></input>
```

```html
<!-- this-works.html -->
<input type="text" id="someFancyId" unicorn:model="name"></input>
<input type="text" id="someFancyId" unicorn:model="name" unicorn:key="someFancyKey"></input>
```

### DOM merging

To merge changes in the DOM, `Unicorn` uses, in order, `unicorn:id`, `unicorn:key`, or the element's `id` to intelligently update DOM elements.

## Lifecycle events

`Unicorn` provides events that fire when different parts of the lifecycle occur.

### updated

The `updated` event is fired after the AJAX call finishes and the component is merged with the newly rendered component template. The callback gets called with one argument, `component`.

```html
<!-- updated-event.html -->

<script type="application/javascript">
  window.addEventListener("DOMContentLoaded", (event) => {
    Unicorn.addEventListener("updated", (component) =>
      console.log("got updated", component)
    );
  });
</script>
```

## Ignore elements

Some JavaScript libraries will change the DOM (such as `Select2`) after the page renders. That can cause issues for `Unicorn` when trying to merge that DOM with what `Unicorn` _thinks_ the DOM should be. `unicorn:ignore` can be used to prevent `Unicorn` from morphing that element or its children.

```{note}
When the component is initially rendered, normal Django template functionality can be used.
```

```html
<!-- ignored-element.html -->
<div>
  <script src="jquery.min.js"></script>
  <link href="select2.min.css" rel="stylesheet" />
  <script src="select2.min.js"></script>

  <div unicorn:ignore>
    <select
      id="select2-example"
      onchange="Unicorn.call('ignored-element', 'select_state', this.value, this.selectedIndex);"
    >
      {% for state in states %}
      <option value="{{ state }}">{{ state }}</option>
      {% endfor %}
    </select>
  </div>

  <script>
    $(document).ready(function () {
      $("#select2-example").select2();
    });
  </script>
</div>
```

```python
# ignored_element.py
from django_unicorn.components import UnicornView

class JsView(UnicornView):
    states = (
        "Alabama",
        "Alaska",
        "Wisconsin",
        "Wyoming",
    )
    selected_state = ""

    def select_state(self, state_name, selected_idx):
        print("select_state state_name", state_name)
        print("select_state selected_idx", selected_idx)
        self.selected_state = state_name
```

## Context Processors and Component Re-rendering

Django context processors are executed when Django builds a `RequestContext`
during a full template render. Because django-unicorn performs partial,
component-level rendering, context processors are **not automatically re-run**
during component updates or when `force_render` is used.

### Understanding the Difference

In a traditional Django request/response cycle:

1. A request is received
2. A view prepares context data
3. Context processors run
4. The template is rendered

In django-unicorn, component updates work differently:

1. A request triggers a component action
2. The component state is updated
3. Only the component template is re-rendered
4. The DOM is patched with the updated HTML

Since django-unicorn does not rebuild the full Django template rendering
pipeline for component updates, context processors are not executed again.

### Force Render Behavior

Setting `force_render = True` on a component or parent component triggers a
template re-evaluation using the existing component state. It does **not**
recreate the full Django `RequestContext` and does not re-run context processors.

This is intentional and helps maintain performance by avoiding unnecessary
recomputation and database queries.

### Recommended Patterns

If you need values from settings or global context to persist across component
updates, consider one of the following approaches.

#### Store Values in Component State

Instead of relying on context processors, store values directly in the component:

```python
from django.conf import settings
from django_unicorn.components import UnicornView


class ExampleView(UnicornView):
    my_flag = settings.MY_FLAG
```

#### Use Lifecycle Hooks

If values must be refreshed periodically, update them during lifecycle events:

```python
def hydrate(self):
    self.my_flag = settings.MY_FLAG
```

#### Pass Values Explicitly

If using nested components, pass values through component parameters rather
than relying on template context.

### When to Use Context Processors

Context processors are still useful for:

* Initial page rendering
* Global template values shared across many pages
* Request-specific data (e.g., user, permissions)

However, they should not be relied upon for reactive UI state inside components.

### Performance Considerations

Context processors run during template rendering and may execute database
queries or other expensive operations. Automatically running them during every
component update would negatively impact performance and network efficiency.

For this reason, django-unicorn keeps component rendering separate from Django's
request-level context processing.

