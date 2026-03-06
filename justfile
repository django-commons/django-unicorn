import? 'adamghill.justfile'
import? '../dotfiles/just/justfile'

src := "src/django_unicorn"

# List commands
_default:
    just --list --unsorted --justfile {{ justfile() }} --list-heading $'Available commands:\n'

# Grab default `adamghill.justfile` from GitHub
fetch:
  curl https://raw.githubusercontent.com/adamghill/dotfiles/master/just/justfile > adamghill.justfile

# Run the dev server for the example project
runserver:
    -uv run --all-extras example/manage.py runserver 0:8080

# Install pre-commit hooks
install-pre-commit:
    uv run --all-extras pre-commit install

# Run pre-commit on all files
lint:
    uv run --all-extras pre-commit run --all-files

# Run the Python matrix test suite
test-python-matrix:
    act -W .github/workflows/python.yml -j test

# Run the JavaScript unit tests
test-js:
    npm run-script test

# Run both Python and JS tests
test-all:
    test-python-matrix
    test-js

# Build the JavaScript library
js-build:
    npm run build

# Install JS dependencies
js-install:
    npm install

# Run Python unit tests
test-python:
    -uv run --all-extras pytest -m 'not slow and not playwright'

# Run Python unit tests with benchmarks
test-python-benchmarks:
    -uv run --all-extras pytest tests/benchmarks/ --benchmark-autosave --benchmark-only

# Run Python unit tests with compared benchmarks
test-python-benchmarks-compare:
    -uv run --all-extras pytest tests/benchmarks/ --benchmark-only --benchmark-compare

# Run tests with coverage
test-python-coverage:
    -uv run --all-extras pytest --cov=django_unicorn

type:
    -uv run --all-extras ty check .

# Sphinx autobuild
docs-serve:
    -uv run --all-extras sphinx-autobuild -W docs/source site/docs

# Build documentation
docs-build:
    -uv run --all-extras sphinx-build -W docs/source site/docs

# Build everything (checks, JS, docs)
build:
    just type
    just test-python
    just js-install
    just js-build
    just docs-build

# Run e2e tests
test-e2e:
    uv run pytest tests/integration -m integration

# Run e2e tests with headed browser
test-e2e-headed:
    uv run pytest tests/integration -m integration --headed

# Run the dev server for the website
site-serve:
    just docs-build
    cd site && uv run --all-extras manage.py migrate && uv run --all-extras manage.py runserver 0:8081
