/**
 * ELITE V2.2 PORTAL ACTION (Svelte 5 Runes Ready)
 * Di chuyển element ra khỏi Stacking Context hiện tại để vào body (mặc định).
 */
export function portal(node: HTMLElement, target: string | HTMLElement = 'body') {
	let targetEl: HTMLElement | null;

	async function update(newTarget: string | HTMLElement) {
		target = newTarget;
		if (typeof target === 'string') {
			targetEl = document.querySelector(target);
			if (targetEl === null) {
				await new Promise((resolve) => setTimeout(resolve, 0));
				targetEl = document.querySelector(target);
			}
		} else {
			targetEl = target;
		}

		if (targetEl) {
			targetEl.appendChild(node);
			node.hidden = false;
		} else {
			console.warn(`[Portal Action] Target "${target}" not found in DOM.`);
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
