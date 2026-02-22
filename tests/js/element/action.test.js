import test from "ava";
import fetchMock from "fetch-mock";
import { send } from "../../../src/django_unicorn/static/unicorn/js/messageSender.js";
import { getComponent, getElement } from "../utils.js";

test("click", (t) => {
  const html = "<button unicorn:click='test()'></button>";
  const element = getElement(html);

  const action = element.actions[0];
  t.is(action.name, "test()");
  t.is(action.eventType, "click");
  t.is(action.debounceTime, 0);
});

test("keydown.enter", (t) => {
  const html = "<input unicorn:keydown.enter='test()'></input>";
  const element = getElement(html);

  const action = element.actions[0];
  t.is(action.name, "test()");
  t.is(action.eventType, "keydown");
  t.is(action.key, "enter");
});

test("click.prevent", (t) => {
  const html = "<a href='#' unicorn:click.prevent='test()'>Test()</a>";
  const element = getElement(html);

  const action = element.actions[0];
  t.true(action.isPrevent);
  t.is(action.eventType, "click");
  t.is(action.key, undefined);
});

test("click.stop", (t) => {
  const html = "<a href='#' unicorn:click.stop='test()'>Test()</a>";
  const element = getElement(html);

  const action = element.actions[0];
  t.true(action.isStop);
  t.is(action.eventType, "click");
  t.is(action.key, undefined);
});

test("click.discard", (t) => {
  const html = "<a href='#' unicorn:click.discard='test()'>Test()</a>";
  const element = getElement(html);

  const action = element.actions[0];
  t.true(action.isDiscard);
  t.is(action.eventType, "click");
  t.is(action.key, undefined);
});

test("click.debounce", (t) => {
  const html = "<a href='#' unicorn:click.debounce-99='test()'>Test()</a>";
  const element = getElement(html);

  const action = element.actions[0];
  t.is(action.debounceTime, 99);
  t.is(action.eventType, "click");
  t.is(action.key, undefined);
});

test("click.keyup.enter.debounce", (t) => {
  const html =
    "<a href='#' unicorn:click.keyup.enter.debounce-99='test()'>Test()</a>";
  const element = getElement(html);

  const action = element.actions[0];
  t.is(action.debounceTime, 99);
  t.is(action.eventType, "click");
  t.is(action.key, "enter");
});

test("click.discard model changes", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click.discard='cancel'></button>
</div>`;
  const component = getComponent(html);
  const modelEl = component.modelEls[0].el;

  // create event and trigger it
  const inputEvent = component.document.createEvent("HTMLEvents");
  inputEvent.initEvent("input", true, true);
  modelEl.dispatchEvent(inputEvent);

  // check that the model change is in the actionQueue
  t.is(component.actionQueue.length, 1);
  t.is(component.actionQueue[0].type, "syncInput");
  t.is(component.actionQueue[0].payload.name, "name");

  // check that there are actions associated with click
  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  // check that the model change got discarded, but the cancel action is in the actionQueue
  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.type, "callMethod");
  t.is(action.payload.name, "cancel");
});

test("multiple actions", (t) => {
  const html =
    "<input unicorn:keyup.enter='add' unicorn:keydown.escape='clear'></input>";
  const element = getElement(html);

  t.true(element.actions.length === 2);
  t.true(element.actions[0].eventType === "keyup");
  t.true(element.actions[1].eventType === "keydown");
});

test("click on internal element", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test()'><span id="clicker">Click</span></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.children[0].click();

  t.is(component.actionQueue.length, 1);
});

test("$returnValue", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test($returnValue)'></button>
</div>`;
  const component = getComponent(html);
  component.return = { value: "123" };

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.payload.name, 'test("123")');
});

test("$returnValue invalid property", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test($returnValue.blob)'></button>
</div>`;
  const component = getComponent(html);
  component.return = { value: "123" };

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.payload.name, "test()");
});

test("$returnValue nested property", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test($returnValue.hello)'></button>
</div>`;
  const component = getComponent(html);
  component.return = { value: { hello: "world" } };

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.payload.name, 'test("world")');
});

test("$returnValue with method", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test($returnValue.trim())'></button>
</div>`;
  const component = getComponent(html);
  component.return = { value: " world " };

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.payload.name, 'test("world")');
});

test("$event action variable invalid property", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test($event.target.value)' value='1'></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.payload.name, 'test("1")');
});

test("$event invalid variable", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test($event.target.value.blob)' value='2'></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.payload.name, "test()");
});

test("$event action variable with method", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test($event.target.value.trim())' value=' 3 '></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.payload.name, 'test("3")');
});

test("$event action variable in middle of args", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model='name'></input>
  <button unicorn:click='test($event.target.value.trim(), 1)' value=' 4 '></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);
  const action = component.actionQueue[0];
  t.is(action.payload.name, 'test("4", 1)');
});

test("event action loading attr", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' u:loading.attr="disabled"></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  const { el } = component.actionEvents.click[0].element;
  t.true(typeof el.attributes.disabled === "undefined");

  el.click();
  t.false(typeof el.attributes.disabled === "undefined");
});

test("event action loading class", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' u:loading.class="loading"></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  const { el } = component.actionEvents.click[0].element;
  t.is(el.classList.length, 0);

  el.click();
  t.is(el.classList.length, 1);
  t.is(el.classList[0], "loading");
});

test("event action loading attr 500 reverts", async (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' u:loading.attr="disabled"></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  const { el } = component.actionEvents.click[0].element;
  t.true(typeof el.attributes.disabled === "undefined");

  el.click();
  t.false(typeof el.attributes.disabled === "undefined");

  // mock the fetch
  global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", 500);

  await send(component);

  t.true(typeof el.attributes.disabled === "undefined");
  fetchMock.reset();
});

test("event action loading class 500 reverts", async (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' u:loading.class="loading-class"></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  const { el } = component.actionEvents.click[0].element;
  t.is(el.classList.length, 0);

  el.click();
  t.is(el.classList.length, 1);
  t.is(el.classList[0], "loading-class");

  // mock the fetch
  global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", 500);

  await send(component);

  t.is(el.classList.length, 0);
  fetchMock.reset();
});

test("event action loading remove class", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' u:loading.class.remove="unloading" class="unloading"></button>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  const { el } = component.actionEvents.click[0].element;
  t.is(el.classList.length, 1);
  t.is(el.classList[0], "unloading");

  el.click();
  t.is(el.classList.length, 0);
});

test("event action loading show", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' id='testId' u:key='testKey'></button>
  <div u:loading>
  Loading
  </div>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);
  t.is(component.loadingEls.length, 1);

  const { el } = component.actionEvents.click[0].element;
  const loadingEl = component.loadingEls[0];
  t.true(loadingEl.el.hidden);

  el.click();
  t.false(loadingEl.el.hidden);
});

test("event action loading hide", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' id='testId' u:key='testKey'></button>
  <div u:loading.remove>
  Loading
  </div>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);
  t.is(component.loadingEls.length, 1);

  const { el } = component.actionEvents.click[0].element;
  const loadingEl = component.loadingEls[0];
  t.false(loadingEl.el.hidden);

  el.click();
  t.true(loadingEl.el.hidden);
});

test("event action loading by id", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' id='testId' u:key='testKey'></button>
  <div u:loading u:target='testId'>
  Loading
  </div>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);
  t.is(component.loadingEls.length, 1);

  const { el } = component.actionEvents.click[0].element;
  const loadingEl = component.loadingEls[0];
  t.true(loadingEl.el.hidden);

  el.click();
  t.false(loadingEl.el.hidden);
});

test("event action loading by key", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' id='testId' u:key='testKey'></button>
  <div u:loading u:target='testKey'>
  Loading
  </div>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);
  t.is(component.loadingEls.length, 1);

  const { el } = component.actionEvents.click[0].element;
  const loadingEl = component.loadingEls[0];
  t.true(loadingEl.el.hidden);

  el.click();
  t.false(loadingEl.el.hidden);
});

test("event action wildcard loading by id", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' id='testId-1' u:key='testKey'></button>
  <div>
    <button unicorn:click='test()' id='testId-2' u:key='testKey'></button>
  </div>
  <button unicorn:click='test()' id='testId' u:key='testKey'></button>
  <div u:loading u:target='testId-*'>
  Loading
  </div>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 3);
  t.is(component.loadingEls.length, 1);

  const el1 = component.actionEvents.click[0].element.el;
  const el2 = component.actionEvents.click[1].element.el;
  const el3 = component.actionEvents.click[2].element.el;
  const loadingEl = component.loadingEls[0];
  t.true(loadingEl.el.hidden);

  el1.click();
  t.false(loadingEl.el.hidden);

  loadingEl.el.hidden = true;
  t.true(loadingEl.el.hidden);

  el2.click();
  t.false(loadingEl.el.hidden);

  loadingEl.el.hidden = true;
  t.true(loadingEl.el.hidden);

  el3.click();
  t.true(loadingEl.el.hidden);
});

test("event action wildcard loading by key", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <button unicorn:click='test()' id='testId' u:key='testKey-1'></button>
  <div>
    <button unicorn:click='test()' id='testId' u:key='testKey-2'></button>
  </div>
  <button unicorn:click='test()' id='testId' u:key='testKey3'></button>
  <div u:loading u:target='testKey-*'>
  Loading
  </div>
</div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 3);
  t.is(component.loadingEls.length, 1);

  const el1 = component.actionEvents.click[0].element.el;
  const el2 = component.actionEvents.click[1].element.el;
  const el3 = component.actionEvents.click[2].element.el;
  const loadingEl = component.loadingEls[0];
  t.true(loadingEl.el.hidden);

  el1.click();
  t.false(loadingEl.el.hidden);

  loadingEl.el.hidden = true;
  t.true(loadingEl.el.hidden);

  el2.click();
  t.false(loadingEl.el.hidden);

  loadingEl.el.hidden = true;
  t.true(loadingEl.el.hidden);

  el3.click();
  t.true(loadingEl.el.hidden);
});
