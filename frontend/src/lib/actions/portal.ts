/**
 * Portal Action (Elite V2.2)
 * Renders an element in a different part of the DOM (defaults to body).
 */
export function portal(node: HTMLElement, target: HTMLElement | string = "body") {
  let targetElement: HTMLElement | null;

  async function update(newTarget: HTMLElement | string) {
    if (typeof newTarget === "string") {
      targetElement = document.querySelector(newTarget);
    } else {
      targetElement = newTarget;
    }

    if (targetElement) {
      targetElement.appendChild(node);
      node.hidden = false;
    } else {
      console.warn(`[Portal] Target "${newTarget}" not found.`);
    }
  }

  update(target);

  return {
    update,
    destroy() {
      if (node.parentNode) {
        node.parentNode.removeChild(node);
      }
    }
  };
}
