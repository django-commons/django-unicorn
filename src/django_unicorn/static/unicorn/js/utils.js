/**
 * Checks if an object is empty. Useful to check if a dictionary has a value.
 */
export function isEmpty(obj) {
  return (
    typeof obj === "undefined" ||
    obj === null ||
    (Object.keys(obj).length === 0 && obj.constructor === Object) ||
    obj === ""
  );
}

/**
 * Checks if an object has a value.
 */
export function hasValue(obj) {
  return !isEmpty(obj);
}

/**
 * Checks if an object is a function.
 */
export function isFunction(obj) {
  return obj && typeof obj === "function";
}

/**
 * Checks if a string has the search text.
 */
export function contains(str, search) {
  if (!str) {
    return false;
  }

  return str.indexOf(search) > -1;
}

/**
 * A simple shortcut for querySelector that everyone loves.
 */
export function $(selector, scope) {
  if (scope === undefined) {
    scope = document;
  }

  return scope.querySelector(selector);
}

/**
 * Get the CSRF token used by Django.
 */
export function getCsrfToken(component) {
  // Default to looking for the CSRF in the cookie
  const cookieKey = component.csrfTokenCookieName + "=";
  const csrfTokenCookie = component.document.cookie
    .split(";")
    .filter((item) => item.trim().startsWith(cookieKey));

  if (csrfTokenCookie.length > 0) {
    return csrfTokenCookie[0].replace(cookieKey, "");
  }

  // Fall back to check for the CSRF hidden input
  const csrfElements = component.document.getElementsByName(
    "csrfmiddlewaretoken"
  );

  if (csrfElements && csrfElements.length > 0) {
    return csrfElements[0].getAttribute("value");
  }

  throw Error("CSRF token is missing. Do you need to add {% csrf_token %}?");
}

/**
 * Converts a string to "kebab-case", aka lower-cased with hyphens.
 * @param {string} str The string to be converted.
 */
export function toKebabCase(str) {
  if (!str) {
    return "";
  }

  const match = str.match(
    /[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+/g
  );

  if (!match) {
    return str;
  }

  return match.map((x) => x.toLowerCase()).join("-");
}

/**
 * Filter to accept any element (use with walk)
 */
export const FilterAny = {
  acceptNode: (node) => NodeFilter.FILTER_ACCEPT,
};

/**
 * Filter to skip nested components (use with walk)
 */
export const FilterSkipNested = {
  acceptNode: (node) => {
    if (node.getAttribute("unicorn:meta")) {
      // with a tree walker, child nodes are also rejected
      return NodeFilter.FILTER_REJECT;
    }
    return NodeFilter.FILTER_ACCEPT;
  },
};

/**
 * Traverses the DOM looking for child elements.
 */
export function walk(el, callback, filter = FilterAny) {
  const walker = document.createTreeWalker(
    el,
    NodeFilter.SHOW_ELEMENT,
    filter,
    false
  );

  while (walker.nextNode()) {
    // TODO: Handle sub-components?
    callback(walker.currentNode);
  }
}

export function args(func) {
  func = func.trim();

  if (!contains(func, "(") || !func.endsWith(")")) {
    return [];
  }

  // Remove the method name and parenthesis
  func = func.slice(func.indexOf("(") + 1, func.length - 1);

  const functionArgs = [];
  let currentArg = "";

  let inSingleQuote = false;
  let inDoubleQuote = false;
  let parenthesisCount = 0;
  let bracketCount = 0;
  let curlyCount = 0;

  for (let idx = 0; idx < func.length; idx++) {
    const c = func.charAt(idx);
    currentArg += c;

    if (c === "[") {
      bracketCount++;
    } else if (c === "]") {
      bracketCount--;
    } else if (c === "(") {
      parenthesisCount++;
    } else if (c === ")") {
      parenthesisCount--;
    } else if (c === "{") {
      curlyCount++;
    } else if (c === "}") {
      curlyCount--;
    } else if (c === "'") {
      inSingleQuote = !inSingleQuote;
    } else if (c === '"') {
      inDoubleQuote = !inDoubleQuote;
    } else if (c === ",") {
      if (
        !inSingleQuote &&
        !inDoubleQuote &&
        bracketCount === 0 &&
        parenthesisCount === 0
      ) {
        // Remove the trailing comma
        currentArg = currentArg.slice(0, currentArg.length - 1);

        functionArgs.push(currentArg);
        currentArg = "";
      }
    }

    if (idx === func.length - 1) {
      if (
        !inSingleQuote &&
        !inDoubleQuote &&
        bracketCount === 0 &&
        parenthesisCount === 0
      ) {
        functionArgs.push(currentArg.trim());
        currentArg = "";
      }
    }
  }

  return functionArgs;
}

/**
 * Converts string with '*' wildcards to RegExp.
 */
export function toRegExp(str) {
  const strArray = str.split("*");
  let regexp = "";
  strArray.forEach((item, idx) => {
    if (idx === 0 && item === "") {
      regexp = regexp.concat("[a-zA-Z0-9_:.\\-]*");
    } else if (idx === strArray.length - 1) {
      if (item !== "") {
        regexp = regexp.concat(`(${item})`);
      }
    } else {
      regexp = regexp.concat(`(${item})`, "[a-zA-Z0-9_:.\\-]*");
    }
  });
  return new RegExp(regexp);
}
