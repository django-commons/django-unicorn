# Views

Views contain a class that inherits from `UnicornView` for the component's Python code.

To follow typical naming conventions, the view will convert the component's name to be more Pythonic. For example, if the component name is `hello-world`, the template file name will also be `hello-world.html`. However, the view file name will be `hello_world.py` and it will contain one class named `HelloWorldView`.

This allows `Unicorn` to connect the template and view using convention instead of configuration. Using the `startunicorn` management command is the easiest way to make sure that components are created correctly.

## Example view

```python
# hello_world.py
from django_unicorn.components import UnicornView

class HelloWorldView(UnicornView):
    pass
```

## Class variables

`Unicorn` will serialize/deserialize view class variables to JSON as needed for interactive parts of the component.

Automatically handled field types:
- `str`
- `int`
- `Decimal`
- `float`
- `list`
- `dictionary`
- [`Django Model`](django-models.md#model)
- [`Django QuerySet`](django-models.md#queryset)
- `dataclass`
- `Pydantic` models
- [Custom classes](views.md#custom-class)

### A word of caution about mutable class variables

Be careful when using a default mutable class variables, namely `list`, `dictionary`, and objects. As mentioned in [A Word About Names and Objects](https://docs.python.org/3.8/tutorial/classes.html#tut-object) defining a mutable default for a class variable can have subtle and unexpected consequences -- it _will_ cause component instances to share state which is usually not the intention.

```python
# sentence.py
from django_unicorn.components import UnicornView

# This will cause unexpected consequences
class SentenceView(UnicornView):
    words: list[str] = []  # all SentenceView instances will share a reference to one list in memory
    word_counts: dict[str, int] = {}  # all SentenceView instances will share a reference to one dictionary in memory

    def add_word(self, word: str):
        ...
```

The correct way to initialize a mutable object.

```python
# sentence.py
from django_unicorn.components import UnicornView

class SentenceView(UnicornView):
    words: list[str]  # not setting a default value is valid
    word_counts: dict[str, int] = None  # using None for the default is valid

    def mount(self):
        self.words = []  # initialize a new list every time a SentenceView is initialized and mounted
        self.word_counts = {}  # initialize a new dictionary every time a SentenceView is initialized and mounted

    def add_word(self, word: str):
        ...
```

`list`, `dictionaries`, and objects all run into this problem, so be sure to initialize mutable objects in the component's `mount` function.

### Class variable type hints

Type hints on fields help `Unicorn` ensure that the field will always have the appropriate type.

```python
# rating.py
from django_unicorn.components import UnicornView

class RatingView(UnicornView):
    rating: float = 0

    def calculate_percentage(self):
        assert isinstance(rating, float)
        print(self.rating / 100.0)
```

Without the `float` type hint on `rating`, Python will complain that `rating` is a `str`.

### Custom class

Custom classes need to define how they are serialized. If you have access to the object to serialize, you can define a `to_json` method on the object to return a dictionary that can be used to serialize. Inheriting from `unicorn.components.UnicornField` is a quick way to serialize a custom class, but it uses `self.__dict__` under the hood, so it is not doing anything particularly smart.

Another option is to set the `form_class` on the component and utilize [Django's built-in forms and widgets](validation.md) to handle how the class should be deserialized.

```python
# hello_world.py
from django_unicorn.components import UnicornView, UnicornField

class Author(UnicornField):
    def mount(self):
        self.name = 'Neil Gaiman'

    # Not needed because inherited from `UnicornField`
    # def to_json(self):
    #    return {'name': self.name}

    class HelloWorldView(UnicornView):
        author = Author()
```

```html
<!-- hello-world.html -->
<div>
  <input unicorn:model="author.name" type="text" id="author_name" />
</div>
```

```{danger}
Never put sensitive data into a public property because that information will publicly available in the HTML source code, unless explicitly prevented with [`javascript_exclude`](views.md#javascript_exclude).
```

## Class properties

### template_name

By default, the component name is used to determine what template should be used. For example, `hello_world.HelloWorldView` would by default use `unicorn/hello-world.html`. However, you can specify a particular template by setting `template_name` in the component.

```python
# hello_world.py
from django_unicorn.components import UnicornView

class HelloWorldView(UnicornView):
    template_name = "unicorn/hello-world.html"
```

### template_html

Template HTML can be defined inline on the component instead of using an external HTML file.

```python
# hello_world.py
from django_unicorn.components import UnicornView

class HelloWorldView(UnicornView):
    template_html = """<div>
    <div>
        Count: {{ count }}
    </div>

    <button unicorn:click="increment">+</button>
    <button unicorn:click="decrement">-</button>
</div>
"""

    ...
```

## Instance properties

### component_args

The arguments passed into the component.

```html
<!-- index.html -->
{% unicorn 'hello-arg' 'World' %}
```

```python
# hello_arg.py
from django_unicorn.components import UnicornView

class HelloArgView(UnicornView):
    def mount(self):
      assert self.component_args[0] == "World"
```

### component_kwargs

The keyword arguments passed into the component.

```html
<!-- index.html -->
{% unicorn 'hello-kwarg' hello='World' %}
```

```python
# hello_kwarg.py
from django_unicorn.components import UnicornView

class HelloKwargView(UnicornView):
    def mount(self):
      assert self.component_kwargs["hello"] == "World"
```

### request

The current `request`.

```python
# hello_world.py
from django_unicorn.components import UnicornView

class HelloWorldView(UnicornView):
    def mount(self):
        print("Initial request that rendered the component", self.request)

    def test(self):
        print("AJAX request that re-renders the component", self.request)
```

### force_render

Forces the component to render. This is not normally needed for the current component, but is sometimes needed when a child component needs a parent to re-render.

```python
# filter.py
from django_unicorn.components import UnicornView

class FilterView(UnicornView):
    search = ""

    def updated_search(self, query):
        self.parent.load_table()

        if query:
            self.parent.books = list(filter(lambda f: query.lower() in f.name.lower(), self.parent.books))

        # Forces the parent to re-render instead of just the current child component
        self.parent.force_render = True
```

## Custom methods

Defined component instance methods with no arguments (other than `self`) are available in the Django template context and can be called like a property.

```python
# states.py
from django_unicorn.components import UnicornView

class StateView(UnicornView):
    def all_states(self):
        return ["Alabama", "Alaska", "Arizona", ...]
```

```html
<!-- states.html -->
<div>
  <ul>
    {% for state in all_states %}
    <li>{{ state }}</li>
    {% endfor %}
  </ul>
</div>
{% endverbatim %}
```

:::{tip}
If the method is intensive and will be called multiple times, it can be cached with Django's <a href="https://docs.djangoproject.com/en/stable/ref/utils/#django.utils.functional.cached_property">`cached_property`</a> to prevent duplicate API requests or database queries. The method will only be executed once per component rendering.

```python
# states.py
from django.utils.functional import cached_property
from django_unicorn.components import UnicornView

class StateView(UnicornView):
    @cached_property
    def all_states(self):
        return ["Alabama", "Alaska", "Arizona", ...]
```

:::

## Instance methods

### mount()

Gets called when the component gets initialized or [reset](actions.md#reset).

```python
# hello_world.py
from django_unicorn.components import UnicornView

class HelloWorldView(UnicornView):
    name = "original"

    def mount(self):
        self.name = "mounted"
```

### hydrate()

Gets called when the component data gets set.

```python
# hello_world.py
from django_unicorn.components import UnicornView

class HelloWorldView(UnicornView):
    name = "original"

    def hydrate(self):
        self.name = "hydrated"
```

### updating(property_name, property_value)

Gets called before each property that will get set. This can be called multiple times in certain instances, e.g. during a debounce.

### updated(property_name, property_value)

Gets called after each property gets set. This can be called multiple times in certain instances, e.g. during a debounce.

### resolved(property_name, property_value)

Gets called after the specified property gets set. This will only get called once.

### updating\_{property_name}(property_value)

Gets called before the specified property gets set. This can be called multiple times in certain instances, e.g. during a debounce.

### updated\_{property_name}(property_value)

Gets called after the specified property gets set. This can be called multiple times in certain instances, e.g. during a debounce.

### resolved\_{property_name}(property_value)

Gets called after the specified property gets set. This will only get called once.

### calling(name, args)

Gets called before each method that gets called.

### called(name, args)

Gets called after each method gets called.

### complete()

Gets called after all methods have been called.

### rendered(html)

Gets called after the component has been rendered.

### parent_rendered(html)

Gets called after the component's parent has been rendered (if applicable).

## Meta

Classes that derive from `UnicornView` can include a `Meta` class that provides some advanced options for the component.

### exclude

By default, all public attributes of the component are included in the context of the Django template and available to JavaScript. One way to protect internal-only data is to prefix the attribute name with `_` to indicate it should stay private.

```python
# hello_state.py
from django_unicorn.components import UnicornView

class HelloStateView(UnicornView):
    _all_states = (
        "Alabama",
        "Alaska",
        ...
        "Wisconsin",
        "Wyoming",
    )
```

Another way to prevent that data from being available to the component template is to add it to the `Meta` class's `exclude` tuple.

```python
# hello_state.py
from django_unicorn.components import UnicornView

class HelloStateView(UnicornView):
    all_states = (
        "Alabama",
        "Alaska",
        ...
        "Wisconsin",
        "Wyoming",
    )

    class Meta:
        exclude = ("all_states", )
```

### javascript_exclude

To allow an attribute to be included in the the context to be used by a Django template, but not exposed to JavaScript, add it to the `Meta` class's `javascript_exclude` tuple.

```html
<!-- hello-state.html -->
<div>
  {% for state in all_states %}
  <div>{{ state }}</div>
  {% endfor %}
</div>
```

```python
# hello_state.py
from django_unicorn.components import UnicornView

class HelloStateView(UnicornView):
    all_states = (
        "Alabama",
        "Alaska",
        ...
        "Wisconsin",
        "Wyoming",
    )

    class Meta:
        javascript_exclude = ("all_states", )
```

### safe

By default, `unicorn` HTML encodes updated field values to prevent XSS attacks. You need to explicitly opt-in to allow a field to be returned without being encoded by adding it to the `Meta` class's `safe` tuple.

```html
<!-- safe-example.html -->
<div>
  <input unicorn:model="something_safe" />
  {{ something_safe }}
</div>
```

```python
# safe_example.py
from django_unicorn.components import UnicornView

class SafeExampleView(UnicornView):
    something_safe = ""

    class Meta:
        safe = ("something_safe", )
```

````{note}
A context variable can also be marked as `safe` in the template with the normal Django template filter.

```html
<!-- safe-example.html -->
<div>
  <input unicorn:model="something_safe" />
  {{ something_safe|safe }}
</div>
```
````

### login_not_required

By default, every component requires the user to be authenticated when Django's
[`LoginRequiredMiddleware`](https://docs.djangoproject.com/en/stable/ref/middleware/#django.contrib.auth.middleware.LoginRequiredMiddleware)
is active (Django 5.1+). Set `login_not_required = True` inside the `Meta` class to allow
unauthenticated users to interact with the component on public pages.

```python
# newsletter_signup.py
from django_unicorn.components import UnicornView

class NewsletterSignupView(UnicornView):
    email = ""

    class Meta:
        login_not_required = True

    def subscribe(self):
        ...
```

```{note}
`Meta.login_not_required` has no effect on Django versions older than 5.1 because
`LoginRequiredMiddleware` was not available before that release.
```

```{warning}
Only set `Meta.login_not_required = True` on components whose actions are safe to
execute without authentication. Any sensitive operation (e.g. accessing private
data, modifying records) should still verify `self.request.user.is_authenticated`
inside the relevant component methods.
```

## Pickling and Caching

Components are pickled and cached for the duration of the AJAX request. This means that any instance variable on the component must be pickleable.

```{warning}
Do not store unpickleable objects (e.g. generators) on the component instance.
```

If you need to use an unpickleable object, either convert it to a pickleable type (e.g. convert a generator to a list) or re-initialize it within the method that needs it without storing it on `self`.


