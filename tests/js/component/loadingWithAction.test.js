import test from "ava";
import { getComponent } from "../utils.js";

test("u:click action detected when child has u:loading", (t) => {
    const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <button unicorn:click="send_otp">
      <span unicorn:loading.remove>Send One Time Password</span>
      <span unicorn:loading>Sending...</span>
    </button>
  </div>`;
    const component = getComponent(html);

    t.false(component.actionEvents.click === undefined);
    t.is(component.actionEvents.click.length, 1);
    t.is(component.actionEvents.click[0].action.name, "send_otp");
});

test("u:click action detected when child has u:loading.class", (t) => {
    const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <button unicorn:click="send_otp">
      <span unicorn:loading.class="loading">Send One Time Password</span>
    </button>
  </div>`;
    const component = getComponent(html);

    t.false(component.actionEvents.click === undefined);
    t.is(component.actionEvents.click.length, 1);
    t.is(component.actionEvents.click[0].action.name, "send_otp");
});

test("u:click with u:loading on same element still works", (t) => {
    const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <button unicorn:click="send_otp" unicorn:loading.class="loading-wrapper">
      <span>Send One Time Password</span>
    </button>
  </div>`;
    const component = getComponent(html);

    t.false(component.actionEvents.click === undefined);
    t.is(component.actionEvents.click.length, 1);
    t.is(component.actionEvents.click[0].action.name, "send_otp");
});
