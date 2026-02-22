import test from "ava";
import { getComponent } from "../utils.js";
import { handleDirty } from "../../../src/django_unicorn/static/unicorn/js/eventListeners.js";

test("dirtyEls: element with u:dirty.class and no u:model is collected", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.class="is-dirty" u:target="nameInput"></div>
</div>`;
  const component = getComponent(html);

  t.is(component.dirtyEls.length, 1);
  t.deepEqual(component.dirtyEls[0].dirty.classes, ["is-dirty"]);
});

test("dirtyEls: element with u:model is NOT added to dirtyEls (self-dirty handled inline)", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" u:dirty.class="is-dirty">
</div>`;
  const component = getComponent(html);

  t.is(component.dirtyEls.length, 0);
  t.is(component.modelEls.length, 1);
});

test("dirtyEls: multiple separate dirty elements are all collected", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div id="wrapper" u:dirty.class="is-dirty" u:target="nameInput"></div>
  <span u:dirty.attr="disabled" u:target="nameInput"></span>
</div>`;
  const component = getComponent(html);

  t.is(component.dirtyEls.length, 2);
});

test("dirtyEls: element without u:dirty modifier produces empty dirty object and is NOT collected", (t) => {
  // A bare u:dirty with no modifier like .class or .attr results in an empty
  // dirty object, which should not be added to dirtyEls.
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name">
</div>`;
  const component = getComponent(html);

  t.is(component.dirtyEls.length, 0);
});

test("handleDirty: adds dirty class to element that targets the changed model input (by id)", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.class="is-dirty" u:target="nameInput"></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  t.is(dirtyElement.el.classList.length, 0);

  handleDirty(component, modelElement);

  t.is(dirtyElement.el.classList.length, 1);
  t.is(dirtyElement.el.classList[0], "is-dirty");
});

test("handleDirty: reverts dirty class when model input returns to original value", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.class="is-dirty is-already-dirty" u:target="nameInput" class="is-dirty is-already-dirty"></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  t.is(dirtyElement.el.classList.length, 2);

  handleDirty(component, modelElement, true);

  t.is(dirtyElement.el.classList.length, 0);
});

test("handleDirty: does NOT touch a dirty element that targets a different id", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <input u:model="email" id="emailInput">
  <div u:dirty.class="is-dirty" u:target="emailInput"></div>
</div>`;
  const component = getComponent(html);

  const nameModelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  t.is(dirtyElement.el.classList.length, 0);

  // Only name changed — dirty element targets emailInput, so it must stay clean
  handleDirty(component, nameModelElement);

  t.is(dirtyElement.el.classList.length, 0);
});

test("handleDirty: adds dirty class to element that targets the model input by key", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" u:key="nameKey">
  <div u:dirty.class="is-dirty" u:target="nameKey"></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  t.is(dirtyElement.el.classList.length, 0);

  handleDirty(component, modelElement);

  t.is(dirtyElement.el.classList.length, 1);
  t.is(dirtyElement.el.classList[0], "is-dirty");
});


test("handleDirty: sets attr on element that targets the model input", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.attr="readonly" u:target="nameInput"></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  // Note: the test walker overrides getAttribute, so use hasAttribute instead
  t.false(dirtyElement.el.hasAttribute("readonly"));

  handleDirty(component, modelElement);

  t.true(dirtyElement.el.hasAttribute("readonly"));
});

test("handleDirty: removes attr when reverting on targeted element", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.attr="readonly" u:target="nameInput" readonly="readonly"></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  t.true(dirtyElement.el.hasAttribute("readonly"));

  handleDirty(component, modelElement, true);

  t.false(dirtyElement.el.hasAttribute("readonly"));
});


test("handleDirty: untargeted dirty element becomes dirty on any model change", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.class="form-changed"></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  t.is(dirtyElement.el.classList.length, 0);

  handleDirty(component, modelElement);

  t.is(dirtyElement.el.classList.length, 1);
  t.is(dirtyElement.el.classList[0], "form-changed");
});

test("handleDirty: untargeted dirty element is NOT auto-reverted during editing (only after server response)", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.class="form-changed" class="form-changed"></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  // Class is already present (element was dirtied earlier)
  t.is(dirtyElement.el.classList.length, 1);

  handleDirty(component, modelElement, true);

  t.is(dirtyElement.el.classList.length, 1);
  t.is(dirtyElement.el.classList[0], "form-changed");
});

test("handleDirty: removes class on targeted element (class.remove modifier)", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.class.remove="btn-clean" u:target="nameInput" class="btn-clean"></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  t.is(dirtyElement.el.classList.length, 1);
  t.is(dirtyElement.el.classList[0], "btn-clean");

  handleDirty(component, modelElement);

  t.is(dirtyElement.el.classList.length, 0);
});

test("handleDirty: restores removed class when reverting on targeted element", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input u:model="name" id="nameInput">
  <div u:dirty.class.remove="btn-clean" u:target="nameInput" class=""></div>
</div>`;
  const component = getComponent(html);

  const modelElement = component.modelEls[0];
  const dirtyElement = component.dirtyEls[0];

  t.is(dirtyElement.el.classList.length, 0);

  handleDirty(component, modelElement, true);

  t.is(dirtyElement.el.classList.length, 1);
  t.is(dirtyElement.el.classList[0], "btn-clean");
});
