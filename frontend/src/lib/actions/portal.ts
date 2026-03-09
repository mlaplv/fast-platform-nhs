export function portal(
  node: HTMLElement,
  target: HTMLElement | string = "body",
) {
  let targetNode: HTMLElement;
  function updateTarget() {
    if (typeof target === "string") {
      targetNode = document.querySelector(target) as HTMLElement;
    } else {
      targetNode = target;
    }
    if (targetNode) {
      targetNode.appendChild(node);
    }
  }

  updateTarget();

  return {
    update(newTarget: HTMLElement | string) {
      target = newTarget;
      updateTarget();
    },
    destroy() {
      if (node.parentNode) {
        node.parentNode.removeChild(node);
      }
    },
  };
}
