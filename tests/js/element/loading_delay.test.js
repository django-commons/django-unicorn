import test from "ava";
import fetchMock from "fetch-mock";
import { send } from "../../../src/django_unicorn/static/unicorn/js/messageSender.js";
import { getComponent } from "../utils.js";

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

test("loading delay shows after timeout", async (t) => {
    const html = `
    <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
      <button unicorn:click='test()' u:loading.class="loading" u:loading.delay-100></button>
    </div>`;
    const component = getComponent(html);
    const { el } = component.actionEvents.click[0].element;

    // Initial state: not loading
    t.is(el.classList.length, 0);

    // Trigger click
    el.click();

    // Immediately after click: still not loading (because of delay)
    t.is(el.classList.length, 0);

    // Wait 50ms (less than 100ms): still not loading
    await delay(50);
    t.is(el.classList.length, 0);

    // Wait 100ms more (total 150ms): should be loading
    await delay(100);
    t.is(el.classList.length, 1);
    t.is(el.classList[0], "loading");
});

test("loading delay does not show if action takes less time", async (t) => {
    const html = `
    <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
      <button unicorn:click='test()' u:loading.class="loading" u:loading.delay-200></button>
    </div>`;
    const component = getComponent(html);
    const { el } = component.actionEvents.click[0].element;

    // Trigger click
    el.click();

    // Immediately after click: not loading
    t.is(el.classList.length, 0);

    // Mock fetch to return quickly (e.g. 50ms)
    // We mock a delay in the mock response using delay() inside the response if possible, 
    // or just use fetchMock delay option.
    global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", {
        body: {},
        delay: 50, // 50ms delay
    });

    // Execute send (simulating the action completing)
    // send returns a promise that resolves when the action is done
    const sendPromise = send(component);

    // Wait 100ms (total from start > 50ms response time but < 200ms loading delay)
    await delay(100);

    // loading should NOT have shown because action finished at 50ms
    // Check if class is present
    t.is(el.classList.length, 0);

    await sendPromise;
    fetchMock.reset();
});
