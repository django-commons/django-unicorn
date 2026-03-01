# Pagination

Pagination is a common pattern for displaying large datasets in manageable chunks. `Unicorn` works seamlessly with Django's built-in [Paginator](https://docs.djangoproject.com/en/stable/topics/pagination/) to create interactive, paginated views.

## Basic pagination

Here's a simple example of implementing pagination in a Unicorn component.

```python
# movies.py
from django_unicorn.components import UnicornView
from django.core.paginator import Paginator
from movies_app.models import Movie

class MoviesView(UnicornView):
    items_per_page = 10
    page_number = 1
    movies = []
    
    class Meta:
        javascript_exclude = (
            "paginator",
            "page",
            "page_range",
        )
    
    def mount(self):
        self.load_movies()
    
    def load_movies(self):
        # Get all movies
        qs = Movie.objects.all()
        
        # Create paginator
        paginator = Paginator(qs, self.items_per_page)
        page = paginator.get_page(self.page_number)
        
        # Store results
        self.movies = list(page.object_list)
        self.paginator = paginator
        self.page = page
        self.page_range = paginator.get_elided_page_range(
            number=self.page_number,
            on_each_side=2,
            on_ends=1
        )
    
    def go_to_page(self, page_num):
        self.page_number = page_num
        self.load_movies()
```

```html
<!-- movies.html -->
<div>
    <!-- Results -->
    <div>
        {% for movie in movies %}
        <div>
            <h3>{{ movie.title }}</h3>
            <p>{{ movie.description }}</p>
        </div>
        {% empty %}
        <p>No movies found.</p>
        {% endfor %}
    </div>
    
    <!-- Pagination controls -->
    {% if page.has_other_pages %}
    <nav>
        {% if page.has_previous %}
        <button unicorn:click="go_to_page({{ page.previous_page_number }})">
            Previous
        </button>
        {% endif %}
        
        {% for page_num in page_range %}
            {% if page_num == page.number %}
            <span class="current">{{ page_num }}</span>
            {% elif page_num == paginator.ELLIPSIS %}
            <span>...</span>
            {% else %}
            <button unicorn:click="go_to_page({{ page_num }})">
                {{ page_num }}
            </button>
            {% endif %}
        {% endfor %}
        
        {% if page.has_next %}
        <button unicorn:click="go_to_page({{ page.next_page_number }})">
            Next
        </button>
        {% endif %}
        
        <p>Page {{ page.number }} of {{ paginator.num_pages }}</p>
    </nav>
    {% endif %}
</div>
```

## Pagination with filtering

A common use case is combining pagination with search and filtering. When filters change, it's important to reset to page 1.

```python
# movies.py
from django_unicorn.components import UnicornView
from django.core.paginator import Paginator
from movies_app.models import Movie, Category

class MoviesView(UnicornView):
    # Pagination state
    items_per_page = 10
    page_number = 1
    
    # Search/filter state
    search_query = ""
    category = ""
    
    # Data
    movies = []
    categories = []
    
    class Meta:
        javascript_exclude = (
            "paginator",
            "page",
            "page_range",
        )
    
    def mount(self):
        self.categories = Category.objects.all()
        self.load_movies()
    
    def load_movies(self):
        # Build queryset with filters
        qs = Movie.objects.all()
        
        if self.search_query:
            qs = qs.filter(title__icontains=self.search_query)
        
        if self.category:
            qs = qs.filter(category_id=self.category)
        
        # Create paginator
        paginator = Paginator(qs, self.items_per_page)
        page = paginator.get_page(self.page_number)
        
        # Store results
        self.movies = list(page.object_list)
        self.paginator = paginator
        self.page = page
        self.page_range = paginator.get_elided_page_range(
            number=self.page_number,
            on_each_side=2,
            on_ends=1
        )
    
    def go_to_page(self, page_num):
        self.page_number = page_num
        self.load_movies()
    
    def updated_search_query(self, value):
        # Reset to page 1 when search changes
        self.page_number = 1
        self.load_movies()
    
    def updated_category(self, value):
        # Reset to page 1 when filter changes
        self.page_number = 1
        self.load_movies()
```

:::html
:force: true
<!-- movies.html -->
<div>
    <!-- Search and filters -->
    <div>
        <input 
            unicorn:model.debounce-500ms="search_query" 
            type="text" 
            placeholder="Search movies..."
        />
        
        <select unicorn:model="category">
            <option value="">All Categories</option>
            {% for cat in categories %}
            <option value="{{ cat.id }}">{{ cat.name }}</option>
            {% endfor %}
        </select>
    </div>
    
    <!-- Results -->
    <div>
        {% for movie in movies %}
        <div>
            <h3>{{ movie.title }}</h3>
            <p>{{ movie.description }}</p>
        </div>
        {% empty %}
        <p>No movies found.</p>
        {% endfor %}
    </div>
    
    <!-- Pagination controls -->
    {% if page.has_other_pages %}
    <nav>
        {% if page.has_previous %}
        <button unicorn:click="go_to_page({{ page.previous_page_number }})">
            Previous
        </button>
        {% endif %}
        
        {% for page_num in page_range %}
            {% if page_num == page.number %}
            <span class="current">{{ page_num }}</span>
            {% elif page_num == paginator.ELLIPSIS %}
            <span>...</span>
            {% else %}
            <button unicorn:click="go_to_page({{ page_num }})">
                {{ page_num }}
            </button>
            {% endif %}
        {% endfor %}
        
        {% if page.has_next %}
        <button unicorn:click="go_to_page({{ page.next_page_number }})">
            Next
        </button>
        {% endif %}
        
        <p>Page {{ page.number }} of {{ paginator.num_pages }}</p>
    </nav>
    {% endif %}
</div>
:::

## Common pitfalls

### Serialization errors

Django's `Paginator`, `Page`, and page range objects are not JSON serializable. If you try to use them as component fields without excluding them from JavaScript, you'll encounter errors like:

```
TypeError: Type is not JSON serializable: Page
```

**Solution**: Add these objects to `javascript_exclude` in your component's `Meta` class:

```python
class MoviesView(UnicornView):
    class Meta:
        javascript_exclude = (
            "paginator",
            "page",
            "page_range",
        )
```

This allows you to use these objects in your template while preventing them from being serialized to JavaScript.

### User model serialization

Similar issues can occur with Django's `User` model or other complex objects:

```python
from django.contrib.auth.models import User

class MyView(UnicornView):
    user: User = None
    
    class Meta:
        javascript_exclude = ("user",)
```

## Performance considerations

### Limit exposed data

For security and performance, only expose the data you need. Use `values()` or `only()` to limit the fields:

```python
def load_movies(self):
    # Only select needed fields
    qs = Movie.objects.all().values("id", "title", "description")
    
    paginator = Paginator(qs, self.items_per_page)
    page = paginator.get_page(self.page_number)
    
    self.movies = list(page.object_list)
    # ...
```

### Use elided page ranges

For large datasets, use `get_elided_page_range()` to avoid displaying hundreds of page numbers:

```python
# Shows: 1 ... 8 9 [10] 11 12 ... 100
self.page_range = paginator.get_elided_page_range(
    number=self.page_number,
    on_each_side=2,  # Show 2 pages on each side of current
    on_ends=1        # Show 1 page at each end
)
```

### Optimize queries

Use `select_related()` and `prefetch_related()` to avoid N+1 query problems:

```python
def load_movies(self):
    qs = Movie.objects.select_related('category').prefetch_related('actors')
    paginator = Paginator(qs, self.items_per_page)
    # ...
```

## Alternative approaches

### Using values() for simple lists

If you only need to display data (not edit it), using `values()` is more efficient:

```python
class MoviesView(UnicornView):
    movies = []
    
    def mount(self):
        qs = Movie.objects.all().values("id", "title", "year")
        paginator = Paginator(qs, 10)
        page = paginator.get_page(1)
        self.movies = list(page.object_list)
```

### Custom pagination UI

You can create custom pagination controls to match your design:

:::html
:force: true
<!-- Custom pagination with first/last buttons -->
<nav>
    <button 
        unicorn:click="go_to_page(1)" 
        {% if not page.has_previous %}disabled{% endif %}
    >
        First
    </button>
    
    <button 
        unicorn:click="go_to_page({{ page.previous_page_number }})" 
        {% if not page.has_previous %}disabled{% endif %}
    >
        &laquo; Prev
    </button>
    
    <span>Page {{ page.number }} of {{ paginator.num_pages }}</span>
    
    <button 
        unicorn:click="go_to_page({{ page.next_page_number }})" 
        {% if not page.has_next %}disabled{% endif %}
    >
        Next &raquo;
    </button>
    
    <button 
        unicorn:click="go_to_page({{ paginator.num_pages }})" 
        {% if not page.has_next %}disabled{% endif %}
    >
        Last
    </button>
</nav>
:::

## Community examples

For more complex pagination implementations, check out these community examples:

- [Basic pagination example](https://github.com/poiedk/django-unicorn-pagination-example) by @poiedk
- [Filtered pagination with MultipleObjectMixin](https://github.com/trolldbois/django-unicorn-filteredpaginatedview-example) by @trolldbois
