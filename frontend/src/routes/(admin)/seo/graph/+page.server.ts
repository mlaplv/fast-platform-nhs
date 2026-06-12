import type { PageServerLoad } from './$types';
import { API_BASE } from '$env/static/private';

export const load: PageServerLoad = async ({ fetch, locals }) => {
	try {
		const res = await fetch(`${API_BASE}/api/v1/seo/graph`);
		if (!res.ok) return { graphData: null, error: `HTTP ${res.status}` };
		const graphData = await res.json();
		return { graphData, error: null };
	} catch (e) {
		return { graphData: null, error: 'Không thể tải SEO graph từ server.' };
	}
};
