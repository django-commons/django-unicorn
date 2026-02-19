import { debounce } from "./delayers.js";
import { Element } from "./element.js";
import {
  addActionEventListener,
  addModelEventListener,
} from "./eventListeners.js";
import { components, lifecycleEvents } from "./store.js";
import { send } from "./messageSender.js";
import {
  $,
  hasValue,
  isEmpty,
  isFunction,
  walk,
  FilterSkipNested,
} from "./utils.js";

/**
 * Encapsulate component.
 */
export class Component {
  constructor(args) {
    this.id = args.id;
    this.name = args.name;
    this.key = args.key;
    this.messageUrl = args.messageUrl;
    this.csrfTokenHeaderName = args.csrfTokenHeaderName;
    this.csrfTokenCookieName = args.csrfTokenCookieName;
    this.hash = args.hash;
    this.data = args.data || {};
    this.syncUrl = `${this.messageUrl}/${this.name}`;

    this.document = args.document || document;
    this.walker = args.walker || walk;
    this.window = args.window || window;
    this.morpher = args.morpher;

    this.root = undefined;
    this.modelEls = [];
    this.loadingEls = [];
    this.keyEls = [];
    this.visibilityEls = [];
    this.errors = {};
    this.return = {};
    this.poll = {};

    this.actionQueue = [];
    this.actionCleanups = [];
    this.currentActionQueue = null;
    this.lastTriggeringElements = [];

    this.actionEvents = {};
    this.attachedEventTypes = [];
    this.attachedModelEvents = [];

    this.init();
    this.initHistoryState();
    this.refreshEventListeners();
    this.initVisibility();
    this.initPolling();

    this.callCalls(args.calls);
  }

  /**
   * Initializes the Component.
   */
  init() {
    this.root = $(`[unicorn\\:id="${this.id}"]`, this.document);

    if (!this.root) {
      throw Error("No id found");
    }

    this.refreshChecksum();
  }

  /**
   * Gets the children components of the current component.
   */
  getChildrenComponents() {
    const elements = [];

    this.walker(this.root, (el) => {
      if (el.isSameNode(this.root)) {
        // Skip the component root element
        return;
      }

      const componentId = el.getAttribute("unicorn:id");

      if (componentId) {
        const childComponent = components[componentId] || null;

        if (childComponent) {
          elements.push(childComponent);
        }
      }
    });

    return elements;
  }

  /**
   * Gets the parent component of the current component.
   * @param {int} parentComponentId Parent component id.
   */
  getParentComponent(parentComponentId) {
    if (typeof parentComponentId !== "undefined") {
      return components[parentComponentId] || null;
    }

    let currentEl = this.root;
    let parentComponent = null;

    while (!parentComponent && currentEl.parentElement !== null) {
      currentEl = currentEl.parentElement;
      const componentId = currentEl.getAttribute("unicorn:id");

      if (componentId) {
        parentComponent = components[componentId] || null;
      }
    }

    return parentComponent;
  }

  /**
   * Call JavaScript functions on the `window`.
   * @param {Array} calls A list of objects that specify the methods to call.
   *
   * `calls`: [{"fn": "someFunctionName"},]
   * `calls`: [{"fn": "someFunctionName", args: ["world"]},]
   * `calls`: [{"fn": "SomeModule.someFunctionName"},]
   * `calls`: [{"fn": "SomeModule.someFunctionName", args: ["world", "universe"]},]
   *
   * Returns:
   * Array of results for each method call.
   */
  callCalls(calls) {
    calls = calls || [];
    const results = [];

    calls.forEach((call) => {
      let functionName = call.fn;
      let module = this.window;

      call.fn.split(".").forEach((obj, idx) => {
        // only traverse down modules to the first dot, because the last portion is the function name
        if (idx < call.fn.split(".").length - 1) {
          module = module[obj];
          // account for the period when slicing
          functionName = functionName.slice(obj.length + 1);
        }
      });

      if (call.args) {
        results.push(module[functionName](...call.args));
      } else {
        results.push(module[functionName]());
      }
    });

    return results;
  }

  /**
   * Sets event listeners on unicorn elements.
   */
  refreshEventListeners() {
    this.actionEvents = {};
    this.modelEls = [];
    this.loadingEls = [];
    this.visibilityEls = [];

    try {
      this.walker(
        this.root,
        (el) => {
          if (el.isSameNode(this.root)) {
            // Skip the component root element
            return;
          }

          const element = new Element(el);

          if (element.isUnicorn) {
            if (hasValue(element.model)) {
              if (!this.attachedModelEvents.some((e) => e.isSame(element))) {
                this.attachedModelEvents.push(element);
                addModelEventListener(this, element);

                // If a model is lazy, also add an event listener for input for dirty states
                if (element.model.isLazy) {
                  // This input event for isLazy will be stopped after dirty is checked when the event fires
                  addModelEventListener(this, element, "input");
                }
              }

              if (!this.modelEls.some((e) => e.isSame(element))) {
                this.modelEls.push(element);
              }
            } else if (hasValue(element.loading)) {
              this.loadingEls.push(element);

              // Hide loading elements that are shown when an action happens
              if (element.loading.show) {
                element.hide();
              }
            }

            if (hasValue(element.key)) {
              this.keyEls.push(element);
            }

            if (hasValue(element.visibility)) {
              this.visibilityEls.push(element);
            }

            element.actions.forEach((action) => {
              if (this.actionEvents[action.eventType]) {
                this.actionEvents[action.eventType].push({ action, element });
              } else {
                this.actionEvents[action.eventType] = [{ action, element }];

                if (
                  !this.attachedEventTypes.some((et) => et === action.eventType)
                ) {
                  this.attachedEventTypes.push(action.eventType);
                  addActionEventListener(this, action.eventType);
                  element.events.push(action.eventType);
                }
              }
            });
          }
        },
        FilterSkipNested
      );
    } catch (err) {
      // nothing
    }
  }

  /**
   * Calls the method for a particular component.
   */
  callMethod(methodName, debounceTime, partials, errCallback) {
    const action = {
      type: "callMethod",
      payload: { name: methodName },
      partials,
    };
    this.actionQueue.push(action);

    // Debounce timeout defaults to 0 in element.js to remove any perceived lag, but can be overridden
    this.queueMessage(debounceTime, (triggeringElements, _, err) => {
      if (err && isFunction(errCallback)) {
        errCallback(err);
      } else if (err) {
        console.error(err);
      } else {
        // Can hard-code `forceModelUpdate` to `true` since it is always required for
        // `callMethod` actions
        this.setModelValues(triggeringElements, true, true);
      }
    });
  }

  /**
   * Initializes `visible` elements.
   */
  initVisibility() {
    if (
      typeof window !== "undefined" &&
      "IntersectionObserver" in window &&
      "IntersectionObserverEntry" in window &&
      "intersectionRatio" in window.IntersectionObserverEntry.prototype
    ) {
      this.visibilityEls.forEach((element) => {
        const observer = new IntersectionObserver(
          (entries) => {
            const entry = entries[0];

            if (entry.isIntersecting) {
              this.callMethod(
                element.visibility.method,
                element.visibility.debounceTime,
                element.partials,
                (err) => {
                  if (err) {
                    console.error(err);
                  }
                }
              );
            }
          },
          { threshold: [element.visibility.threshold] }
        );

        observer.observe(element.el);
      });
    }
  }

  /**
   * Handles poll errors.
   * @param {Error} err Error.
   */
  handlePollError(err) {
    if (err) {
      console.error(err);
    } else if (this.poll.timer) {
      clearInterval(this.poll.timer);
    }
  }

  /**
   * Check to see if the poll is disabled.
   */
  isPollEnabled() {
    if (!this.poll.disable) {
      if (hasValue(this.poll.disableData)) {
        if (this.poll.disableData.startsWith("!")) {
          // Manually negate this and re-negate it after the check
          this.poll.disableData = this.poll.disableData.slice(1);

          if (this.data[this.poll.disableData]) {
            this.poll.disableData = `!${this.poll.disableData}`;

            return true;
          }

          this.poll.disableData = `!${this.poll.disableData}`;
        } else if (!this.data[this.poll.disableData]) {
          return true;
        }
      } else {
        return true;
      }
    }

    return false;
  }

  /**
   * Sets up polling if it is defined on the component's root.
   */
  initPolling() {
    const rootElement = new Element(this.root);

    if (rootElement.isUnicorn && hasValue(rootElement.poll)) {
      this.poll = rootElement.poll;
      this.poll.timer = null;

      this.document.addEventListener(
        "visibilitychange",
        () => {
          if (this.document.hidden) {
            if (this.poll.timer) {
              clearInterval(this.poll.timer);
            }
          } else {
            // Call the poll method once the tab is visible again
            this.startPolling(true);
          }
        },
        false
      );

      this.poll.partials = rootElement.partials;

      // Call the method once before the timer starts
      this.startPolling(true);
    }
  }

  /**
   * Listens for browser `popstate` events (Back/Forward navigation) and restores
   * the component state that was stored in the history entry. When a `LocationUpdate`
   * is used, the component state is saved in `history.pushState`; this method
   * retrieves that state and triggers `$refresh` so the server re-renders the
   * component with the restored data.
   */
  initHistoryState() {
    this.window.addEventListener("popstate", (event) => {
      if (
        event.state &&
        event.state.unicorn &&
        event.state.unicorn.componentId === this.id
      ) {
        // Merge the stored state back into the component data
        Object.assign(this.data, event.state.unicorn.data);

        // Ask the server to re-render with the restored data
        this.callMethod("$refresh", 0, null, (err) => {
          if (err) {
            console.error(err);
          }
        });
      }
    });
  }

  /**
   * Starts polling and handles stopping the polling if there is an error.
   */
  startPolling(fireImmediately) {
    if (fireImmediately && this.isPollEnabled()) {
      this.callMethod(
        this.poll.method,
        0,
        this.poll.partials,
        this.handlePollError
      );
    }

    this.poll.timer = setInterval(() => {
      if (this.isPollEnabled()) {
        this.callMethod(
          this.poll.method,
          0,
          this.poll.partials,
          this.handlePollError
        );
      }
    }, this.poll.timing);
  }

  /**
   * Refresh the checksum.
   */
  refreshChecksum() {
    this.checksum = this.root.getAttribute("unicorn:checksum");
  }

  /**
   * Sets the value of an element. Tries to deal with HTML weirdnesses.
   * @param {Element} element Element to set value to (value retrieved from `component.data`).
   */
  setValue(element) {
    if (isEmpty(element.model)) {
      // Don't try to set the value if there isn't a model on the element
      return;
    }

    this.setNestedValue(element, element.model.name, this.data);
  }

  /**
   * Sets an element value dealing with potential nested values
   * @param {Element} element Element to set values on
   * @param {String} name Name of the property
   * @param {Object} data Data to get values from
   */
  // eslint-disable-next-line class-methods-use-this
  setNestedValue(element, name, data) {
    const namePieces = name.split(".");
    // Get local version of data in case have to traverse into a nested property
    let _data = data;

    for (let i = 0; i < namePieces.length; i++) {
      const namePiece = namePieces[i];

      if (_data == null) {
        return;
      }

      if (Object.prototype.hasOwnProperty.call(_data, namePiece)) {
        if (i === namePieces.length - 1) {
          element.setValue(_data[namePiece]);
        } else {
          _data = _data[namePiece];
        }
      }
    }
  }

  /**
   * Sets all model values.
   * @param {[Element]} triggeringElements The elements that triggered the event.
   */
  setModelValues(triggeringElements, forceModelUpdates, updateParents) {
    triggeringElements = triggeringElements || [];
    forceModelUpdates = forceModelUpdates || false;
    updateParents = updateParents || false;

    let lastTriggeringElement = null;

    // Focus on the last element which triggered the update.
    // Prevents validation errors from stealing focus.
    if (triggeringElements.length > 0) {
      let elementFocused = false;
      lastTriggeringElement = triggeringElements.slice(-1)[0];

      if (
        hasValue(lastTriggeringElement) &&
        hasValue(lastTriggeringElement.model) &&
        !lastTriggeringElement.model.isLazy
      ) {
        ["id", "key"].forEach((attr) => {
          this.modelEls.forEach((element) => {
            if (!elementFocused) {
              if (
                lastTriggeringElement[attr] &&
                lastTriggeringElement[attr] === element[attr]
              ) {
                element.focus();
                elementFocused = true;
              }
            }
          });
        });
      }
    }

    this.modelEls.forEach((element) => {
      if (
        forceModelUpdates ||
        !lastTriggeringElement ||
        !lastTriggeringElement.isSame(element)
      ) {
        this.setValue(element);
      }
    });

    // Re-set model values for all children
    this.getChildrenComponents().forEach((childComponent) => {
      childComponent.setModelValues(
        triggeringElements,
        forceModelUpdates,
        false
      );
    });

    if (updateParents) {
      const parent = this.getParentComponent();

      if (parent) {
        parent.setModelValues(
          triggeringElements,
          forceModelUpdates,
          updateParents
        );
      }
    }
  }

  /**
   * Queues the `messageSender.send` call.
   */
  queueMessage(debounceTime, callback) {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    if (debounceTime === -1) {
      debounceTime = 250;
    }

    this.debounceTimer = setTimeout(() => {
      send(this, callback);
      this.debounceTimer = null;
    }, debounceTime);
  }

  /**
   * Triggers the event's callback if it is defined.
   * @param {String} eventName The event name to trigger. Current options: "updated".
   */
  triggerLifecycleEvent(eventName) {
    if (eventName in lifecycleEvents) {
      lifecycleEvents[eventName].forEach((cb) => cb(this));
    }
  }

  /**
   * Manually trigger a model's `input` or `blur` event to force a component update.
   *
   * Useful when setting an element's value manually which won't trigger the correct event to fire.
   * @param {String} key Key of the element.
   */
  trigger(key) {
    this.modelEls.forEach((element) => {
      if (element.key === key) {
        const eventType = element.model.isLazy ? "blur" : "input";
        element.el.dispatchEvent(new Event(eventType));
      }
    });
  }

  /**
   * Replace the target DOM with the rerendered component.
   *
   * The function updates the DOM, and updates the Unicorn component store by deleting
   * components that were removed, and adding new components.
   */
  morph(targetDom, rerenderedComponent) {
    if (!rerenderedComponent) {
      return;
    }

    // Helper function that returns an array of nodes with an attribute unicorn:id
    const findUnicorns = () => [
      ...targetDom.querySelectorAll("[unicorn\\:id]"),
    ];

    // Find component IDs before morphing
    const componentIdsBeforeMorph = new Set(
      findUnicorns().map((el) => el.getAttribute("unicorn:id"))
    );

    // Morph
    this.morpher.morph(targetDom, rerenderedComponent);

    // Find all component IDs after morphing
    const componentIdsAfterMorph = new Set(
      findUnicorns().map((el) => el.getAttribute("unicorn:id"))
    );

    // Delete components that were removed
    const removedComponentIds = [...componentIdsBeforeMorph].filter(
      (id) => !componentIdsAfterMorph.has(id)
    );
    removedComponentIds.forEach((id) => {
      Unicorn.deleteComponent(id);
    });

    // Populate Unicorn with new components
    findUnicorns().forEach((el) => {
      Unicorn.insertComponentFromDom(el);
    });
  }

  morphRoot(rerenderedComponent) {
    this.morph(this.root, rerenderedComponent);
  }
}
