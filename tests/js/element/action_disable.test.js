import test from "ava";
import { getComponent } from "../utils.js";

test("action disable modifier", async (t) => {
  const html = `
    <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
      <button unicorn:click.disable="test()"></button>
    </div>
  `;
  const component = getComponent(html);
  const button = component.root.querySelector("button");

  // 1. Initial state: Enabled
  t.false(button.hasAttribute("disabled"));

  const MouseEvent = component.document.defaultView.MouseEvent;
  const event = new MouseEvent("click", {
    bubbles: true,
    cancelable: true,
    view: component.document.defaultView,
  });

  // 2. Click: Should become disabled immediately
  button.dispatchEvent(event);
  t.true(button.disabled);

  // 3. Wait for debounce (0ms) + fetch (async) to complete
  // We can use a short timeout to let the event loop process the fetch
  await new Promise(resolve => setTimeout(resolve, 10));

  // 4. Final state: Should be enabled again
  t.false(button.disabled);
});

test("action disable modifier with error", async (t) => {
  const html = `
      <div unicorn:id="error-test" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
        <button unicorn:click.disable="test()"></button>
      </div>
    `;
  const component = getComponent(html, "error-test");
  const button = component.root.querySelector("button");

  global.fetch.post("/test/error-input", 500);
  component.syncUrl = "/test/error-input";

  const MouseEvent = component.document.defaultView.MouseEvent;
  button.dispatchEvent(new MouseEvent("click", {
    bubbles: true,
    view: component.document.defaultView
  }));

  t.true(button.disabled);

  await new Promise(resolve => setTimeout(resolve, 20));

  t.false(button.disabled);
});
