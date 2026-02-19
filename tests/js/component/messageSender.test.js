import test from "ava";
import fetchMock from "fetch-mock";
import { getComponent } from "../utils.js";
import { send } from "../../../src/django_unicorn/static/unicorn/js/messageSender.js";

test("call_method redirect", async (t) => {
  const html = `
<input type="hidden" name="csrfmiddlewaretoken" value="asdf">
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <input unicorn:model='name'></input>
    <button unicorn:click='test()'><span id="clicker">Click</span></button>
</div>
  `;

  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);

  // mock the fetch
  const res = {
    id: "aQzrrRoG",
    dom: "",
    data: {
      name: "World",
    },
    errors: {},
    redirect: { url: "http://www.google.com" },
    return: {},
  };
  global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", res);

  await send(component);

  t.is(component.window.location.href, "http://www.google.com");
  fetchMock.reset();
});

test("call_method refresh redirect", async (t) => {
  const html = `
<input type="hidden" name="csrfmiddlewaretoken" value="asdf">
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <input unicorn:model='name'></input>
    <button unicorn:click='test()'><span id="clicker">Click</span></button>
</div>
  `;

  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);

  // mock the fetch
  const res = {
    id: "aQzrrRoG",
    dom: "",
    data: {
      name: "World",
    },
    errors: {},
    redirect: {
      url: "/test/text-inputs?some=query",
      refresh: true,
      title: "new title",
    },
    return: {},
  };
  global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", res);

  await new Promise((resolve) => {
    send(component, (a, b, err) => {
      t.true(err === null);
      t.is(component.window.history.get(), "/test/text-inputs?some=query");
      t.is(component.window.document.title, "new title");

      // The history state should contain the component id and data
      const state = component.window.history.getState();
      t.truthy(state.unicorn);
      t.is(state.unicorn.componentId, component.id);
      t.deepEqual(state.unicorn.data, component.data);

      fetchMock.reset();
      resolve();
    });
  });
});

test("call_method hash", async (t) => {
  const html = `
<input type="hidden" name="csrfmiddlewaretoken" value="asdf">
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <input unicorn:model='name'></input>
    <button unicorn:click='test()'><span id="clicker">Click</span></button>
</div>
  `;

  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);

  // mock the fetch
  const res = {
    id: "aQzrrRoG",
    dom: "",
    data: {
      name: "World",
    },
    errors: {},
    redirect: {
      hash: "#somehash",
    },
    return: {},
  };
  global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", res);

  await new Promise((resolve) => {
    send(component, (a, b, err) => {
      t.true(err === null);
      t.is(component.window.location.hash, "#somehash");
      fetchMock.reset();
      resolve();
    });
  });
});

test("call_method forceModelUpdate is true", async (t) => {
  const html = `
<input type="hidden" name="csrfmiddlewaretoken" value="asdf">
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <input unicorn:model='name'></input>
    <button unicorn:click='test()'><span id="clicker">Click</span></button>
</div>
  `;

  const component = getComponent(html);

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);

  // mock the fetch
  const res = {
    id: "aQzrrRoG",
    dom: "blob",
    data: {
      name: "World",
    },
    errors: {},
    redirect: {},
    return: {},
  };
  global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", res);

  await new Promise((resolve) => {
    send(component, (a, forceModelUpdates, err) => {
      t.true(err === null);
      t.true(forceModelUpdates);
      fetchMock.reset();
      resolve();
    });
  });
});

test("call_method partial.id", async (t) => {
  // Annoyingly it appears that $('[unicorn\\:key='something']) doesn't
  // seem to work in JSDom, so this just tests targeting by id
  const html = `
<input type="hidden" name="csrfmiddlewaretoken" value="asdf">
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <input unicorn:model='name'></input>
    <span id="clicker-id">Click</span>
    <button unicorn:click='test()' u:partial.id='clicker-id'>Click</button>
</div>
  `;

  const component = getComponent(html);
  let morphdomCount = 0;
  const morphdomMergers = [];
  component.morpher.morph = (initial, merger, ___) => {
    morphdomCount += 1;
    morphdomMergers.push(merger);
  };

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();

  t.is(component.actionQueue.length, 1);

  // mock the fetch
  const res = {
    id: "aQzrrRoG",
    partials: [
      { id: "clicker-id", dom: "<span id='clicker-id'>id partial!</span>" },
    ],
    data: {
      name: "World",
    },
    errors: {},
    redirect: {},
    return: {},
  };
  global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", res);

  await new Promise((resolve) => {
    send(component, (a, forceModelUpdates, err) => {
      t.true(err === null);
      t.is(morphdomCount, 1);
      t.is(morphdomMergers.length, 1);
      t.is(morphdomMergers[0], "<span id='clicker-id'>id partial!</span>");
      fetchMock.reset();
      resolve();
    });
  });
});

test("call_method partial target", async (t) => {
  // Annoyingly it appears that $('[unicorn\\:key='something']) doesn't
  // seem to work in JSDom, so this just tests targeting by id
  const html = `
<input type="hidden" name="csrfmiddlewaretoken" value="asdf">
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:checksum="GXzew3Km">
    <input unicorn:model='name'></input>
    <span id="clicker-id">Click</span>
    <button unicorn:click='test()' u:partial='clicker-id'>Click</button>
</div>
  `;

  const component = getComponent(html);
  let morphdomCount = 0;
  const morphdomMergers = [];
  component.morpher.morph = (initial, merger, ___) => {
    morphdomCount += 1;
    morphdomMergers.push(merger);
  };

  t.is(component.attachedEventTypes.length, 1);
  t.is(component.actionEvents.click.length, 1);

  component.actionEvents.click[0].element.el.click();
  t.is(component.actionQueue.length, 1);

  // mock the fetch
  const res = {
    id: "aQzrrRoG",
    partials: [
      { id: "clicker-id", dom: "<span id='clicker-id'>id partial!</span>" },
    ],
    data: {
      name: "World",
    },
    errors: {},
    redirect: {},
    return: {},
  };
  global.fetch = fetchMock.sandbox().mock().post("/test/text-inputs", res);

  await new Promise((resolve) => {
    send(component, (a, forceModelUpdates, err) => {
      t.true(err === null);
      t.is(morphdomCount, 1);
      t.is(morphdomMergers.length, 1);
      t.is(morphdomMergers[0], "<span id='clicker-id'>id partial!</span>");
      fetchMock.reset();
      resolve();
    });
  });
});
