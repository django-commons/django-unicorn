import test from "ava";
import { JSDOM } from "jsdom";
import { deleteComponent } from "../../../src/django_unicorn/static/unicorn/js/unicorn.js";
import { components } from "../../../src/django_unicorn/static/unicorn/js/store.js";

test.beforeEach(() => {
  const dom = new JSDOM("<!doctype html><html><body></body></html>");
  global.document = dom.window.document;

  // Clear components store between tests
  for (const key in components) {
    delete components[key];
  }
});

test.afterEach(() => {
  delete global.document;
});

test("deleteComponent removes component from store", (t) => {
  const componentId = "test-delete-id";
  components[componentId] = { id: componentId };

  deleteComponent(componentId);

  t.falsy(components[componentId]);
});

test("deleteComponent removes root element from DOM", (t) => {
  const componentId = "test-dom-remove-id";
  components[componentId] = { id: componentId };

  const root = document.createElement("div");
  root.setAttribute("unicorn:id", componentId);
  document.body.appendChild(root);

  t.truthy(document.querySelector(`[unicorn\\:id="${componentId}"]`));

  deleteComponent(componentId);

  t.falsy(document.querySelector(`[unicorn\\:id="${componentId}"]`));
});

test("deleteComponent is a no-op when element is not in DOM", (t) => {
  const componentId = "test-no-dom-id";
  components[componentId] = { id: componentId };

  // Element was never added to the DOM — should not throw
  t.notThrows(() => deleteComponent(componentId));
  t.falsy(components[componentId]);
});

test("deleteComponent is a no-op when component is not in store", (t) => {
  const componentId = "test-no-store-id";

  const root = document.createElement("div");
  root.setAttribute("unicorn:id", componentId);
  document.body.appendChild(root);

  // Component not in store — element should still be removed
  t.notThrows(() => deleteComponent(componentId));
  t.falsy(document.querySelector(`[unicorn\\:id="${componentId}"]`));
});
