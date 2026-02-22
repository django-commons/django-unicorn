
import test from "ava";
import fetchMock from "fetch-mock";
import { getComponent } from "../utils.js";
import { send } from "../../../src/django_unicorn/static/unicorn/js/messageSender.js";

test("race condition: later response overwrites newer one", async (t) => {
    const html = `
<input type="hidden" name="csrfmiddlewaretoken" value="asdf">
<div unicorn:id="race-condition-id" unicorn:name="race-condition" unicorn:checksum="checksum">
    <input unicorn:model='name'></input>
</div>
  `;

    const component = getComponent(html, "race-condition-id", "race-condition");

    // Set initial data
    component.data.name = "";

    // Queue first action "a"
    const action1 = {
        type: "syncInput",
        payload: { name: "name", value: "a" },
    };
    component.actionQueue.push(action1);

    // Mock fetch for first request (slow)
    const res1 = {
        id: "race-condition-id",
        data: { name: "a" },
        errors: {},
        return: {},
        epoch: Date.now() + 1000,
    };

    // Create a promise to control when the first response resolves
    let resolveReq1;
    const req1Promise = new Promise((resolve) => {
        resolveReq1 = resolve;
    });

    const sandbox = fetchMock.sandbox();
    global.fetch = sandbox;

    sandbox.postOnce("/test/race-condition", req1Promise.then(() => res1));

    // Send first request
    const send1 = send(component);

    // Queue second action "ab"
    const action2 = {
        type: "syncInput",
        payload: { name: "name", value: "ab" },
    };
    component.actionQueue.push(action2);

    // Mock fetch for second request (fast)
    const res2 = {
        id: "race-condition-id",
        data: { name: "ab" }, // This is the newer state
        errors: {},
        return: {},
        epoch: Date.now() + 2000,
    };

    sandbox.postOnce("/test/race-condition", res2, { overwriteRoutes: false });

    // Send second request
    const send2 = send(component);

    // Wait for send2 to complete (it should use the fast response)
    await send2;

    // At this point, component.data.name should be "ab"
    t.is(component.data.name, "ab");

    // Now resolve the first request (the slow one)
    resolveReq1();
    await send1;

    // WITHOUT FIX: component.data.name will be "a" (stale)
    // WITH FIX: component.data.name should still be "ab"
    t.is(component.data.name, "ab", "Stale response overwrote newer state");

    fetchMock.reset();
});
