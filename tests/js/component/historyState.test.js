import test from "ava";
import { getComponent } from "../utils.js";

const html = `
<input type="hidden" name="csrfmiddlewaretoken" value="asdf">
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <input unicorn:model='name'></input>
    <button unicorn:click='test()'><span id="clicker">Click</span></button>
</div>
`;

test("popstate listener is registered on window", (t) => {
    const component = getComponent(html);

    // The initHistoryState() call should have registered a popstate listener
    t.truthy(component._windowEventListeners["popstate"]);
    t.is(component._windowEventListeners["popstate"].length, 1);
});

test("popstate ignores events with no unicorn state", (t) => {
    const component = getComponent(html);

    // Fire a popstate event with no state — should not trigger any refresh
    const listeners = component._windowEventListeners["popstate"];
    t.truthy(listeners);

    // actionQueue should be empty before and after
    t.is(component.actionQueue.length, 0);

    listeners[0]({ state: null });
    t.is(component.actionQueue.length, 0);
});

test("popstate ignores events with non-matching component id", (t) => {
    const component = getComponent(html);
    const listeners = component._windowEventListeners["popstate"];

    t.is(component.actionQueue.length, 0);

    // Fire with a different componentId — should be ignored
    listeners[0]({
        state: {
            unicorn: {
                componentId: "different-id",
                data: { name: "OldValue" },
            },
        },
    });

    t.is(component.actionQueue.length, 0);
});

test("popstate restores data and triggers refresh for matching component", (t) => {
    const component = getComponent(html);
    const listeners = component._windowEventListeners["popstate"];

    // Spy on callMethod so we can verify $refresh is called without needing
    // a working HTTP endpoint
    const calledMethods = [];
    component.callMethod = (methodName) => {
        calledMethods.push(methodName);
    };

    const previousData = { name: "PreviousName" };

    // Fire popstate with a matching componentId and stored previous state
    listeners[0]({
        state: {
            unicorn: {
                componentId: component.id,
                data: previousData,
            },
        },
    });

    // The stored data should have been merged back into the component
    t.is(component.data.name, "PreviousName");

    // $refresh should have been called to trigger a server re-render
    t.is(calledMethods.length, 1);
    t.is(calledMethods[0], "$refresh");
});
