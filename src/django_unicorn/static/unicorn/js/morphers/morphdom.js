import morphdom from "../morphdom/2.6.1/morphdom.js";
import { Transition } from "../transition.js";
import { Element as UnicornElement } from "../element.js";

export class MorphdomMorpher {
  constructor(options) {
    this.options = options;
  }

  morph(dom, htmlElement) {
    return morphdom(dom, htmlElement, this.getOptions());
  }

  getOptions() {
    const reloadScriptElements = this.options.RELOAD_SCRIPT_ELEMENTS || false;

    return {
      childrenOnly: false,
      // eslint-disable-next-line consistent-return
      getNodeKey(node) {
        // A node's unique identifier. Used to rearrange elements rather than
        // creating and destroying an element that already exists.
        if (node.attributes) {
          const key =
            node.getAttribute("unicorn:id") ||
            node.getAttribute("unicorn:key") ||
            node.id;

          if (key) {
            return key;
          }
        }
      },
      // eslint-disable-next-line consistent-return
      onBeforeElUpdated(fromEl, toEl) {
        // Because morphdom also supports vDom nodes, it uses isSameNode to detect
        // sameness. When dealing with DOM nodes, we want isEqualNode, otherwise
        // isSameNode will ALWAYS return false.
        if (fromEl.isEqualNode(toEl)) {
          return false;
        }

        if (reloadScriptElements) {
          if (fromEl.nodeName === "SCRIPT" && toEl.nodeName === "SCRIPT") {
            // https://github.com/patrick-steele-idem/morphdom/issues/178#issuecomment-652562769
            const script = document.createElement("script");
            // copy over the attributes
            [...toEl.attributes].forEach((attr) => {
              script.setAttribute(attr.nodeName, attr.nodeValue);
            });

            script.innerHTML = toEl.innerHTML;
            fromEl.replaceWith(script);

            return false;
          }
        }

        return true;
      },
      onNodeAdded(node) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          Transition.enter(node);
        }

        if (reloadScriptElements) {
          if (node.nodeName === "SCRIPT") {
            // https://github.com/patrick-steele-idem/morphdom/issues/178#issuecomment-652562769
            const script = document.createElement("script");
            // copy over the attributes
            [...node.attributes].forEach((attr) => {
              script.setAttribute(attr.nodeName, attr.nodeValue);
            });

            script.innerHTML = node.innerHTML;
            node.replaceWith(script);
          }
        }
      },
      onBeforeNodeDiscarded(node) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          const element = new UnicornElement(node);

          if (element.transitions.leave) {
            Transition.leave(node).then(() => {
              node.remove();
            });

            return false;
          }
        }

        return true;
      },
    };
  }
}
