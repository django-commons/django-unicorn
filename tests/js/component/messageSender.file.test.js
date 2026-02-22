import test from "ava";
import { getComponent } from "../utils.js";
import { send } from "../../../src/django_unicorn/static/unicorn/js/messageSender.js";

function makeResponse() {
  return {
    ok: true,
    json: async () => ({
      id: "",
      dom: "",
      data: {},
      errors: {},
      redirect: {},
      return: {},
    }),
  };
}

test("send uses JSON body when no files are present", async (t) => {
  const component = getComponent();
  component.actionQueue.push({
    type: "callMethod",
    payload: { name: "save" },
  });

  let capturedOptions = null;
  global.fetch = async (_url, options) => {
    capturedOptions = options;
    return makeResponse();
  };

  await send(component);

  t.false(capturedOptions.body instanceof FormData);
  t.is(capturedOptions.headers["Content-Type"], "application/json");
});

test("send uses FormData when component.data contains a File", async (t) => {
  const file = new File(["content"], "photo.jpg", { type: "image/jpeg" });
  const component = getComponent(undefined, undefined, undefined, {
    photo: file,
  });
  component.actionQueue.push({
    type: "callMethod",
    payload: { name: "save" },
  });

  let capturedOptions = null;
  global.fetch = async (_url, options) => {
    capturedOptions = options;
    return makeResponse();
  };

  await send(component);

  t.true(capturedOptions.body instanceof FormData);
});

test("send omits Content-Type header when using FormData", async (t) => {
  const file = new File(["content"], "photo.jpg", { type: "image/jpeg" });
  const component = getComponent(undefined, undefined, undefined, {
    photo: file,
  });
  component.actionQueue.push({
    type: "callMethod",
    payload: { name: "save" },
  });

  let capturedOptions = null;
  global.fetch = async (_url, options) => {
    capturedOptions = options;
    return makeResponse();
  };

  await send(component);

  t.false("Content-Type" in capturedOptions.headers);
});

test("send uses FormData when a syncInput action payload contains a File", async (t) => {
  const file = new File(["content"], "photo.jpg", { type: "image/jpeg" });
  const component = getComponent();
  component.actionQueue.push({
    type: "syncInput",
    payload: { name: "photo", value: file },
  });

  let capturedOptions = null;
  global.fetch = async (_url, options) => {
    capturedOptions = options;
    return makeResponse();
  };

  await send(component);

  t.true(capturedOptions.body instanceof FormData);
  t.false("Content-Type" in capturedOptions.headers);
});

test("send FormData includes body field as JSON-stringified payload", async (t) => {
  const file = new File(["content"], "photo.jpg", { type: "image/jpeg" });
  const component = getComponent(undefined, undefined, undefined, {
    photo: file,
  });
  component.actionQueue.push({
    type: "callMethod",
    payload: { name: "save" },
  });

  let capturedBody = null;
  global.fetch = async (_url, options) => {
    capturedBody = options.body;
    return makeResponse();
  };

  await send(component);

  const bodyJson = capturedBody.get("body");
  t.is(typeof bodyJson, "string");

  const parsed = JSON.parse(bodyJson);
  t.is(parsed.id, component.id);
  t.truthy(parsed.actionQueue);
});

test("send FormData appends File from component.data", async (t) => {
  const file = new File(["hello"], "photo.jpg", { type: "image/jpeg" });
  const component = getComponent(undefined, undefined, undefined, {
    photo: file,
  });
  component.actionQueue.push({
    type: "callMethod",
    payload: { name: "save" },
  });

  let capturedBody = null;
  global.fetch = async (_url, options) => {
    capturedBody = options.body;
    return makeResponse();
  };

  await send(component);

  const uploadedFile = capturedBody.get("photo");
  t.true(uploadedFile instanceof File);
  t.is(uploadedFile.name, "photo.jpg");
});

test("send FormData appends File from syncInput action payload", async (t) => {
  const file = new File(["content"], "upload.pdf", { type: "application/pdf" });
  const component = getComponent();
  component.actionQueue.push({
    type: "syncInput",
    payload: { name: "document", value: file },
  });

  let capturedBody = null;
  global.fetch = async (_url, options) => {
    capturedBody = options.body;
    return makeResponse();
  };

  await send(component);

  const uploadedFile = capturedBody.get("document");
  t.true(uploadedFile instanceof File);
  t.is(uploadedFile.name, "upload.pdf");
});

test("send does not call fetch when action queue is empty", async (t) => {
  const component = getComponent();

  let fetchCalled = false;
  global.fetch = async () => {
    fetchCalled = true;
    return makeResponse();
  };

  await send(component);

  t.false(fetchCalled);
});

test("send uses JSON body when only callMethod actions with no files", async (t) => {
  const component = getComponent();
  component.actionQueue.push({
    type: "callMethod",
    payload: { name: "processData" },
  });
  component.actionQueue.push({
    type: "syncInput",
    payload: { name: "name", value: "hello" },
  });

  let capturedOptions = null;
  global.fetch = async (_url, options) => {
    capturedOptions = options;
    return makeResponse();
  };

  await send(component);

  t.false(capturedOptions.body instanceof FormData);
  t.is(capturedOptions.headers["Content-Type"], "application/json");
});
