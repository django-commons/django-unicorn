import test from "ava";
import { getElement } from "../utils.js";

test("file input captures accept attribute in file property", (t) => {
  const html = "<input unicorn:model='photo' type='file' accept='image/*'></input>";
  const element = getElement(html);

  t.is(element.file.accept, "image/*");
});

test("file input captures multiple=true when multiple attribute is present", (t) => {
  const html = "<input unicorn:model='photo' type='file' multiple></input>";
  const element = getElement(html);

  t.true(element.file.multiple);
});

test("file input captures multiple=false when multiple attribute is absent", (t) => {
  const html = "<input unicorn:model='photo' type='file'></input>";
  const element = getElement(html);

  t.false(element.file.multiple);
});

test("file input accept defaults to empty string when accept attribute is absent", (t) => {
  const html = "<input unicorn:model='photo' type='file'></input>";
  const element = getElement(html);

  t.is(element.file.accept, "");
});

test("file input sets both accept and multiple from attributes", (t) => {
  const html =
    "<input unicorn:model='docs' type='file' accept='.pdf,.doc' multiple></input>";
  const element = getElement(html);

  t.is(element.file.accept, ".pdf,.doc");
  t.true(element.file.multiple);
});

test("text input has empty file property", (t) => {
  const html = "<input unicorn:model='name' type='text'></input>";
  const element = getElement(html);

  t.deepEqual(element.file, {});
});

test("file input without unicorn model has empty file property", (t) => {
  const html = "<input type='file' accept='image/*'></input>";
  const element = getElement(html);

  t.deepEqual(element.file, {});
});

test("file input getValue() returns the el.files property", (t) => {
  const html = "<input unicorn:model='photo' type='file'></input>";
  const element = getElement(html);

  // In JSDOM, el.files is an empty FileList (not null)
  t.is(element.getValue(), element.el.files);
});
