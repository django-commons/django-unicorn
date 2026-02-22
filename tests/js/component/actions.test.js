import test from "ava";
import { getComponent } from "../utils.js";
import { isEmpty } from "../../../src/django_unicorn/static/unicorn/js/utils.js";

test("action", (t) => {
  const component = getComponent();

  t.is(component.attachedEventTypes.length, 1);
  t.false(isEmpty(component.actionEvents));
  t.is(component.actionEvents.click.length, 1);
});

test("multiple of same action eventType", (t) => {
  const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input unicorn:model='name'></input>
    <button unicorn:click='name="world"'></button>
    <button unicorn:click='name="hello"'></button>
  </div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.false(isEmpty(component.actionEvents));
  t.is(component.actionEvents.click.length, 2);
});

test("multiple action eventTypes", (t) => {
  const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input unicorn:model='name'></input>
    <button unicorn:click='name="world"'></button>
    <button unicorn:keyup='name="hello"'></button>
  </div>`;
  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 2);
  t.false(isEmpty(component.actionEvents));
  t.is(component.actionEvents.click.length, 1);
  t.is(component.actionEvents.keyup.length, 1);
});
