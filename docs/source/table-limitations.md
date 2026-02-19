# Table Rendering Limitations

When using components inside HTML `<table>` elements, you must follow strict HTML structure rules. Failing to do so can cause reactivity issues that may look like state updates are not working.

This is not a bug in **Django Unicorn**, but a consequence of how browsers handle table DOM structure.

## Why This Happens

HTML tables are **structurally strict**. Browsers automatically correct invalid markup inside table elements.

Valid structure rules:
* `<table>` may contain `<thead>`, `<tbody>`, `<tfoot>`
* `<tbody>` may contain **only** `<tr>`
* `<tr>` may contain **only** `<td>` or `<th>`
* `<td>` may contain flow content (`<div>`, `<span>`, etc.)

If a component rendered inside a `<tbody>` outputs something like:

```html
<tr>
    <td>Row content</td>
</tr>

<div class="modal">...</div>
```

The `<div>` is **invalid inside `<tbody>`**, so the browser will automatically move it elsewhere in the DOM.

When this happens:
1. The browser modifies the DOM structure.
2. Unicorn's DOM diffing no longer matches the expected structure.
3. Reactive updates may silently fail or appear inconsistent.

This commonly appears as:
* A modal not showing reactively
* Conditional blocks not updating
* Child components not re-rendering properly

## Example of Problematic Pattern

Parent template:

```html
<tbody>
    {% for item in items %}
        {% unicorn 'row-component' item=item key=item.id %}
    {% endfor %}
</tbody>
```

Child component template:

```html
<tr>
    <td>{{ item.name }}</td>
    <td>
        <button unicorn:click="show_modal">Delete</button>
    </td>
</tr>

{% if modal_visible %}
    <div class="modal">Are you sure?</div>
{% endif %}
```

The `<div>` rendered after `<tr>` is invalid inside `<tbody>` and will be relocated by the browser.

## Why It Works With `<div>`

Replacing table tags with `<div>` works because `<div>` elements have no structural constraints. The browser does not auto-correct their placement, so Unicorn's DOM diffing remains stable.

## Recommended Solutions

### 1. Move Modals Outside the Table (Recommended)

Control modal state from the parent component and render the modal outside the `<table>`.

Child component:

```python
def request_delete(self):
    self.parent.confirm_delete(self.item.id)
```

Parent component:

```python
selected_id = None
show_modal = False

def confirm_delete(self, item_id):
    self.selected_id = item_id
    self.show_modal = True
```

Render the modal below the table:

```html
</table>

{% if show_modal %}
    <div class="modal">...</div>
{% endif %}
```

This keeps table markup valid and avoids DOM restructuring.

### 2. Render Modal Inside a Valid `<td>`

If you must render it within the table, wrap it inside a `<td colspan="...">`:

```html
{% if modal_visible %}
<tr>
    <td colspan="5">
        <div class="modal">...</div>
    </td>
</tr>
{% endif %}
```

This preserves valid table structure.

### 3. Ensure Single Valid Root Per Component

When rendering a component inside `<tbody>`, its root element must be a `<tr>`.
When rendering inside `<tr>`, its root must be `<td>` or `<th>`.

Avoid rendering sibling elements that break table hierarchy.

## Key Takeaway

If you experience reactivity issues inside tables:
* Verify your component outputs valid HTML table structure.
* Ensure no `<div>` or non-table elements are placed directly inside `<tbody>` or `<tr>`.
* Prefer handling overlays and modals outside the table.

Table elements are one of the strictest parts of HTML. Following valid structure rules ensures Unicorn's DOM diffing remains reliable and reactive updates function correctly.
