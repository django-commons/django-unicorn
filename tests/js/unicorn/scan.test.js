import test from "ava";
import { JSDOM } from "jsdom";
import { scan, init } from "../../../src/django_unicorn/static/unicorn/js/unicorn.js";
import { components } from "../../../src/django_unicorn/static/unicorn/js/store.js";

test.beforeEach(() => {
    const dom = new JSDOM('<!doctype html><html><body></body></html>');
    global.document = dom.window.document;
    global.window = dom.window;
    global.MutationObserver = dom.window.MutationObserver;
    global.Node = dom.window.Node;
    global.NodeFilter = dom.window.NodeFilter;

    // Clear components
    for (const key in components) {
        delete components[key];
    }
});

test.afterEach(() => {
    delete global.document;
    delete global.window;
    delete global.MutationObserver;
    delete global.Node;
});

test("scan initializes component from dom", (t) => {
    const componentRoot = document.createElement("div");
    componentRoot.setAttribute("unicorn:id", "test-scan-id");
    componentRoot.setAttribute("unicorn:name", "test-name");
    componentRoot.setAttribute("unicorn:key", "test-key");
    componentRoot.setAttribute("unicorn:meta", "test-checksum");
    componentRoot.setAttribute("unicorn:data", "{}");
    componentRoot.setAttribute("unicorn:calls", "[]");
    document.body.appendChild(componentRoot);

    scan();

    t.truthy(components["test-scan-id"]);
});

test("init observes document automatically", async (t) => {
    init("unicorn/", "X-Unicorn", "unicorn", { NAME: "morphdom" });

    const componentRoot = document.createElement("div");
    componentRoot.setAttribute("unicorn:id", "test-auto-id");
    componentRoot.setAttribute("unicorn:name", "test-name");
    componentRoot.setAttribute("unicorn:key", "test-key");
    componentRoot.setAttribute("unicorn:meta", "test-checksum");
    componentRoot.setAttribute("unicorn:data", "{}");
    componentRoot.setAttribute("unicorn:calls", "[]");

    document.body.appendChild(componentRoot);

    // Wait for MutationObserver (microtask/macrotask)
    await new Promise(resolve => setTimeout(resolve, 50));

    t.truthy(components["test-auto-id"]);
});
