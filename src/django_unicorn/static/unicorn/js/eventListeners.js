import { $, args, hasValue, toKebabCase, toRegExp } from "./utils.js";
import { Element } from "./element.js";

/**
 * Handles loading elements in the component.
 * @param {Component} component Component.
 * @param {Element} targetElement Targetted element. Can be null when called via Unicorn.call().
 */
export function handleLoading(component, targetElement) {
  if (targetElement) {
    targetElement.handleLoading();
  }

  // Look at all elements with a loading attribute
  component.loadingEls.forEach((loadingElement) => {
    if (loadingElement.target) {
      // Targeted loading elements only apply when there is a specific triggering element
      if (!targetElement) {
        return;
      }

      // Get all ID matches
      if (loadingElement.target.includes("*")) {
        const targetRegex = toRegExp(loadingElement.target);
        const targetedElArray = [];
        const childrenCollection = component.root.getElementsByTagName("*");
        [...childrenCollection].forEach((child) => {
          [...child.attributes].forEach((attr) => {
            if (
              ["id", "unicorn:key", "u:key"].includes(attr.name) &&
              attr.value.match(targetRegex)
            ) {
              targetedElArray.push(child);
            }
          });
        });

        targetedElArray.forEach((targetedEl) => {
          if (targetElement.el.isSameNode(targetedEl)) {
            loadingElement.handleLoading();
            if (loadingElement.loading.hide) {
              loadingElement.hide();
            } else if (loadingElement.loading.show) {
              loadingElement.show();
            }
          }
        });
      } else {
        let targetedEl = $(`#${loadingElement.target}`, component.root);

        if (!targetedEl) {
          component.keyEls.forEach((keyElement) => {
            if (!targetedEl && keyElement.key === loadingElement.target) {
              targetedEl = keyElement.el;
            }
          });
        }

        if (targetedEl) {
          if (targetElement.el.isSameNode(targetedEl)) {
            loadingElement.handleLoading();
            if (loadingElement.loading.hide) {
              loadingElement.hide();
            } else if (loadingElement.loading.show) {
              loadingElement.show();
            }
          }
        }
      }
    } else {
      loadingElement.handleLoading();

      if (loadingElement.loading.hide) {
        loadingElement.hide();
      } else if (loadingElement.loading.show) {
        loadingElement.show();
      }
    }
  });
}

/**
 * Parse arguments and deal with nested data.
 *
 * // <button u:click="test($returnValue.hello.trim())">Test</button>
 * let data = {hello: " world "};
 * let output = parseEventArg(data, "$returnValue.hello.trim()");
 * // output is 'world'
 *
 * @param {Object} data The data that should be parsed.
 * @param {String} arg The argument to the function.
 * @param {String} specialArgName The special argument (starts with a $).
 */
function parseEventArg(data, arg, specialArgName) {
  // Remove any extra whitespace, everything before and including "$event", and the ending paren
  arg = arg
    .trim()
    .slice(arg.indexOf(specialArgName) + specialArgName.length)
    .trim();

  arg.split(".").forEach((piece) => {
    piece = piece.trim();

    if (piece) {
      // TODO: Handle method calls with args
      if (piece.endsWith("()")) {
        // method call
        const methodName = piece.slice(0, piece.length - 2);
        data = data[methodName]();
      } else if (hasValue(data[piece])) {
        data = data[piece];
      } else {
        throw Error(`'${piece}' could not be retrieved`);
      }
    }
  });

  if (typeof data === "string") {
    // Wrap strings in quotes
    data = `"${data}"`;
  }

  return data;
}

/**
 * Adds an action event listener to the document for each type of event (e.g. click, keyup, etc).
 * Added at the document level because validation errors would sometimes remove the
 * events when attached directly to the element.
 * @param {Component} component Component that contains the element.
 * @param {string} eventType Event type to listen for.
 */
export function addActionEventListener(component, eventType) {
  component.document.addEventListener(eventType, (event) => {
    let targetElement = new Element(event.target);

    // Make sure that the target element is a unicorn element.
    // Handles events fired from an element inside a unicorn element
    // e.g. <button u:click="click"><span>Click!</span></button>
    if (targetElement && !targetElement.isUnicorn) {
      targetElement = targetElement.getUnicornParent();
    }

    if (
      targetElement &&
      targetElement.isUnicorn &&
      targetElement.actions.length > 0 &&
      eventType in component.actionEvents
    ) {
      component.actionEvents[eventType].forEach((actionEvent) => {
        const { action } = actionEvent;
        const { element } = actionEvent;

        if (targetElement.isSame(element)) {
          // Add the value of any child element of the target that is a lazy model to the action queue
          // Handles situations similar to https://github.com/livewire/livewire/issues/528
          component.walker(element.el, (childEl) => {
            const modelElsInTargetScope = component.modelEls.filter((e) =>
              e.isSameEl(childEl)
            );

            modelElsInTargetScope.forEach((modelElement) => {
              if (hasValue(modelElement.model) && modelElement.model.isLazy) {
                const actionForQueue = {
                  type: "syncInput",
                  payload: {
                    name: modelElement.model.name,
                    value: modelElement.getValue(),
                  },
                };
                component.actionQueue.push(actionForQueue);
              }
            });
          });

          if (action.isPrevent) {
            event.preventDefault();
          }

          if (action.isStop) {
            event.stopPropagation();
          }

          if (action.isDiscard) {
            // Remove all existing action events in the queue
            component.actionQueue = [];
          }

          let actionName = action.name;
          // Handle special arguments (e.g. $event)
          args(actionName).forEach((eventArg) => {
            if (eventArg.startsWith("$event")) {
              try {
                const data = parseEventArg(event, eventArg, "$event");
                actionName = actionName.replace(eventArg, data);
              } catch (err) {
                // console.error(err);
                actionName = actionName.replace(eventArg, "");
              }
            } else if (eventArg.startsWith("$returnValue")) {
              if (
                hasValue(component.return) &&
                hasValue(component.return.value)
              ) {
                try {
                  const data = parseEventArg(
                    component.return.value,
                    eventArg,
                    "$returnValue"
                  );
                  actionName = actionName.replace(eventArg, data);
                } catch (err) {
                  actionName = actionName.replace(eventArg, "");
                }
              } else {
                actionName = actionName.replace(eventArg, "");
              }
            }
          });

          if (!action.key || action.key === toKebabCase(event.key)) {
            if (action.isDisable) {
              element.el.disabled = true;
              component.actionCleanups.push(() => {
                element.el.disabled = false;
              });
            }

            handleLoading(component, targetElement);
            component.callMethod(
              actionName,
              action.debounceTime,
              targetElement.partials
            );
          }
        }
      });
    }
  });
}

/**
 * Adds a model event listener to the element.
 * @param {Component} component Component that contains the element.
 * @param {Element} Element that will get the event attached.
 * @param {string} eventType Event type to listen for. Optional; will use `model.eventType` by default.
 */
export function addModelEventListener(component, element, eventType) {
  eventType = eventType || element.model.eventType;
  element.events.push(eventType);
  const { el } = element;

  el.addEventListener(eventType, (event) => {
    let isDirty = false;

    if (component.data[element.model.name] !== element.getValue()) {
      isDirty = true;
      element.handleDirty();
    } else {
      element.handleDirty(true);
    }

    if (element.model.isLazy) {
      // Lazy models fire an input and blur so that the dirty check above works as expected.
      // This will prevent the input event from doing anything.
      if (eventType === "input") {
        return;
      }

      // Lazy non-dirty elements can bail
      if (!isDirty) {
        return;
      }
    }

    const action = {
      type: "syncInput",
      payload: {
        name: element.model.name,
        value: element.getValue(),
      },
      partials: element.partials,
    };

    if (!component.lastTriggeringElements.some((e) => e.isSame(element))) {
      component.lastTriggeringElements.push(element);
    }

    if (element.model.isDefer) {
      let foundActionIdx = -1;

      // Update the existing action with the current value
      component.actionQueue.forEach((a, idx) => {
        if (a.payload.name === element.model.name) {
          a.payload.value = element.getValue();
          foundActionIdx = idx;
        }
      });

      // Add a new action
      if (isDirty && foundActionIdx === -1) {
        component.actionQueue.push(action);
      }

      // Remove the found action that isn't dirty
      if (!isDirty && foundActionIdx > -1) {
        component.actionQueue.splice(foundActionIdx);
      }

      return;
    }

    component.actionQueue.push(action);

    component.queueMessage(
      element.model.debounceTime,
      (triggeringElements, forceModelUpdate, err) => {
        if (err) {
          console.error(err);
        } else {
          triggeringElements = triggeringElements || [];

          // Make sure that the current element is included in the triggeringElements
          // if for some reason it is missing
          if (!triggeringElements.some((e) => e.isSame(element))) {
            triggeringElements.push(element);
          }

          component.setModelValues(triggeringElements, forceModelUpdate, true);
        }
      }
    );
  });
}
