import test from "ava";
import fetchMock from "fetch-mock";
import { getComponent } from "../utils.js";

// Needs to be serial because we are mocking global fetch
test.serial("keyup.debounce should not fire immediately", async (t) => {
    const html = `
  <div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
    <input unicorn:keyup.debounce-100='test()'></input>
  </div>`;
    const component = getComponent(html);
    const input = component.root.querySelector("input");

    // Mock fetch
    const mockFetch = fetchMock.sandbox().mock("begin:test/text-inputs", 200).mock("begin:/test/text-inputs", 200);
    global.fetch = mockFetch;

    // Trigger keyup event
    input.dispatchEvent(new input.ownerDocument.defaultView.Event("keyup", { bubbles: true }));

    // Check immediately - should be 0 calls
    t.is(mockFetch.calls().length, 0, "Should not have fired yet");

    // Wait a bit, but less than debounce time
    await new Promise((r) => setTimeout(r, 50));

    // Trigger another keyup
    input.dispatchEvent(new input.ownerDocument.defaultView.Event("keyup", { bubbles: true }));

    // Wait remaining time for first event (total 100ms from start), 
    // but since we triggered again at 50ms, timer should reset and not fire at 100ms
    await new Promise((r) => setTimeout(r, 60)); // Total 110ms from start

    // Still should be 0
    t.is(mockFetch.calls().length, 0, "Should still be waiting (debouncing)");

    // Wait for the second debounce to complete (needs another 40ms, so let's wait 100ms to be safe)
    await new Promise((r) => setTimeout(r, 100));

    // Should have fired ONCE
    t.is(mockFetch.calls().length, 1, "Should have fired once");

    mockFetch.reset();
});
