# JavaScript Integration

## Call JavaScript from View

To integrate with other JavaScript functions, view methods can call an arbitrary JavaScript function after it gets rendered.

```html
<!-- call-javascript.html -->
<div>
  <script>
    function hello(name) {
      alert("Hello, " + name);
    }
  </script>

  <input type="text" unicorn:model="name" />
  <button type="submit" unicorn:click="hello">Hello!</button>
</div>
```

```python
# call_javascript.py
from django_unicorn.components import UnicornView

class CallJavascriptView(UnicornView):
    name = ""

    def mount(self):
        self.call("hello", "world")

    def hello(self):
        self.call("hello", self.name)
```

## Remove a Component

Call `self.remove()` from any view method to remove the component's root element from the DOM. This is useful for list-item components (e.g. table rows or list items) that need to delete themselves without requiring a parent component to manage re-rendering.

```python
# todo_item.py
from django_unicorn.components import UnicornView

class TodoItemView(UnicornView):
    item_id: int = 0

    def delete(self):
        # perform any server-side cleanup here
        TodoItem.objects.filter(pk=self.item_id).delete()
        self.remove()
```

```html
<!-- todo-item.html -->
<li>
  {{ item_id }}
  <button unicorn:click="delete">Delete</button>
</li>
```

Calling `self.remove()` is shorthand for `self.call("Unicorn.deleteComponent", self.component_id)`. After the server responds, the component's root element is removed from the DOM and cleaned up from the internal component store.

## Call Method on Other Component

From a component, it is possible to call a method on another component. This is useful when you want to trigger a refresh or an update on another component.

```html
<!-- compare-list.html -->
<div>
  <!-- content -->
</div>
```

```python
# compare_list.py
from django_unicorn.components import UnicornView

class CompareListView(UnicornView):
    def reload_state(self):
        # do something
        pass
```

```html
<!-- source-checkbox.html -->
<div>
  <input type="checkbox" unicorn:model="is_checked" unicorn:change="toggle_check_state" />
</div>
```

```python
# source_checkbox.py
from django_unicorn.components import UnicornView

class SourceCheckboxView(UnicornView):
    is_checked = False

    def toggle_check_state(self):
        self.is_checked = not self.is_checked
        self.call("Unicorn.call", "compare-list", "reload_state")
```

The first argument to `call` is the name of the JavaScript function to call, which is `Unicorn.call`. The second argument is the name (or key) of the component to call. The third argument is the name of the method to call on that component.
```

## Trigger Model Update

Normally when a model element gets changed by a user it will trigger an event which `Unicorn` listens for (either `input` or `blur` depending on if it has a `lazy` modifier). However, when setting an element with JavaScript those events do not fire. `Unicorn.trigger()` provides a way to trigger that event from JavaScript manually.

The first argument to `trigger` is the component name. The second argument is the value for the element's `unicorn:key`.

```html
<!-- trigger-model.html -->
<input
  id="nameId"
  unicorn:key="nameKey"
  unicorn:model="name"
  value="initial value"
/>

<script>
  document.getElementById("nameId").value = "new value";
  Unicorn.trigger("hello_world", "nameKey");
</script>
```

## Dynamic Content

Unicorn automatically initializes components that are dynamically added to the page (e.g. via `htmx`, `fetch`, or `innerHTML`) using a `MutationObserver`.

If you need to manually check the DOM for new components, you can use `Unicorn.scan()`.

```javascript
// Scan the entire document
Unicorn.scan();

// Scan a specific element
const container = document.getElementById('container');
Unicorn.scan(container);
```

