export function portal(node: HTMLElement, target: HTMLElement | string = 'body') {
  let targetNode: HTMLElement | null;
  
  function update() {
    targetNode = typeof target === 'string' ? document.querySelector(target) : target;
    if (targetNode) {
      targetNode.appendChild(node);
      node.hidden = false;
    }
  }

  update();

  return {
    update(newTarget: HTMLElement | string) {
      target = newTarget;
      update();
    },
    destroy() {
      if (node.parentNode) {
        node.parentNode.removeChild(node);
      }
    }
  };
}
