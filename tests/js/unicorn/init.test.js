import test from "ava";
import { JSDOM } from "jsdom";
import { init } from "../../../src/django_unicorn/static/unicorn/js/unicorn.js";
import { components } from "../../../src/django_unicorn/static/unicorn/js/store.js";

test.beforeEach(() => {
  const dom = new JSDOM("<!doctype html><html><body></body></html>");
  global.document = dom.window.document;
  global.window = dom.window;
  global.MutationObserver = dom.window.MutationObserver;
  global.Node = dom.window.Node;
  global.NodeFilter = dom.window.NodeFilter;

  for (const key in components) {
    delete components[key];
  }
});

test.afterEach(() => {
  delete global.document;
  delete global.window;
  delete global.MutationObserver;
  delete global.Node;
  delete global.NodeFilter;
});

test("init unicorn", (t) => {
  const actual = init("unicorn/", "X-Unicorn", "unicorn", { NAME: "morphdom" });

  t.true(actual.messageUrl === "unicorn/");
  t.true(actual.csrfTokenHeaderName === "X-Unicorn");
  t.true(actual.csrfTokenCookieName === "unicorn");
});
