import test from "ava";
import { getComponent } from "../utils.js";

test("unicorn:id", (t) => {
  const component = getComponent();

  t.true(component.root != null);
  t.is(component.id, "5jypjiyb");
});

test("unicorn:name", (t) => {
  const component = getComponent();

  t.is(component.name, "text-inputs");
});

test("unicorn:meta", (t) => {
  const component = getComponent();

  t.is(component.checksum, "GXzew3Km");
});

test("component on non-div", (t) => {
  const html = `
  <span unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  </span>`;
  const component = getComponent(html);

  t.is(component.root.attributes.length, 3);
  t.is(component.id, "5jypjiyb");
  t.is(component.checksum, "GXzew3Km");
});
