from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect
from fbv.decorators import render_html


@cache_page(60 * 15)
@csrf_protect
@render_html("www/index.html")
def index(request):
    return {}


@cache_page(60 * 15)
@render_html("www/articles.html")
def articles(request):
    return {}


@cache_page(60 * 15)
def screencasts(request, name="installation"):
    template_name = f"www/screencasts/{name}.html"
    return render(request, template_name)


def examples(request, name="todo"):
    template_name = f"www/examples/{name}.html"
    return render(request, template_name)


@cache_page(60 * 15)
@render_html("www/sponsors.html")
def sponsors(request):
    return {}


@csrf_protect
def documentation(request, name="introduction"):
    return redirect("/docs/")


def docs_redirect(request, name):
    return redirect(name + "/")
