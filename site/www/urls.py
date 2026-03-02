from django.urls import include, path, re_path
from django.views.generic.base import RedirectView

from . import views

app_name = "www"

urlpatterns = [
    path("", views.index, name="index"),
    path("articles", views.articles, name="articles"),
    path("sponsors", views.sponsors, name="sponsors"),
    # screencasts
    re_path(
        r"^screencasts/(?P<name>[\w/-]+)$",
        views.screencasts,
        name="screencasts",
    ),
    path("screencasts", RedirectView.as_view(url="/screencasts/installation")),
    # examples
    re_path(
        r"^examples/(?P<name>[\w/-]+)$",
        views.examples,
        name="examples",
    ),
    path("examples", RedirectView.as_view(url="/examples/todo")),
    # old documentation path
    path("documentation", views.documentation, name="documentation"),
    re_path(
        r"^documentation/(?P<name>[\w/-]+)$",
        views.documentation,
        name="documentation",
    ),
    # sphinx-generated documentation
    re_path(r"docs/(?P<name>[\w-]+[^/])$", views.docs_redirect),
    path("docs/", include("django_sphinx_docs.urls")),
]
