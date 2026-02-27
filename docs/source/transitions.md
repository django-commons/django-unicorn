# Transitions

Transitions allow you to add CSS animations when elements are added to or removed from the DOM. This is particularly useful for modals, menus, and other UI elements that should fade or slide into place.

`Unicorn` follows the same transition pattern as Vue and Alpine.js, using six lifecycle stages defined by data attributes.

## Attributes

There are six attributes that can be used to define a transition:

- `u:transition:enter`: Classes applied during the entire entering phase.
- `u:transition:enter-start`: Classes applied at the start of the entering phase. Removed after one frame.
- `u:transition:enter-end`: Classes applied at the end of the entering phase.
- `u:transition:leave`: Classes applied during the entire leaving phase.
- `u:transition:leave-start`: Classes applied at the start of the leaving phase.
- `u:transition:leave-end`: Classes applied at the end of the leaving phase.

Alternatively, you can use the `unicorn:` prefix instead of `u:`.

## Example

The following example uses Tailwind CSS classes to create a fade and scale transition.

```html
<div>
    <button unicorn:click="toggle">Toggle</button>
    
    {% if show %}
    <div u:transition:enter="transition ease-out duration-300"
         u:transition:enter-start="opacity-0 transform scale-90"
         u:transition:enter-end="opacity-100 transform scale-100"
         u:transition:leave="transition ease-in duration-300"
         u:transition:leave-start="opacity-100 transform scale-100"
         u:transition:leave-end="opacity-0 transform scale-90"
         class="bg-gray-100 p-4 mt-2">
        Transitional Content
    </div>
    {% endif %}
</div>
```

## How it works

When an element with a transition is added to the DOM:
1. `u:transition:enter` and `u:transition:enter-start` classes are added.
2. After one frame, `u:transition:enter-start` is removed and `u:transition:enter-end` is added.
3. Once the transition finishes, `u:transition:enter` and `u:transition:enter-end` are removed.

When an element with a transition is removed from the DOM:
1. `u:transition:leave` and `u:transition:leave-start` classes are added.
2. After one frame, `u:transition:leave-start` is removed and `u:transition:leave-end` is added.
3. `Unicorn` waits for the transition to finish (`element.getAnimations()`) before finally removing the element from the DOM.
