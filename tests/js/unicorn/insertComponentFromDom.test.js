/**
 * Regression tests for issue #666: updating child components via a parent method.
 *
 * When a parent component re-renders (after a parent method modifies children),
 * the morphed parent DOM has updated unicorn:data and unicorn:meta for each child.
 * insertComponentFromDom must update existing child JS component state so the
 * next request from the child sends correct (updated) data instead of stale data.
 */

import test from "ava";
import { JSDOM } from "jsdom";
import { insertComponentFromDom } from "../../../src/django_unicorn/static/unicorn/js/unicorn.js";
import { components } from "../../../src/django_unicorn/static/unicorn/js/store.js";

function makeNode(id, checksum, data) {
  const node = global.document.createElement("div");
  node.setAttribute("unicorn:id", id);
  node.setAttribute("unicorn:name", "child-view");
  node.setAttribute("unicorn:key", "");
  node.setAttribute("unicorn:meta", checksum);
  node.setAttribute("unicorn:data", JSON.stringify(data));
  node.setAttribute("unicorn:calls", "[]");
  return node;
}

test.beforeEach(() => {
  const dom = new JSDOM("<!doctype html><html><body></body></html>");
  global.document = dom.window.document;
  global.window = dom.window;
  global.Node = dom.window.Node;
  global.NodeFilter = dom.window.NodeFilter;

  for (const key in components) {
    delete components[key];
  }
});

test.afterEach(() => {
  delete global.document;
  delete global.window;
  delete global.Node;
  delete global.NodeFilter;
});

test("insertComponentFromDom creates new component when not in store", (t) => {
  const node = makeNode("new-id", "checksum-abc", { is_editing: false });
  // Component.init() searches the document for the root element, so append it first
  document.body.appendChild(node);

  insertComponentFromDom(node);

  t.truthy(components["new-id"]);
  t.false(components["new-id"].data.is_editing);
});

test("insertComponentFromDom updates existing component data when checksum differs", (t) => {
  // Simulate a child component that was initialized on page load with is_editing=false
  components["child-123"] = {
    id: "child-123",
    checksum: "old-checksum",
    hash: "old-hash",
    epoch: "111",
    data: { is_editing: false },
    setModelValues() {},
  };

  // After the parent's begin_edit_all runs, the DOM has new checksum and is_editing=true
  const updatedNode = makeNode("child-123", "new-checksum", { is_editing: true });

  insertComponentFromDom(updatedNode);

  t.is(components["child-123"].data.is_editing, true,
    "Child data should be updated when server changes it via parent method");
  t.is(components["child-123"].checksum, "new-checksum",
    "Child checksum should be updated to match the new server state");
});

test("insertComponentFromDom does not update existing component when checksum is same", (t) => {
  components["child-456"] = {
    id: "child-456",
    checksum: "same-checksum",
    data: { is_editing: false },
    setModelValues() {},
  };

  // Same checksum — no server-side change
  const sameNode = makeNode("child-456", "same-checksum", { is_editing: true });

  insertComponentFromDom(sameNode);

  t.false(components["child-456"].data.is_editing,
    "Data should not be overwritten when checksum has not changed");
});

test("insertComponentFromDom updates hash and epoch when checksum differs", (t) => {
  components["child-789"] = {
    id: "child-789",
    checksum: "old-checksum",
    hash: "old-hash",
    epoch: "100",
    data: {},
    setModelValues() {},
  };

  const node = global.document.createElement("div");
  node.setAttribute("unicorn:id", "child-789");
  node.setAttribute("unicorn:name", "child-view");
  node.setAttribute("unicorn:key", "");
  // Format: checksum:hash:epoch
  node.setAttribute("unicorn:meta", "new-checksum:new-hash:200");
  node.setAttribute("unicorn:data", JSON.stringify({ value: 42 }));
  node.setAttribute("unicorn:calls", "[]");

  insertComponentFromDom(node);

  t.is(components["child-789"].checksum, "new-checksum");
  t.is(components["child-789"].hash, "new-hash");
  t.is(components["child-789"].epoch, "200");
  t.is(components["child-789"].data.value, 42);
});
