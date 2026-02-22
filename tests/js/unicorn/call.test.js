import test from "ava";
import { call } from "../../../src/django_unicorn/static/unicorn/js/unicorn.js";
import { components } from "../../../src/django_unicorn/static/unicorn/js/store.js";
import { getComponent } from "../utils.js";

test("call triggers loading show", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
  <div u:loading>Loading</div>
</div>`;
  const component = getComponent(html);
  components[component.id] = component;
  component.callMethod = () => {};

  t.is(component.loadingEls.length, 1);
  const loadingEl = component.loadingEls[0];
  t.true(loadingEl.el.hidden);

  call("text-inputs", "testMethod");
  t.false(loadingEl.el.hidden);
});

test("call triggers loading hide", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
  <div u:loading.remove>Loading</div>
</div>`;
  const component = getComponent(html);
  components[component.id] = component;
  component.callMethod = () => {};

  t.is(component.loadingEls.length, 1);
  const loadingEl = component.loadingEls[0];
  t.false(loadingEl.el.hidden);

  call("text-inputs", "testMethod");
  t.true(loadingEl.el.hidden);
});

test("call triggers loading class", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
  <div u:loading.class="loading">Loading</div>
</div>`;
  const component = getComponent(html);
  components[component.id] = component;
  component.callMethod = () => {};

  t.is(component.loadingEls.length, 1);
  const loadingEl = component.loadingEls[0];
  t.is(loadingEl.el.classList.length, 0);

  call("text-inputs", "testMethod");
  t.is(loadingEl.el.classList.length, 1);
  t.is(loadingEl.el.classList[0], "loading");
});

test("call triggers loading attr", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
  <button u:loading.attr="disabled">Submit</button>
</div>`;
  const component = getComponent(html);
  components[component.id] = component;
  component.callMethod = () => {};

  t.is(component.loadingEls.length, 1);
  const loadingEl = component.loadingEls[0];
  t.true(typeof loadingEl.el.attributes.disabled === "undefined");

  call("text-inputs", "testMethod");
  t.false(typeof loadingEl.el.attributes.disabled === "undefined");
});

test("call does not trigger targeted loading element", (t) => {
  const html = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
  <button id="myBtn" unicorn:click="test()">Click</button>
  <div u:loading u:target="myBtn">Loading</div>
</div>`;
  const component = getComponent(html);
  components[component.id] = component;
  component.callMethod = () => {};

  t.is(component.loadingEls.length, 1);
  const loadingEl = component.loadingEls[0];
  t.true(loadingEl.el.hidden);

  call("text-inputs", "testMethod");
  t.true(loadingEl.el.hidden);
});

test("call a method", (t) => {
  const component = getComponent();
  components[component.id] = component;

  component.callMethod = (methodName) => {
    t.true(methodName === "testMethod");
  };

  call("text-inputs", "testMethod");
});

test("call a method with string argument", (t) => {
  const component = getComponent();
  components[component.id] = component;

  component.callMethod = (methodName) => {
    t.true(methodName === "testMethod('test1')");
  };

  call("text-inputs", "testMethod", "test1");
});

test("call a method with string and int argument", (t) => {
  const component = getComponent();
  components[component.id] = component;

  component.callMethod = (methodName) => {
    t.true(methodName === "testMethod('test1', 2)");
  };

  call("text-inputs", "testMethod", "test1", 2);
});

test("call a method with string containing single quotes", (t) => {
  const component = getComponent();
  components[component.id] = component;

  component.callMethod = (methodName) => {
    t.true(methodName === "testMethod('It\\'s a test')");
  };

  call("text-inputs", "testMethod", "It's a test");
});

test("call a method with string containing double quotes", (t) => {
  const component = getComponent();
  components[component.id] = component;

  component.callMethod = (methodName) => {
    t.true(methodName === 'testMethod(\'He said "hello"\')');
  };

  call("text-inputs", "testMethod", 'He said "hello"');
});

test("call a method with string containing backslashes", (t) => {
  const component = getComponent();
  components[component.id] = component;

  component.callMethod = (methodName) => {
    t.true(methodName === "testMethod('C:\\\\Users\\\\test')");
  };

  call("text-inputs", "testMethod", "C:\\Users\\test");
});

test("call a method with complex chemical name (issue #607)", (t) => {
  const component = getComponent();
  components[component.id] = component;

  const chemicalName = "Chloro(2-dicyclohexylphosphino-3,6-dimethoxy-2',4',6'-tri-i-propyl-1,1'-biphenyl)(2'-amino-1,1'-biphenyl-2-yl)palladium(II)";

  component.callMethod = (methodName) => {
    t.true(methodName === `testMethod('Chloro(2-dicyclohexylphosphino-3,6-dimethoxy-2\\',4\\',6\\'-tri-i-propyl-1,1\\'-biphenyl)(2\\'-amino-1,1\\'-biphenyl-2-yl)palladium(II)')`);
  };

  call("text-inputs", "testMethod", chemicalName);
});

test("call a method with string containing both quotes and parentheses", (t) => {
  const component = getComponent();
  components[component.id] = component;

  component.callMethod = (methodName) => {
    t.true(methodName === "testMethod('test(with \\'quotes\\' and \"double\")')");
  };

  call("text-inputs", "testMethod", "test(with 'quotes' and \"double\")");
});

