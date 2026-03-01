# Changelog

## 0.65.0

- Properly escape single quotes in Unicorn.call() arguments [#773](https://github.com/adamghill/django-unicorn/pull/773) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).
- Automatically initialize components via MutationObserver [#760](https://github.com/adamghill/django-unicorn/pull/760) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).
- Support HTTP redirect from mount() [#767](https://github.com/adamghill/django-unicorn/pull/767) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).
- Fix: `IndexError` when using a custom setter method with $event.target.value by [#761](https://github.com/adamghill/django-unicorn/pull/761) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).
- Fix: correct debounce behavior with delay [#764](https://github.com/adamghill/django-unicorn/pull/764) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).
- Fix: prevent poll from overwriting many-to-many fields [#769](https://github.com/adamghill/django-unicorn/pull/769) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).


## 0.64.0

- Switch to `lxml` instead of `beautifulsoup` for improved HTML parsing performance.
- Add `unicorn:bind` as a synonym for `unicorn:model`.
- Add [`unicorn:loading.delay`](loading-states.md#delay) modifier to prevent loading state from showing for fast actions [#754](https://github.com/adamghill/django-unicorn/pull/754) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).
- Add [action modifier to disable](actions.md#disable) an element while an action is in-flight [#755](https://github.com/adamghill/django-unicorn/pull/755) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).
- Add `Component` base class as an alias for `UnicornView`.
- Fix: Set request on restored component [#753](https://github.com/adamghill/django-unicorn/pull/753).
- Fix: Coerce component key types to handle integer/string comparisons.
- Fix: Handle pickle error for nested components.
- Fix: Support inherited type hints in `get_type_hints` by [#759](https://github.com/adamghill/django-unicorn/pull/759) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).
- Fix: "Multiple root elements" error with `unicorn:view` and `unicorn:poll` [#668](https://github.com/adamghill/django-unicorn/pull/668) by [JohananOppongAmoateng](https://github.com/JohananOppongAmoateng).

## 0.63.0

- Fix: Child components would cause RecursionError when pickling by [igadmile](https://github.com/igadmile) in [#672](https://github.com/adamghill/django-unicorn/pull/672).

## 0.62.0

- Security fix: for CVE-2025-24370 for a class pollution vulnerability (reported by [superboy-zjc](https://github.com/superboy-zjc)).

**Breaking changes**

- Remove support for Python 3.8 and 3.9 because Django 5.0 has dropped support.

## 0.61.0

- Add [`template_html`](views.md#template_html) to specify inline template HTML on the component.
- Add `resolved` method which only fires once even when there are multiple actions, e.g. during a debounce.

## 0.60.0

- Silence warnings about multiple root elements for direct views.
- Handle `force_render` in nested children for direct views [#663](https://github.com/adamghill/django-unicorn/pull/663).
- Handle error when manually refreshing direct views.
- Handle component field type annotations for `dataclasses` and `Pydantic` `BaseModel` [#649](https://github.com/adamghill/django-unicorn/pull/649) by [siliconcow](https://github.com/siliconcow).
- Update `startunicorn` command to prevent spamming users and handle folder creation for nested components [#642](https://github.com/adamghill/django-unicorn/pull/642) by [felipmartins](https://github.com/felipmartins).

**Breaking changes**

- Unparseable `kwarg` argument passed into a component will be considered `None` instead of being converted to a string.

```html
<!-- If `abcde` is not a variable in the template context, it will get set to `name` as `None` whereas before it would get set as 'abcde' -->
{% unicorn 'hello' name=abcde %}
```

## 0.59.0

- Update logic to find components [#655](https://github.com/adamghill/django-unicorn/pull/655) by [jacksund](https://github.com/jacksund).
- Add fallback location to look for components.

## 0.58.1

- Try to prevent type hints from crashing components. [#639](https://github.com/adamghill/django-unicorn/issues/639)

## 0.58.0

This release could not have been made possible without the generous support of https://github.com/winrid and https://github.com/om-proptech. Thank you for sponsoring me and believing in `django-unicorn`! It also includes critical improvements to nested components from https://github.com/imankulov.

- Handle a list of `ValidationError` or just a string instead of requiring a the `dict` version.
- Better support for type annotations for component fields.
- Improved nested component support by [imankulov](https://github.com/imankulov).
- Add [`force_render`](views.md#force_render) and [`$parent`](actions.md#parent).

**Breaking changes**

Child components will not *by default* render the parent component anymore. If this is required for your child component, specify `self.parent.force_render = True` in any action that requires the parent to re-render. This change will reduce network bandwidth and isolates the amount of re-rendering required for nested components.

## 0.57.1

- Fix: Correctly serialize forms that have a a field with a Select widget.

## 0.57.0

- Warn if there is a missing root element.
- Use `unicorn:id` to merge elements with `morphdom`.

## 0.56.1

- Handle Alpine.js being loaded with defer.

## 0.56.0

- Add support for using both Alpine.js and `Unicorn` together in a component ([#597](https://github.com/adamghill/django-unicorn/pull/597) by [imankulov](https://github.com/imankulov)).
- Do not send a 304 if the child has a parent ([#595](https://github.com/adamghill/django-unicorn/pull/595)).
- Prevent sending the child DOM if there is a parent to reduce network payload size.
- More verbose error message when a component can not be loaded ([#453](https://github.com/adamghill/django-unicorn/pull/453) by [nerdoc](https://github.com/nerdoc)).

## 0.55.0

- Support `List`/`list` type annotations for component actions and fields ([#582](https://github.com/adamghill/django-unicorn/pull/582)).
- Fix: calling a method in a parent will have the request available ([#583]https://github.com/adamghill/django-unicorn/pull/583).

**Breaking changes**

- Dropped official support for Python 3.7 because its [end of life was June 27, 2023](https://endoflife.date/python).
- Dropped official support for Django 2.2 because its [end of life was April 1, 2022](https://endoflife.date/django).

## 0.54.0

- Coerce type annotated arguments in an action method to the specified type ([#571](https://github.com/adamghill/django-unicorn/pull/571)).
- Fix: Dictionary fields would sometimes create checksum errors ([#572](https://github.com/adamghill/django-unicorn/pull/572)).

## 0.53.0

- Support passing arguments into a component ([#560](https://github.com/adamghill/django-unicorn/pull/560)).
- Fix the handling of `None` for select elements. ([#563](https://github.com/adamghill/django-unicorn/pull/563)).
- Better handling of `AuthenticationForm` when used in `Component.form_class` ([#552](https://github.com/adamghill/django-unicorn/pull/552)) by [lassebomh](https://github.com/lassebomh).

## v0.52.0

- Use `CSRF_COOKIE_NAME` Django setting ([#545](https://github.com/adamghill/django-unicorn/pull/545)) by [frnidito](https://github.com/frnidito).
- Asterisk wildcard support for targeting loading ([#543](https://github.com/adamghill/django-unicorn/pull/543)) by [regoawt](https://github.com/regoawt).

## v0.51.0

- Fix: remove use of `ByteString` ([#534](https://github.com/adamghill/django-unicorn/pull/534)) by [hauntsaninja](https://github.com/hauntsaninja).
- Fix: Update `loading` on elements other than the current action element ([#512]https://github.com/adamghill/django-unicorn/pull/512) by [bazubii](https://github.com/bazubii)).
- Add new logo and doc changes ([#518](https://github.com/adamghill/django-unicorn/pull/518)) by [dancaron](https://github.com/dancaron).
- Fix: Nested children caching issues ([#511](https://github.com/adamghill/django-unicorn/pull/511)) by [bazubii](https://github.com/bazubii)).
- Fix: Negating a variable for `poll.disable` would not work correctly in some instances.

## v0.50.0

- Support more than 1 level of nested children ([#476](https://github.com/adamghill/django-unicorn/pull/507) by [bazubii](https://github.com/bazubii)).

[All changes since 0.49.2](https://github.com/adamghill/django-unicorn/compare/0.49.2...0.50.0).

## v0.49.2

- Fix: Calling methods with a model typehint would fail after being called multiple times ([#476](https://github.com/adamghill/django-unicorn/pull/476) by [stat1c-void](https://github.com/stat1c-void)).

[All changes since 0.49.1](https://github.com/adamghill/django-unicorn/compare/0.49.1...0.49.2).

## v0.49.1

- Fix: Missing `pp` import in Python 3.7.

[All changes since 0.49.0](https://github.com/adamghill/django-unicorn/compare/0.49.0...0.49.1).

## v0.49.0

- Fix: Handle inherited (i.e. subclassed) models [#459](https://github.com/adamghill/django-unicorn/issues/459).
- Fix: Support abbreviated `u:view` ([#464](https://github.com/adamghill/django-unicorn/pull/464) by [nerdoc](https://github.com/nerdoc)).
- Add version and build date to minified JavaScript for easier debugging.

[All changes since 0.48.0](https://github.com/adamghill/django-unicorn/compare/0.48.0...0.49.0).

## v0.48.0

- Reload JavaScript script elements when a template is re-rendered. Currently only enabled with the [`RELOAD_SCRIPT_ELEMENTS` setting](settings.md/#reload_script_elements).

[All changes since 0.47.0](https://github.com/adamghill/django-unicorn/compare/0.47.0...0.48.0).

## v0.47.0

- Fix: Include stacktrace for `AttributeError` errors.
- Fix: Only call `updated_` and `updating_` component functions once.

[All changes since 0.46.0](https://github.com/adamghill/django-unicorn/compare/0.46.0...0.47.0).

## v0.46.0

- Support for loading nested components from a route that uses a class-based view.
- Better support for children components.

[All changes since 0.45.1](https://github.com/adamghill/django-unicorn/compare/0.45.1...0.46.0).

## v0.45.1

- Fix: Handle JavaScript error that sometimes happens with nested components. [237](https://github.com/adamghill/django-unicorn/issues/237) by [clangley](https://github.com/clangley)

[All changes since 0.45.0](https://github.com/adamghill/django-unicorn/compare/0.45.0...0.45.1).

## v0.45.0

- Add ability to render initial data JavaScript inside the rendered component with [`SCRIPT_LOCATION`](settings.md#script_location) setting

[All changes since 0.44.1](https://github.com/adamghill/django-unicorn/compare/0.44.1...0.45.0).

## v0.44.1

- Fix: Some types of type annotations on a component method would cause an error when it was called [#392](https://github.com/adamghill/django-unicorn/issues/392) by [nerdoc](https://github.com/nerdoc).
- Add `component_id`, `component_name`, `component_key` to the `unicorn` dictionary in the template context [#389](https://github.com/adamghill/django-unicorn/issues/389) by [nerdoc](https://github.com/nerdoc).

[All changes since 0.44.0](https://github.com/adamghill/django-unicorn/compare/0.44.0...0.44.1).

## v0.44.0

- Add support for raising a `ValidationError` from component methods.

[All changes since 0.43.1](https://github.com/adamghill/django-unicorn/compare/0.43.1...0.44.0).

## v0.43.1

- Fix: direct views were not caching the component correctly.

[All changes since 0.43.0](https://github.com/adamghill/django-unicorn/compare/0.43.0...0.43.1).

## v0.43.0

- Defer displaying `messages` when an action method returns a [redirect](messages.md#redirecting).
- Prevent morphing or other changes when redirecting.

[All changes since 0.42.1](https://github.com/adamghill/django-unicorn/compare/0.42.1...0.43.0).

## v0.42.1

- Fix: dictionaries in a component would generate incorrect checksums and trigger a `Checksum does not match` error
- Remove some serializations that was happening unnecessarily on every render.
- Add Python 3.10 and Django 4.0 to test matrix.

[All changes since 0.42.0](https://github.com/adamghill/django-unicorn/compare/0.42.0...0.42.1).

## v0.42.0

- Remove all blank spaces from JSON responses.
- Optional support for [minifying response HTML](settings.md#minify_html) with [`htmlmin`](https://pypi.org/project/htmlmin/).
- Log warning message if the component HTML does not appear to be well-formed (i.e. an element does not have an ending tag). [#342](https://github.com/adamghill/django-unicorn/issues/342) by [liamlawless35](https://github.com/liamlawless35)

**Breaking changes**

- Bump supported Python to >=3.7.

[All changes since 0.41.2](https://github.com/adamghill/django-unicorn/compare/0.41.2...0.42.0).

## v0.41.2

- Fix: Handle excluding a field's attribute when the field is `None`.

[All changes since 0.41.1](https://github.com/adamghill/django-unicorn/compare/0.41.1...0.41.2).

## v0.41.1

- Fix: Handle component classes with a `bool` class attribute and a `form_class` with a `BooleanField`. Reported by [zurtri](https://github.com/zurtri)

[All changes since 0.41.0](https://github.com/adamghill/django-unicorn/compare/0.41.0...0.41.1).

## v0.41.0

- Support using a context variable for a component name. [#314](https://github.com/adamghill/django-unicorn/pull/314) by [robwa](https://github.com/robwa)

[All changes since 0.40.0](https://github.com/adamghill/django-unicorn/compare/0.40.0...0.41.0).

## v0.40.0

- Add [direct view](direct-view.md) so that components can be added directly to urls without being required to be included in a regular Django template.
- Add capability for [`startunicorn`](cli.md#sub-folders) to create components in sub-folders. (#299)[https://github.com/adamghill/django-unicorn/issues/299]

[All changes since 0.39.1](https://github.com/adamghill/django-unicorn/compare/0.39.1...0.40.0).

## v0.39.1

- Prefer `prefetch_related` to reduce database calls for many-to-many fields.

[All changes since 0.39.0](https://github.com/adamghill/django-unicorn/compare/0.39.0...0.39.1).

## v0.39.0

- Explicit error messages when an invalid component field is excluded
- Better support for serializing many-to-many fields which have been prefetched to reduce the number of database calls
- Support excluding many-to-many fields with `javascript_exclude`

[All changes since 0.38.1](https://github.com/adamghill/django-unicorn/compare/0.38.1...0.39.0).

## v0.38.1

- Fix: Allow components to be `pickled` so they can be cached.

[All changes since 0.38.0](https://github.com/adamghill/django-unicorn/compare/0.38.0...0.38.1).

## v0.38.0

- Include request context in component templates.

[All changes since 0.37.2](https://github.com/adamghill/django-unicorn/compare/0.37.2...0.38.0).

## v0.37.2

- Fix: nested field attributes for `javascript_exclude`.

[All changes since 0.37.1](https://github.com/adamghill/django-unicorn/compare/0.37.1...0.37.2).

## v0.37.1

- Support nested field attributes for `javascript_exclude`.

[All changes since 0.37.0](https://github.com/adamghill/django-unicorn/compare/0.37.0...0.37.1).

## v0.37.0

- Revert loading and dirty elements when the server returns a 304 (not modified) or a 500 error.

[All changes since 0.36.1](https://github.com/adamghill/django-unicorn/compare/0.36.1...0.37.0).

## v0.36.1

- More verbose error messages when components can't be loaded ([nerdoc](https://github.com/nerdoc)).
- More complete handling to prevent XSS attacks.

[All changes since 0.36.0](https://github.com/adamghill/django-unicorn/compare/0.36.0...0.36.1).

## v0.36.0

- Security fix: for CVE-2021-42053 to prevent XSS attacks (reported by [Jeffallan](https://github.com/Jeffallan)).

**Breaking changes**

- responses will be HTML encoded going forward (to explicitly opt-in to previous behavior use [safe](views.md#safe))

[All changes since 0.35.3](https://github.com/adamghill/django-unicorn/compare/0.35.3...0.36.0).

## v0.35.3

- Fix: Handle when there are multiple apps sub-directories [273](https://github.com/adamghill/django-unicorn/pull/273) by [apoorvaeternity](https://github.com/apoorvaeternity).

[All changes since 0.35.2](https://github.com/adamghill/django-unicorn/compare/0.35.2...0.35.3).

## v0.35.2

- Fix: Make sure `visible:elements` trigger as expected in more cases.
- Prevent the visible element from continuing to trigger if the visibility element method returns `False`.

[All changes since 0.35.0](https://github.com/adamghill/django-unicorn/compare/0.35.0...0.35.2).

## v0.35.0

- [Trigger](javascript.md) an `input` or `blur` event for a model element from JavaScript.
- [Visibility](visibility.md) event with `unicorn:visible` attribute.

**Breaking changes**

- `db_model` Python decorator, `unicorn:db`, `unicorn:field`, `unicorn:pk` template attributes are removed.

[All changes since 0.34.0](https://github.com/adamghill/django-unicorn/compare/0.34.0...0.35.0).

## v0.34.0

- Initial prototype for component template [lifecycle events](templates.md#lifecycle-events).
- Fix: elements after a child component would not get initialized [#262](https://github.com/adamghill/django-unicorn/pull/262) by [joshiggins](https://github.com/joshiggins).
- Fix: cache would fail in some instances [258](https://github.com/adamghill/django-unicorn/issues/258).

[All changes since 0.33.0](https://github.com/adamghill/django-unicorn/compare/0.33.0...0.34.0).

## v0.33.0

- Fix: Allow comments, blank lines, or text at the top of component templates before the root element.

[All changes since 0.32.0](https://github.com/adamghill/django-unicorn/compare/0.32.0...0.33.0).

## v0.32.0

- Add debounce support to actions.

[All changes since 0.31.0](https://github.com/adamghill/django-unicorn/compare/0.31.0...0.32.0).

## v0.31.0

- Move JavaScript static assets into `unicorn` sub-folder
- Determine correct path for installed app passed to `startunicorn` management command
- Call `startapp` management command if app is not already installed

[All changes since 0.30.0](https://github.com/adamghill/django-unicorn/compare/0.30.0...0.31.0).

## v0.30.0

- Look in all `INSTALLED_APPS` for components instead of only in a `unicorn` app [210](https://github.com/adamghill/django-unicorn/issues/210)
- Support `settings.APPS_DIR` which is the default for `django-cookiecutter` instead of just `settings.BASE_DIR` [214](https://github.com/adamghill/django-unicorn/issues/214)

**Breaking changes**

- Require an application name when running the `startunicorn` management command for where the component should be created

[All changes since 0.29.0](https://github.com/adamghill/django-unicorn/compare/0.29.0...0.30.0).

## v0.29.0

- Sanitize initial JSON to prevent XSS

[All changes since 0.28.0](https://github.com/adamghill/django-unicorn/compare/0.28.0...0.29.0).

## v0.28.0

- Re-fire poll method when tab/window comes back into focus after losing visibility (https://github.com/adamghill/django-unicorn/pull/202 by [frbor](https://github.com/frbor))

[All changes since 0.27.2](https://github.com/adamghill/django-unicorn/compare/0.27.2...0.28.0).

## v0.27.2

- Fix bug with relationship fields on a Django model

[All changes since 0.27.1](https://github.com/adamghill/django-unicorn/compare/0.27.1...0.27.2).

## v0.27.1

- Fix some issues with many-to-many fields on a Django model

[All changes since 0.27.0](https://github.com/adamghill/django-unicorn/compare/0.27.0...0.27.1).

## v0.27.0

- Many-to-many fields on a Django model are now supported
- Multiple partial targets

[All changes since 0.26.0](https://github.com/adamghill/django-unicorn/compare/0.26.0...0.27.0).

## v0.26.0

- Completely redesigned and much improved support for [Django models and QuerySets](django-models.md).
- Fix the `startunicorn` command and add some ascii art.

[All changes since 0.25.0](https://github.com/adamghill/django-unicorn/compare/0.25.0...0.26.0).

## v0.25.0

- Support calling functions in JavaScript modules.
- Fix: use `unicorn:db` without a `unicorn:model` in the same element.

[All changes since 0.24.0](https://github.com/adamghill/django-unicorn/compare/0.24.0...0.25.0).

## v0.24.0

- Support custom CSRF headers set with [CSRF_HEADER_NAME](https://docs.djangoproject.com/en/stable/ref/settings.md#csrf-header-name) setting.

[All changes since 0.23.0](https://github.com/adamghill/django-unicorn/compare/0.23.0...0.24.0).

## v0.23.0

- Performance enhancement that returns a 304 HTTP status code when an action happens, but the content doesn't change.
- Add [`unicorn:ignore`](https://www.django-unicorn/docs/templates/#ignore-elements) attribute to prevent an element from being morphed (useful when using `Unicorn` with libraries like `Select2` that change the DOM).
- Add support for passing arguments to [`Unicorn.call`](actions.md#calling-methods).
- Bug fix when attempting to cache component views that utilize the `db_model` decorator.

[All changes since 0.22.0](https://github.com/adamghill/django-unicorn/compare/0.22.0...0.23.0).

## v0.22.0

- Use Django cache for storing component state when available
- Add support for Django 2.2.x

[All changes since 0.21.2](https://github.com/adamghill/django-unicorn/compare/0.21.2...0.22.0).

## v0.21.2

- Add backported `dataclasses` for Python 3.6. ([@frbor](https://github.com/frbor))

[All changes since 0.21.0](https://github.com/adamghill/django-unicorn/compare/0.21.0...0.21.2).

## v0.21.0

- Bug fix: Prevent disabled polls from firing at all.
- Support [`Decimal` field type](views.md#class-variables).
- Support [`dataclass` field type](views.md#class-variables).
- Use [type hints](views.md#class-variable-type-hints) to cast fields to primitive Python types if possible.

[All changes since 0.20.0](https://github.com/adamghill/django-unicorn/compare/0.20.0...0.21.0).

## v0.20.0

- Add ability to exclude component view properties from JavaScript to reduce the amount of data initially rendered to the page with [`javascript_exclude`](views.md#javascript_exclude).
- Add [`complete`](views.md#complete), [`rendered`](views.md#renderedhtml), [`parent_rendered`](views.md#parent_renderedhtml) component hooks.
- Call [JavaScript functions](javascript.md) from a component view's method.

[All changes since 0.19.0](https://github.com/adamghill/django-unicorn/compare/0.19.0...0.20.0).

## v0.19.0

- Re-implemented how action method parsing is done to remove all edge cases when passing arguments to component view methods. ([@frbor](https://github.com/frbor)).
- Add support for passing kwargs to component view methods.

[All changes since 0.18.1](https://github.com/adamghill/django-unicorn/compare/0.18.1...0.19.0).

## v0.18.1

- Fix regression where component kwargs were getting lost (<a href="https://github.com/adamghill/django-unicorn/issues/140">#140</a>, <a href="https://github.com/adamghill/django-unicorn/issues/141">#141</a>)
- Fix <code>startunicorn</code> management command (<a href="https://github.com/adamghill/django-unicorn/issues/142">#142</a>)

[All changes since 0.18.0](https://github.com/adamghill/django-unicorn/compare/0.18.0...0.18.1).

## v0.18.0

- Only send updated data back in the response to reduce network latency.
- Experimental support for [queuing up requests](queue-requests.md) to alleviate race conditions when functions take a long time to process.
- Bug fix: prevent race condition where an instantiated component class would be inadvertently re-used for component views that are slow to render
- Bug fix: use the correct component name to call a [component method from "outside" the component](actions.md#calling-methods).
- Deprecated: `DJANGO_UNICORN` setting has been renamed to `UNICORN`.

[All changes since 0.17.2](https://github.com/adamghill/django-unicorn/compare/0.17.2...0.18.0).

## v0.17.2

- Don't send the parent context in the response for child components that specify a partial update.
- Add support for element models to specify a partial update.
- Add support for polls to specify a partial update.
- Handle `date`, `time`, `timespan` when passed as arguments from JavaScript.
- Render child component template's JavaScript initialization with the parent's as opposed to inserting a new script tag after the child component is rendered.
- Bug fix: prevent an error when rendering a Django model with a date-related field, but a string value.

[All changes since 0.17.1](https://github.com/adamghill/django-unicorn/compare/0.17.1...0.17.2).

## v0.17.1

- Remove stray print statement.
- Fix bug where child components would sometimes lose their action events.

[All changes since 0.17.0](https://github.com/adamghill/django-unicorn/compare/0.17.0...0.17.1).

## v0.17.0

- Target DOM changes from an action to only a portion of the DOM with [partial updates](partial-updates.md).

[All changes since 0.16.1](https://github.com/adamghill/django-unicorn/compare/0.16.1...0.17.0).

## v0.16.1

- Remove debounce from action methods to reduce any perceived lag.

[All changes since 0.16.0](https://github.com/adamghill/django-unicorn/compare/0.16.0...0.16.1).

## v0.16.0

- [Dirty states](dirty-states.md) for when there is a change that hasn't been synced yet.
- Add support for setting [multiple classes for loading states](loading-states.md#class).
- Attempt to handle when the component gets out of sync with an invalid checksum error.
- Performance tweaks when there isn't a change to a model or dbModel with lazy or defer modifiers.

[All changes since 0.15.1](https://github.com/adamghill/django-unicorn/compare/0.15.1...0.16.0).

## v0.15.1

- Fix bug where a component name has a dash in its name

[All changes since 0.15.1](https://github.com/adamghill/django-unicorn/compare/0.15.0...0.15.1).

## v0.15.0

- Add support for [child components](child-components.md)
- Add [discard](actions.md#discard) action modifier
- Add support for referring to components in a folder structure
- Remove restriction that component templates must start with a div
- Remove restriction that component root can't also have `unicorn:model` or `unicorn:action`

[All changes since 0.15.0](https://github.com/adamghill/django-unicorn/compare/0.14.1...0.15.0).

## v0.14.1

- Prevent the currently focused model element from updating after the AJAX request finishes ([#100](https://github.com/adamghill/django-unicorn/issues/100)).

[All changes since 0.14.0](https://github.com/adamghill/django-unicorn/compare/0.14.0...0.14.1).

## v0.14.0

- [Disable poll](polling.md#disable-poll) with a component field
- Dynamically change polling options with [PollUpdate](polling.md#pollupdate)
- Basic support for [`pydantic`](https://pydantic-docs.helpmanual.io) models

[All changes since 0.13.0](https://github.com/adamghill/django-unicorn/compare/0.13.0...0.14.0).

## v0.13.0

- [Component key](components.md#component-key) to allow disambiguation of components of the same name
- [`$returnValue`](actions.md#returnvalue) special argument
- Get the last action method's [return value](actions.md#return-values)

[All changes since 0.12.0](https://github.com/adamghill/django-unicorn/compare/0.12.0...0.13.0).

## v0.12.0

- [Redirect](redirecting.md) from action method in component

[All changes since 0.11.2](https://github.com/adamghill/django-unicorn/compare/0.11.2...0.12.0).

## v0.11.2

- Fix encoding issue with default component template on Windows ([#91](https://github.com/adamghill/django-unicorn/issues/91))
- Fix circular import when creating the component ([#92](https://github.com/adamghill/django-unicorn/issues/92))

[All changes since 0.11.0](https://github.com/adamghill/django-unicorn/compare/0.11.0...0.11.2).

## v0.11.0

- [`$toggle`](actions.md#toggle) special method.
- Support nested properties when using the [set shortcut](actions.md#set-shortcut).
- Fix action string arguments that would get spaces removed inadvertently.

**Breaking changes**

- All existing special methods now start with a `$` to signify they are magical. Therefore, `refresh` is now [`$refresh`](actions.md#refresh), `reset` is now [`$reset`](actions.md#reset), and `validate` is now [`$validate`](actions.md#validate).

[All changes since 0.10.1](https://github.com/adamghill/django-unicorn/compare/0.10.1...0.11.0).

## v0.10.1

- Use LRU cache for constructed components to prevent ever-expanding memory.
- Loosen `beautifulsoup4` version requirement.
- Fix bug to handle floats so that they don't lose precision when serialized to JSON.
- Fix bug to handle related models (ForeignKeys, OneToOne, etc) fields in Django models.

[All changes since 0.10.0](https://github.com/adamghill/django-unicorn/compare/0.10.0...0.10.1).

## v0.10.0

- Add support for [passing kwargs](components.md#pass-data-to-a-component) into the component on the template
- Provide access to the [current request](views.md#request) in the component's methods

[All changes since 0.9.4](https://github.com/adamghill/django-unicorn/compare/0.9.4...0.10.0).

## v0.9.4

- Fix: Prevent Django `CharField` form field from stripping whitespaces when used for validation.
- Fix: Handle edge case that would generate a null exception.
- Fix: Only change loading state when an action method gets called, not on every event fire.

[All changes since 0.9.1](https://github.com/adamghill/django-unicorn/compare/0.9.1...0.9.3).

## v0.9.3

- Handle child elements triggering an event which should be handled by a parent unicorn element.

[All changes since 0.9.1](https://github.com/adamghill/django-unicorn/compare/0.9.1...0.9.3).

## v0.9.1

- Fix: certain actions weren't triggering model values to get set correctly

[All changes since 0.9.0](https://github.com/adamghill/django-unicorn/compare/0.9.0...0.9.1).

## v0.9.0

- [Loading states](loading-states.md) for improved UX.
- `$event` [special argument](actions.md#events) for `actions`.
- `u` [unicorn attribute](templates.md#unicorn-attributes).
- `APPS` [setting](settings.md#apps) for determing where to look for components.
- Add support for parent elements for non-db models.
- Fix: Handle if `Meta` doesn't exist for db models.

[All changes since 0.8.0](https://github.com/adamghill/django-unicorn/compare/0.8.0...0.9.0).

## v0.8.0

- Add much more elaborate support for dealing with [Django models](django-models.md).

[All changes since 0.7.1](https://github.com/adamghill/django-unicorn/compare/0.7.1...0.8.0).

## v0.7.1

- Fix bug where multiple actions would trigger multiple payloads.
- Handle lazy models that are children of an action model better.

[All changes since 0.7.0](https://github.com/adamghill/django-unicorn/compare/0.7.0...0.7.1).

## v0.7.0

- Parse [action method arguments](actions.md#passing-arguments) as basic Python objects
- [Stop and prevent modifiers](actions.md#modifiers) on actions
- [Defer modifier](templates.md#defer) on model
- Support for multiple actions on the same element
- Django setting for whether the JavaScript is [minified](settings.md#minified)

**Breaking changes**

- Remove unused `unicorn_styles` template tag
- Use dash for poll timing instead of dot

[All changes since 0.6.5](https://github.com/adamghill/django-unicorn/compare/0.6.5...0.7.0).

## v0.6.5

- Attempt to get the CSRF token from the cookie first before looking at the CSRF token.

[All changes since 0.6.4](https://github.com/adamghill/django-unicorn/compare/0.6.4...0.6.5).

## v0.6.4

- Fix bug where lazy models weren't sending values before an action was called
- Add `is_valid` method to component to more easily check if a component has validation errors.
- Better error message if the CSRF token is not available.

[All changes since 0.6.3](https://github.com/adamghill/django-unicorn/compare/0.6.3...0.6.4).

## v0.6.3

- Fix bug where model elements weren't getting updated values when an action was being called during the same component update.
- Fix bug where some action event listeners were duplicated.

[All changes since 0.6.2](https://github.com/adamghill/django-unicorn/compare/0.6.2...0.6.3).

## v0.6.2

- More robust fix for de-duping multiple actions.
- Fix bug where conditionally added actions didn't get an event listener.

[All changes since 0.6.1](https://github.com/adamghill/django-unicorn/compare/0.6.1...0.6.2).

## v0.6.1

- Fix model sync getting lost when there is an action ([issue 39](https://github.com/adamghill/django-unicorn/issues/39)).
- Small fix for validations.

[All changes since 0.6.0](https://github.com/adamghill/django-unicorn/compare/0.6.0...0.6.1).

## v0.6.0

- [Realtime validation](validation.md) of a Unicorn model.
- [Polling](polling.md) for component updates.
- [More component hooks](views.md)

[All changes since 0.5.0](https://github.com/adamghill/django-unicorn/compare/0.5.0...0.6.0).

## v0.5.0

- [Call](actions.md#calling-methods) component method from JavaScript.
- Support classes, dictionaries, Django Models, (read-only) Django QuerySets properties on a component.
- [Debounce](templates.md#debounce) modifier to change how fast changes are sent to the backend from `unicorn:model`.
- [Lazy](templates.md#lazy) modifier to listen for `blur` instead of `input` on `unicorn:model`.
- Better support for `textarea` HTML element.

[All changes since 0.4.0](https://github.com/adamghill/django-unicorn/compare/0.4.0...0.5.0).

## v0.4.0

- [Set shortcut](actions.md#set-shortcut) for setting properties.
- Listen for any valid event, not just `click`.
- Better handling for model updates when element ids aren't unique.

[All changes since 0.3.0](https://github.com/adamghill/django-unicorn/compare/0.3.0...0.4.0).

## v0.3.0

- Add [mount hook](views.md#mount).
- Add [reset](actions.md#reset) action.
- Remove lag when typing fast in a text input and overall improved performance.
- Better error handling for exceptional cases.

[All changes since 0.2.3](https://github.com/adamghill/django-unicorn/compare/0.2.3...0.3.0).

## v0.2.3

- Fix for creating default folders when running `startunicorn`.

[All changes since 0.2.2](https://github.com/adamghill/django-unicorn/compare/0.2.2...0.2.3).

## v0.2.2

- Set default `template_name` if it's missing in component.

[All changes since 0.2.1](https://github.com/adamghill/django-unicorn/compare/0.2.1...0.2.2).

## v0.2.1

- Fix `startunicorn` Django management command.

[All changes since 0.2.0](https://github.com/adamghill/django-unicorn/compare/0.2.0...0.2.1).

## v0.2.0

- Switch from `Component` class to `UnicornView` to follow the conventions of class-based views.
- [Investigate using class-based view instead of the custom Component class](https://github.com/adamghill/django-unicorn/issues/4)

[All changes since 0.1.1](https://github.com/adamghill/django-unicorn/compare/0.1.1...0.2.0).

## v0.1.1

- Fix package readme and repository link.

[All changes since 0.1.0](https://github.com/adamghill/django-unicorn/compare/0.1.0...0.1.1).

## v0.1.0

- Initial version with basic functionality.
