import { Component } from "./component.js";
import { isEmpty, hasValue } from "./utils.js";
import { components, lifecycleEvents } from "./store.js";
import { getMorpher } from "./morpher.js";

let messageUrl = "";
let csrfTokenHeaderName = "X-CSRFToken";
let csrfTokenCookieName = "csrftoken";
let morpher;

/**
 * Initializes the Unicorn object.
 *
 * @typedef
 */
export function init(
  _messageUrl,
  _csrfTokenHeaderName,
  _csrfTokenCookieName,
  _morpherSettings
) {
  messageUrl = _messageUrl;

  morpher = getMorpher(_morpherSettings);

  if (hasValue(_csrfTokenHeaderName)) {
    csrfTokenHeaderName = _csrfTokenHeaderName;
  }

  if (hasValue(_csrfTokenCookieName)) {
    csrfTokenCookieName = _csrfTokenCookieName;
  }

  if (typeof MutationObserver !== "undefined") {
    const unicornObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            scan(node);
          }
        });
      });
    });

    unicornObserver.observe(document, {
      childList: true,
      subtree: true,
    });
  }

  return {
    messageUrl,
    csrfTokenHeaderName,
    csrfTokenCookieName,
    morpher,
  };
}

/**
 * Initializes the component.
 */
export function componentInit(args) {
  args.messageUrl = messageUrl;
  args.csrfTokenHeaderName = csrfTokenHeaderName;
  args.csrfTokenCookieName = csrfTokenCookieName;
  args.morpher = morpher;

  const component = new Component(args);
  components[component.id] = component;

  component.setModelValues();
}

/**
 * Initialize the component from the DOM element if it hasn't been initialized yet.
 *
 * Used to populate the components object with fresh components, created by the server.
 *
 * @param {Object} node The node to check for initialization.
 */
export function insertComponentFromDom(node) {
  const nodeId = node.getAttribute("unicorn:id");

  if (!components[nodeId]) {
    const args = {
      id: nodeId,
      name: node.getAttribute("unicorn:name"),
      key: node.getAttribute("unicorn:key"),
      checksum: node.getAttribute("unicorn:checksum"),
      data: JSON.parse(node.getAttribute("unicorn:data")),
      calls: JSON.parse(node.getAttribute("unicorn:calls")),
    };

    componentInit(args);
  }
}

/**
 * Scans the DOM for any component roots and initializes them if they haven't been already.
 * @param {Element} root The root element to scan. Defaults to document.
 */
export function scan(root) {
  if (!root) {
    root = document;
  }

  if (root.hasAttribute && root.hasAttribute("unicorn:id")) {
    insertComponentFromDom(root);
  }

  const elements = root.querySelectorAll("[unicorn\\:id]");

  elements.forEach((element) => {
    insertComponentFromDom(element);
  });
}

/**
 * Gets the component wit h the specified name or key.
 * Component keys are searched first, then names.
 *
 * @param {String} componentNameOrKey The name or key of the component to search for.
 */
export function getComponent(componentNameOrKey) {
  let component;

  Object.keys(components).forEach((id) => {
    if (isEmpty(component)) {
      const _component = components[id];

      if (String(_component.key) === String(componentNameOrKey)) {
        component = _component;
      }
    }
  });

  if (isEmpty(component)) {
    Object.keys(components).forEach((id) => {
      if (isEmpty(component)) {
        const _component = components[id];

        if (_component.name === componentNameOrKey) {
          component = _component;
        }
      }
    });
  }

  if (!component) {
    throw Error(`No component found for: ${componentNameOrKey}`);
  }

  return component;
}

/**
 * Removes the component's root element from the DOM and deletes it from the
 * component store.
 * @param {String} componentId.
 */
export function deleteComponent(componentId) {
  const root = document.querySelector(`[unicorn\\:id="${componentId}"]`);

  if (root) {
    root.remove();
  }

  delete components[componentId];
}

/**
 * Call an action on the specified component.
 */
export function call(componentNameOrKey, methodName, ...args) {
  const component = getComponent(componentNameOrKey);
  let argString = "";

  args.forEach((arg) => {
    if (typeof arg !== "undefined") {
      if (typeof arg === "string") {
        // Use JSON.stringify to properly escape quotes and special characters
        // Then replace double quotes with single quotes for Python compatibility
        const escapedArg = JSON.stringify(arg).slice(1, -1).replace(/\\"/g, '"').replace(/'/g, "\\'");
        argString = `${argString}'${escapedArg}', `;
      } else {
        argString = `${argString}${arg}, `;
      }
    }
  });

  if (argString) {
    argString = argString.slice(0, -2);
    methodName = `${methodName}(${argString})`;
  }

  component.callMethod(methodName, 0, null, (err) => {
    console.error(err);
  });
}

/**
 * Gets the last return value.
 */
export function getReturnValue(componentNameOrKey) {
  const component = getComponent(componentNameOrKey);

  return component.return.value;
}

/**
 * Adds an event listener for particular events.
 * @param {String} eventName The event to register under. Current events are: `updated`.
 * @param {Function} callback Function to call when the event gets fired.
 */
export function addEventListener(eventName, callback) {
  if (!(eventName in lifecycleEvents)) {
    lifecycleEvents[eventName] = [];
  }

  lifecycleEvents[eventName].push(callback);
}

/**
 * Trigger a component update by dispatching an event for a particular element.
 */
export function trigger(componentNameOrKey, elementKey) {
  const component = getComponent(componentNameOrKey);
  component.trigger(elementKey);
}
