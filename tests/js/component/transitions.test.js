import test from "ava";
import { JSDOM } from "jsdom";
import { Transition } from "../../../src/django_unicorn/static/unicorn/js/transition.js";
import { MorphdomMorpher } from "../../../src/django_unicorn/static/unicorn/js/morphers/morphdom.js";

/**
 * Setup a fresh JSDOM environment for each test.
 */
test.beforeEach((t) => {
    const dom = new JSDOM('<!DOCTYPE html><div id="test"></div>');
    global.window = dom.window;
    global.document = dom.window.document;
    global.Node = dom.window.Node;

    // Mock requestAnimationFrame to run synchronously for testing
    global.requestAnimationFrame = (cb) => {
        cb();
        return 1;
    };

    // Mock getAnimations with a way to simulate completion
    global.Node.prototype.getAnimations = function () {
        // Return a mocked animation object that resolves its 'finished' promise
        return [
            {
                finished: Promise.resolve(),
            },
        ];
    };
});

/**
 * Helper to check if an element has EXACTLY the expected classes.
 */
const assertClasses = (t, el, expected) => {
    const actual = Array.from(el.classList);
    t.deepEqual(actual.sort(), expected.sort(), `Expected classes ${expected} but found ${actual}`);
};

// --- Unit Tests for Transition ---

test.serial("Transition.run applies and removes classes correctly", async (t) => {
    const el = document.getElementById("test");
    el.setAttribute("u:transition:enter", "base");
    el.setAttribute("u:transition:enter-start", "start");
    el.setAttribute("u:transition:enter-end", "end");

    // We can't easily test the mid-state since we mocked rAF to be sync,
    // so we verify the final state and the logic flow.
    await Transition.run(el, "enter");

    assertClasses(t, el, []);
});

test.serial("Transition.run handles multiple classes", async (t) => {
    const el = document.getElementById("test");
    el.setAttribute("u:transition:leave", "leave-base-1 leave-base-2");
    el.setAttribute("u:transition:leave-start", "start-1 start-2");
    el.setAttribute("u:transition:leave-end", "end-1 end-2");

    await Transition.run(el, "leave");

    assertClasses(t, el, []);
});

test.serial("Transition.run handles 'unicorn:' prefix", async (t) => {
    const el = document.getElementById("test");
    el.setAttribute("unicorn:transition:enter", "base");
    el.setAttribute("unicorn:transition:enter-start", "start");

    await Transition.run(el, "enter");

    assertClasses(t, el, []);
});

test.serial("Transition.run is resilient to missing attributes", async (t) => {
    const el = document.getElementById("test");
    // No attributes set at all
    await Transition.run(el, "enter");
    t.pass();
});

test.serial("Transition.run is resilient to empty attributes", async (t) => {
    const el = document.getElementById("test");
    el.setAttribute("u:transition:enter", "");
    await Transition.run(el, "enter");
    t.pass();
});

// --- Integration Tests for MorphdomMorpher ---

test.serial("Morpher includes Transition.enter in onNodeAdded", (t) => {
    const morpher = new MorphdomMorpher({});
    const options = morpher.getOptions();
    const el = document.createElement("div");
    el.setAttribute("u:transition:enter", "fade");

    let called = false;
    const originalEnter = Transition.enter;
    Transition.enter = (node) => {
        called = true;
        t.is(node, el);
    };

    options.onNodeAdded(el);
    t.true(called, "Transition.enter should have been called");

    Transition.enter = originalEnter;
});

test.serial("Morpher onBeforeNodeDiscarded prevents immediate removal IF transition exists", (t) => {
    const morpher = new MorphdomMorpher({});
    const options = morpher.getOptions();
    const el = document.createElement("div");
    el.setAttribute("u:transition:leave", "fade");

    const result = options.onBeforeNodeDiscarded(el);
    t.false(result, "Should return false to prevent immediate removal");
});

test.serial("Morpher onBeforeNodeDiscarded allows immediate removal IF NO transition exists", (t) => {
    const morpher = new MorphdomMorpher({});
    const options = morpher.getOptions();
    const el = document.createElement("div");

    const result = options.onBeforeNodeDiscarded(el);
    t.true(result, "Should return true to allow immediate removal");
});

test.serial("Morpher onBeforeNodeDiscarded removes node AFTER leave transition finishes", async (t) => {
    const morpher = new MorphdomMorpher({});
    const options = morpher.getOptions();

    // Setup a parent to check removal
    const parent = document.createElement("div");
    const el = document.createElement("div");
    el.setAttribute("u:transition:leave", "fade");
    parent.appendChild(el);

    // Mock Transition.leave to be trackable
    let leaveFinished = false;
    const originalLeave = Transition.leave;
    Transition.leave = async () => {
        await Promise.resolve(); // simulate some async work
        leaveFinished = true;
    };

    options.onBeforeNodeDiscarded(el);

    // Wait for the .then() in the actual implementation to fire
    await new Promise(resolve => setTimeout(resolve, 10));

    t.true(leaveFinished);
    t.is(parent.childNodes.length, 0, "Node should have been removed from DOM");

    Transition.leave = originalLeave;
});
