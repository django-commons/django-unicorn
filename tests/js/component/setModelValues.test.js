import test from "ava";
import { getComponent } from "../utils.js";

test("setModelValues setValue called", (t) => {
  t.plan(4);

  const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input u:model='name'></input>
  </div>`;
  const component = getComponent(html);

  t.is(component.modelEls.length, 1);

  let setValueCalled = false;
  let elementSet = null;

  component.setValue = (element) => {
    t.pass();
    setValueCalled = true;
    elementSet = element;
  };

  const triggeringElements = [];
  const forceModelUpdates = false;
  component.setModelValues(triggeringElements, forceModelUpdates);

  t.true(setValueCalled);
  t.is(elementSet, component.modelEls[0]);
});

test("setModelValues triggeringElement setValue not called", (t) => {
  t.plan(3);

  const html = `
    <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
      <input u:model='name'></input>
    </div>`;
  const component = getComponent(html);

  t.is(component.modelEls.length, 1);

  let setValueCalled = false;
  let elementSet = null;

  component.setValue = (element) => {
    t.pass();
    setValueCalled = true;
    elementSet = element;
  };

  const triggeringElements = [component.modelEls[0]];
  const forceModelUpdates = false;
  component.setModelValues(triggeringElements, forceModelUpdates);

  t.false(setValueCalled);
  t.is(elementSet, null);
});

test("setModelValues triggeringElement forceModelUpdates setValue called", (t) => {
  t.plan(4);

  const html = `
      <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
        <input u:model='name'></input>
      </div>`;
  const component = getComponent(html);

  t.is(component.modelEls.length, 1);

  let setValueCalled = false;
  let elementSet = null;

  component.setValue = (element) => {
    t.pass();
    setValueCalled = true;
    elementSet = element;
  };

  const triggeringElements = [component.modelEls[0]];
  const forceModelUpdates = true;
  component.setModelValues(triggeringElements, forceModelUpdates);

  t.true(setValueCalled);
  t.is(elementSet, component.modelEls[0]);
});

test("setModelValues multiple models setValue called once", (t) => {
  t.plan(2);

  const html = `
        <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
          <input u:model='name'></input>
          <input u:model='blob'></input>
        </div>`;
  const component = getComponent(html);

  t.is(component.modelEls.length, 2);

  component.setValue = (_) => {
    t.pass();
  };

  const triggeringElements = [component.modelEls[0]];
  const forceModelUpdates = false;
  component.setModelValues(triggeringElements, forceModelUpdates);
});
