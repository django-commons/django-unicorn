import test from "ava";
import { getComponent } from "../utils.js";

class Event {
  constructor(type) {
    this.type = type;
  }
}
global.Event = Event;

test("modelEls", (t) => {
  const component = getComponent();

  t.is(component.modelEls.length, 1);
});

test("abbreviated name", (t) => {
  const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input u:model='name'></input>
  </div>`;
  const component = getComponent(html);

  t.is(component.modelEls.length, 1);
});

test("model.lazy has input and blur events", (t) => {
  const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input u:model.lazy='name'></input>
  </div>`;
  const component = getComponent(html);

  t.is(component.modelEls.length, 1);

  const element = component.modelEls[0];

  t.is(element.events.length, 2);
});

test("model trigger with invalid key", (t) => {
  t.plan(0);

  const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input u:model.lazy='name' u:key='nameKey'></input>
  </div>`;
  const component = getComponent(html);
  const element = component.modelEls[0];

  element.el.dispatchEvent = () => {
    t.pass();
  };

  component.trigger("invalidNameKey");
});

test("model.lazy trigger", (t) => {
  t.plan(1);

  const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input u:model.lazy='name' u:key='nameKey'></input>
  </div>`;
  const component = getComponent(html);
  const element = component.modelEls[0];

  element.el.dispatchEvent = (event) => {
    t.true(event.type === "blur");
  };

  component.trigger("nameKey");
});

test("model trigger", (t) => {
  t.plan(1);

  const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input u:model='name' u:key='nameKey'></input>
  </div>`;
  const component = getComponent(html);
  const element = component.modelEls[0];

  element.el.dispatchEvent = (event) => {
    t.true(event.type === "input");
  };

  component.trigger("nameKey");
});
