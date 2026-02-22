import test from "ava";
import morphdom from "../../../src/django_unicorn/static/unicorn/js/morphdom/2.6.1/morphdom.js";
import { getEl } from "../utils.js";

test("contains", (t) => {
  const componentRootHtml = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model="name" type="text" id="name"><br />
  Name: 
</div>
  `;
  const componentRoot = getEl(componentRootHtml);

  const rerenderedComponentHtml = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model="name" type="text" id="name"><br />
  Name: Test
</div>
  `;
  const rerenderedComponent = getEl(rerenderedComponentHtml);

  t.true(componentRoot.outerHTML.indexOf("Name: Test") === -1);
  morphdom(componentRoot, rerenderedComponent);
  t.true(componentRoot.outerHTML.indexOf("Name: Test") > -1);
});

test("ignore element", (t) => {
  const componentRootHtml = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model="name" type="text" id="name"><br />
  Name: 

  <div unicorn:ignore>
    Something here
  </div>
</div>
  `;
  const componentRoot = getEl(componentRootHtml);

  const rerenderedComponentHtml = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model="name" type="text" id="name"><br />
  Name: Test

  <div unicorn:ignore>
    Something else here
  </div>
</div>
  `;
  const rerenderedComponent = getEl(rerenderedComponentHtml);

  t.true(componentRoot.outerHTML.indexOf("Name: Test") === -1);
  t.true(componentRoot.outerHTML.indexOf("Something here") > -1);

  morphdom(componentRoot, rerenderedComponent);

  t.true(componentRoot.outerHTML.indexOf("Name: Test") > -1);
  t.true(componentRoot.outerHTML.indexOf("Something here") > -1);
});

test("ignore all children elements", (t) => {
  const componentRootHtml = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model="name" type="text" id="name"><br />
  Name: 

  <div unicorn:ignore>
    <div>
      Something here
    </div>
    <div>
      More here
    </div>
  </div>
</div>
  `;
  const componentRoot = getEl(componentRootHtml);

  const rerenderedComponentHtml = `
<div unicorn:id="5jypjiyb" unicorn:name="text-inputs" unicorn:meta="GXzew3Km">
  <input unicorn:model="name" type="text" id="name"><br />
  Name: Test

  <div unicorn:ignore>
    <div>
      Something else here
    </div>
    <div>
      More else here
    </div>
  </div>
</div>
  `;
  const rerenderedComponent = getEl(rerenderedComponentHtml);

  t.true(componentRoot.outerHTML.indexOf("Name: Test") === -1);
  t.true(componentRoot.outerHTML.indexOf("Something here") > -1);
  t.true(componentRoot.outerHTML.indexOf("More here") > -1);

  morphdom(componentRoot, rerenderedComponent);

  t.true(componentRoot.outerHTML.indexOf("Name: Test") > -1);
  t.true(componentRoot.outerHTML.indexOf("Something here") > -1);
  t.true(componentRoot.outerHTML.indexOf("More here") > -1);
});
