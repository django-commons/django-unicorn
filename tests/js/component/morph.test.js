import test from "ava";
import { getDocument, walkDOM } from "../utils.js";
import { Component } from "../../../src/django_unicorn/static/unicorn/js/component.js";

// Provide a minimal global Unicorn stub so that Component.morph() can call
// Unicorn.deleteComponent / Unicorn.insertComponentFromDom without errors.
test.before(() => {
  global.Unicorn = {
    deleteComponent: () => {},
    insertComponentFromDom: () => {},
  };
});

/**
 * Builds a Component instance suited for testing morph() behaviour.
 *
 * @param {string} html          - HTML for the parent component root element.
 * @param {Function} morphFn     - Function used as the morpher (receives targetDom and rerenderedHtml).
 * @param {Object} morpherOptions - Optional options forwarded to morpher.options (e.g. {RELOAD_SCRIPT_ELEMENTS: true}).
 */
function getMorphTestComponent(html, morphFn, morpherOptions) {
  const doc = getDocument(html);

  const component = new Component({
    id: "parent-id",
    name: "parent",
    data: {},
    calls: [],
    document: doc,
    messageUrl: "test",
    walker: walkDOM,
    morpher: {
      options: morpherOptions || {},
      morph: morphFn || ((a) => a),
    },
    window: {
      document: { title: "" },
      history: { pushState: () => {} },
      location: { href: "" },
      addEventListener: () => {},
    },
  });

  // Keep component.document in sync (mirrors what getComponent() in utils.js does)
  component.document = doc;

  return component;
}

/**
 * Returns a morpher mock that appends a single child component element to the
 * target DOM. The child element (and any script tags inside it) is created via
 * innerHTML, replicating the behaviour of morphdom which produces non-executing
 * script elements.
 *
 * @param {string} childId   - The unicorn:id value for the new child.
 * @param {string} scriptSrc - Optional external script src to add.
 * @param {string} inlineCode - Optional inline script content.
 */
function makeChildAddingMorpher(childId, { scriptSrc, inlineCode } = {}) {
  return function mockMorph(targetDom) {
    const doc = targetDom.ownerDocument;

    const childDiv = doc.createElement("div");
    childDiv.setAttribute("unicorn:id", childId);
    childDiv.setAttribute("unicorn:name", "child");
    childDiv.setAttribute("unicorn:meta", "XYZ");
    childDiv.setAttribute("unicorn:data", "{}");
    childDiv.setAttribute("unicorn:calls", "[]");

    if (inlineCode) {
      // Create the script via innerHTML so that it is NOT auto-executed when
      // appended — this mimics the morphdom diffing behaviour.
      const temp = doc.createElement("div");
      temp.innerHTML = `<script>${inlineCode}</script>`;
      childDiv.appendChild(temp.firstChild);
    }

    if (scriptSrc) {
      const temp = doc.createElement("div");
      temp.innerHTML = `<script src="${scriptSrc}"></script>`;
      childDiv.appendChild(temp.firstChild);
    }

    targetDom.appendChild(childDiv);
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test("scripts in a newly added child component are replaced with fresh elements", (t) => {
  const html = `
<div unicorn:id="parent-id" unicorn:name="parent" unicorn:meta="ABC"
     unicorn:data="{}" unicorn:calls="[]">
  <p>Parent content</p>
</div>`;

  const component = getMorphTestComponent(
    html,
    makeChildAddingMorpher("child-id", { inlineCode: "window.__ran = true;" })
  );

  const doc = component.document;

  // Spy: count how many times createElement("script") is called during morph.
  // Our fix creates one fresh script element per script found in new child
  // components, so the counter must be >= 1 after morph().
  let scriptsCreatedByFix = 0;
  const origCreate = doc.createElement.bind(doc);
  doc.createElement = (tag) => {
    if (tag.toLowerCase() === "script") {
      scriptsCreatedByFix += 1;
    }
    return origCreate(tag);
  };

  component.morph(component.root, "<rerendered>");

  t.is(scriptsCreatedByFix, 1, "One fresh script element should be created for the new child component's script tag");
});

test("external script src in a newly added child component is preserved on the fresh element", (t) => {
  const html = `
<div unicorn:id="parent-id" unicorn:name="parent" unicorn:meta="ABC"
     unicorn:data="{}" unicorn:calls="[]">
</div>`;

  const component = getMorphTestComponent(
    html,
    makeChildAddingMorpher("child-id", { scriptSrc: "https://example.com/lib.js" })
  );

  component.morph(component.root, "<rerendered>");

  // After morph the child's script element should exist with its src attribute
  const childEl = component.root.querySelector('[unicorn\\:id="child-id"]');
  t.truthy(childEl, "Child component element should be in the DOM");

  const scriptEl = childEl && childEl.querySelector("script");
  t.truthy(scriptEl, "A script element should exist inside the new child component");
  t.is(
    scriptEl && scriptEl.getAttribute("src"),
    "https://example.com/lib.js",
    "The src attribute should be preserved on the fresh script element"
  );
});

test("scripts in an already-existing child component are not re-executed on re-render", (t) => {
  // The child component is present in the initial HTML, so it should be in
  // componentIdsBeforeMorph and our fix must NOT touch its scripts.
  const html = `
<div unicorn:id="parent-id" unicorn:name="parent" unicorn:meta="ABC"
     unicorn:data="{}" unicorn:calls="[]">
  <div unicorn:id="existing-child-id" unicorn:name="child" unicorn:meta="XYZ"
       unicorn:data="{}" unicorn:calls="[]">
    <script>window.__existing = true;</script>
  </div>
</div>`;

  // Morpher that does nothing (existing child remains unchanged)
  const component = getMorphTestComponent(html, () => {});

  const doc = component.document;
  let scriptsCreatedByFix = 0;
  const origCreate = doc.createElement.bind(doc);
  doc.createElement = (tag) => {
    if (tag.toLowerCase() === "script") {
      scriptsCreatedByFix += 1;
    }
    return origCreate(tag);
  };

  component.morph(component.root, "<rerendered>");

  t.is(scriptsCreatedByFix, 0, "Scripts in a pre-existing child component must not be replaced");
});

test("script replacement is skipped when RELOAD_SCRIPT_ELEMENTS is enabled on the morpher", (t) => {
  // When RELOAD_SCRIPT_ELEMENTS is true, morphdom's onNodeAdded hook already
  // replaces scripts — our code must not create duplicates.
  const html = `
<div unicorn:id="parent-id" unicorn:name="parent" unicorn:meta="ABC"
     unicorn:data="{}" unicorn:calls="[]">
</div>`;

  const component = getMorphTestComponent(
    html,
    makeChildAddingMorpher("child-id", { inlineCode: "window.__ran = true;" }),
    { RELOAD_SCRIPT_ELEMENTS: true }
  );

  const doc = component.document;
  let scriptsCreatedByFix = 0;
  const origCreate = doc.createElement.bind(doc);
  doc.createElement = (tag) => {
    if (tag.toLowerCase() === "script") {
      scriptsCreatedByFix += 1;
    }
    return origCreate(tag);
  };

  component.morph(component.root, "<rerendered>");

  t.is(
    scriptsCreatedByFix,
    0,
    "Our fix should not run when RELOAD_SCRIPT_ELEMENTS is enabled to avoid double execution"
  );
});

test("scripts in a deeply nested new child component are executed exactly once", (t) => {
  // Scenario: parent → new child A → new child B (nested)
  // Child B's scripts must be replaced exactly once (when processing B),
  // not again when processing A (the ancestor-check must skip B's scripts
  // when iterating over A).
  const html = `
<div unicorn:id="parent-id" unicorn:name="parent" unicorn:meta="ABC"
     unicorn:data="{}" unicorn:calls="[]">
</div>`;

  // Morpher that adds a child A which itself contains a child B with a script
  function nestedMorph(targetDom) {
    const doc = targetDom.ownerDocument;

    const childA = doc.createElement("div");
    childA.setAttribute("unicorn:id", "child-a");
    childA.setAttribute("unicorn:name", "child-a");
    childA.setAttribute("unicorn:meta", "A");
    childA.setAttribute("unicorn:data", "{}");
    childA.setAttribute("unicorn:calls", "[]");

    // Own script for A
    const tempA = doc.createElement("div");
    tempA.innerHTML = "<script>window.__a = true;</script>";
    childA.appendChild(tempA.firstChild);

    // Nested child B with its own script
    const childB = doc.createElement("div");
    childB.setAttribute("unicorn:id", "child-b");
    childB.setAttribute("unicorn:name", "child-b");
    childB.setAttribute("unicorn:meta", "B");
    childB.setAttribute("unicorn:data", "{}");
    childB.setAttribute("unicorn:calls", "[]");

    const tempB = doc.createElement("div");
    tempB.innerHTML = "<script>window.__b = true;</script>";
    childB.appendChild(tempB.firstChild);

    childA.appendChild(childB);
    targetDom.appendChild(childA);
  }

  const component = getMorphTestComponent(html, nestedMorph);

  const doc = component.document;
  let scriptsCreatedByFix = 0;
  const origCreate = doc.createElement.bind(doc);
  doc.createElement = (tag) => {
    if (tag.toLowerCase() === "script") {
      scriptsCreatedByFix += 1;
    }
    return origCreate(tag);
  };

  component.morph(component.root, "<rerendered>");

  // 2 new child components (A and B), each with 1 script → exactly 2 replacements
  t.is(scriptsCreatedByFix, 2, "Each new child component's script should be replaced exactly once");
});
