/**
 * ELITE V2.2 PORTAL ACTION (Svelte 5 Runes Ready)
 * Di chuyển element ra khỏi Stacking Context hiện tại để vào body (mặc định).
 */
export function portal(node: HTMLElement, target: string | HTMLElement | boolean = 'body') {
	let targetEl: HTMLElement | null;
	let originalParent: HTMLElement | null = node.parentElement;
	let placeholder: Comment | null = null;

	async function update(newTarget: string | HTMLElement | boolean) {
		target = newTarget;

		// CNS V2.2: Support boolean toggle (true = portal to body, false = return home)
		if (target === false) {
			if (placeholder && placeholder.parentNode && originalParent) {
				placeholder.parentNode.replaceChild(node, placeholder);
				placeholder = null;
			}
			return;
		}

		const selector = target === true || target === undefined ? 'body' : target;

		if (typeof selector === 'string') {
			targetEl = document.querySelector(selector);
			if (targetEl === null) {
				await new Promise((resolve) => setTimeout(resolve, 0));
				targetEl = document.querySelector(selector);
			}
		} else {
			targetEl = selector as HTMLElement;
		}

		if (targetEl && node.parentElement !== targetEl) {
			// Save original location
			if (!placeholder) {
				placeholder = document.createComment('portal-placeholder');
				node.parentNode?.replaceChild(placeholder, node);
			}
			targetEl.appendChild(node);
			node.hidden = false;
		}
	}

	// CNS V2.2: Capture parent on next tick if not available yet
	if (!originalParent) {
		setTimeout(() => {
			originalParent = node.parentElement;
			update(target);
		}, 0);
	} else {
		update(target);
	}

	return {
		update,
		destroy() {
			if (placeholder && placeholder.parentNode) {
				placeholder.parentNode.replaceChild(node, placeholder);
			} else if (node.parentNode) {
				node.parentNode.removeChild(node);
			}
		}
	};
}
