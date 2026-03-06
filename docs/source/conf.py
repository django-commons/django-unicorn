from importlib import metadata

# -- Project information -----------------------------------------------------

project = "Unicorn"
copyright = "2023-2026, Adam Hill"  # noqa: A001
author = "Adam Hill"

try:
    version = metadata.version("django-unicorn")
except ImportError:
    # If the package is not installed, fallback to a placeholder
    version = "dev"

release = version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "rst2pdf.pdfbuilder",
    "autoapi.extension",
    "sphinxext.opengraph",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 3

myst_enable_extensions = ["colon_fence"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_title = "Unicorn"
html_css_files = [
    "styles/unicorn.css",
]
html_theme_options = {
    "sidebar_hide_name": True,
    "announcement": """
<script async defer data-domain="django-unicorn.com" src="https://plausible.io/js/plausible.outbound-links.js"></script>
<script>window.plausible = window.plausible || function() { (window.plausible.q = window.plausible.q || []).push(arguments) }</script>
<script async defer src="https://buttons.github.io/buttons.js"></script>
<script async src="https://media.ethicalads.io/media/client/ethicalads.min.js"></script>

<nav class="navbar" role="navigation" aria-label="main navigation" style="background-color: #fafafa;">
    <div class="navbar-brand">
        <a class="navbar-item" href="/" style="margin-top: 6px;">
            <strong>🦄 ✨</strong>
        </a>

        <a role="button" class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="navMenu">
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
        </a>
    </div>

    <div class="navbar-menu" id="navMenu">
        <div class="navbar-end">
            <a class="navbar-item" href="/docs/">
                <img src="/static/img/book.svg" style="max-height: 1.5em; margin-top: 6px; vertical-align: bottom;" />&nbsp;Docs
            </a>
            <a class="navbar-item" href="/screencasts/installation">
                <img src="/static/img/video.svg" style="max-height: 1.5em; margin-top: 6px; vertical-align: bottom;" />&nbsp;Screencasts
            </a>
            <a class="navbar-item" href="/examples">
                <img src="/static/img/tool.svg" style="max-height: 1.5em; margin-top: 6px; vertical-align: bottom;" />&nbsp;Examples
            </a>
            <a class="navbar-item" href="/sponsors">
                <img src="/static/img/heart.svg" style="max-height: 1.5em; margin-top: 6px; vertical-align: bottom;" />&nbsp;Sponsors
            </a>
            <a class="navbar-item" href="https://fosstodon.org/@unicorn">
                <img src="/static/img/mastodon.svg" style="max-height: 1.5em; margin-top: 6px; vertical-align: bottom;" />&nbsp;&nbsp;
            </a>
            <div style="margin-top: .8rem; margin-right: .8rem;">
                <a class="github-button" href="https://github.com/adamghill/django-unicorn/discussions" data-size="large" aria-label="Discuss adamghill/django-unicorn on GitHub">Discuss</a>
            </div>
            <div style="margin-top: .8rem; margin-right: .8rem;">
                <a class="navbar-item github-button" href="https://github.com/adamghill/django-unicorn" data-icon="octicon-star" data-size="large" data-show-count="true" aria-label="Star adamghill/django-unicorn on GitHub">Star</a>
            </div>
            <div style="margin-top: .8rem; margin-right: .8rem;">
                <a class="github-button" href="https://github.com/sponsors/adamghill" data-icon="octicon-heart" data-size="large" aria-label="Sponsor @adamghill on GitHub">Sponsor</a>
            </div>
        </div>
    </div>
</nav>

<div data-ea-publisher="django-unicorncom" data-ea-type="image" data-ea-style="stickybox" id="django-unicorn"
    style="float: right; z-index: 100;">
</div>
""",
}

myst_heading_anchors = 3
myst_enable_extensions = ["linkify", "colon_fence"]

pdf_documents = [
    ("index", "unicorn-latest", "Unicorn", "Adam Hill"),
]

autoapi_dirs = [
    "../../src/django_unicorn",
]
autoapi_root = "api"
autoapi_add_toctree_entry = False
autoapi_generate_api_docs = True
# autoapi_keep_files = True  # useful for debugging generated errors
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
]
autoapi_type = "python"
autodoc_typehints = "signature"
suppress_warnings = ["autoapi.python_import_resolution", "ref.python"]


def skip_member(app, what, name, obj, skip, options):  # noqa: ARG001
    if what == "data" and name.endswith(".logger"):
        skip = True
    elif "startunicorn" in name:
        skip = True
    elif name == "django_unicorn.views.message" and what == "function":
        skip = True

    return skip


def setup(sphinx):
    sphinx.connect("autoapi-skip-member", skip_member)


ogp_site_url = "https://www.django-unicorn.com/"
