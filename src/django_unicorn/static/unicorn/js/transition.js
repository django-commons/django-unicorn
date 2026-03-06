import { Element as UnicornElement } from "./element.js";

/**
 * Handles CSS transitions for an element.
 */
export class Transition {
  /**
   * Run the enter transition.
   * @param {Element} el DOM element
   */
  static async enter(el) {
    await this.run(el, "enter");
  }

  /**
   * Run the leave transition.
   * @param {Element} el DOM element
   */
  static async leave(el) {
    await this.run(el, "leave");
  }

  /**
   * Run a transition for a given stage (enter or leave).
   */
  static async run(el, stage) {
    const element = new UnicornElement(el);
    const transitions = element.transitions;

    const classes = (transitions[stage] || "").split(" ").filter(Boolean);
    const startClasses = (transitions[`${stage}-start`] || "").split(" ").filter(Boolean);
    const endClasses = (transitions[`${stage}-end`] || "").split(" ").filter(Boolean);

    if (classes.length === 0 && startClasses.length === 0 && endClasses.length === 0) {
      return;
    }

    // Prepare transition
    el.classList.add(...classes);
    el.classList.add(...startClasses);

    // Wait for a frame to ensure classes are applied
    await nextFrame();

    el.classList.remove(...startClasses);
    el.classList.add(...endClasses);

    await afterTransition(el);

    el.classList.remove(...classes);
    el.classList.remove(...endClasses);
  }
}

/**
 * Wait for the next animation frame.
 */
function nextFrame() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(resolve);
    });
  });
}

/**
 * Wait for a transition or animation to finish.
 */
function afterTransition(el) {
  return Promise.all(el.getAnimations().map((animation) => animation.finished));
}
