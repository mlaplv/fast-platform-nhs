export function portal(node: HTMLElement, target: string | HTMLElement | boolean = 'body') {
	let targetEl: HTMLElement | null = null;
    let placeholder: Comment | null = null;
    let hasMoved = false;

	async function performPortal(newTarget: string | HTMLElement | boolean) {
		if (newTarget === false) {
			if (hasMoved && placeholder && placeholder.parentNode) {
				placeholder.parentNode.replaceChild(node, placeholder);
				hasMoved = false;
			}
			return;
		}

		const selector = newTarget === true || newTarget === undefined ? 'body' : newTarget;
		
		if (typeof selector === 'string') {
			targetEl = document.querySelector(selector);
			if (!targetEl) {
				await new Promise(r => setTimeout(r, 0));
				targetEl = document.querySelector(selector);
			}
		} else {
			targetEl = selector as HTMLElement;
		}

        if (!node.parentNode) {
            await new Promise(r => setTimeout(r, 0));
        }

		if (targetEl && node.parentNode && node.parentNode !== targetEl) {
            if (!placeholder) {
                placeholder = document.createComment('portal-placeholder');
            }
            if (!hasMoved) {
                node.parentNode.insertBefore(placeholder, node);
            }
			targetEl.appendChild(node);
            hasMoved = true;
			node.hidden = false;
		}
	}

	setTimeout(() => performPortal(target), 0);

	return {
		update(newTarget: string | HTMLElement | boolean) {
            performPortal(newTarget);
        },
		destroy() {
            if (node.parentNode) {
                node.parentNode.removeChild(node);
            }
            if (placeholder && placeholder.parentNode) {
                placeholder.parentNode.removeChild(placeholder);
            }
		}
	};
}
