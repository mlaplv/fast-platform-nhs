/**
 * SEO Graph Store — SvelteKit 5 Runes
 * 
 * State architecture cho interactive Pillar & Cluster network graph.
 * Pattern: Optimistic update → API confirm → rollback on fail.
 */

export interface GraphNode {
	id: string;
	entity_type: 'article' | 'product';
	entity_id: string;
	label: string;
	slug: string;
	url: string | null;
	is_pillar: boolean;
	pillar_topic: string | null;
	group: 'pillar' | 'cluster' | 'unclassified';
	val: number;
	color: string;
	ai_confidence?: number | null;
	is_confirmed?: boolean | null;
}

export interface GraphLink {
	id: string;
	source: string;
	target: string;
	link_type: string;
	ai_confidence: number | null;
	is_confirmed: boolean;
	curvature: number;
	color: string;
}

export interface GraphMeta {
	total_nodes: number;
	total_edges: number;
	generated_at: string;
	pillars: number;
	unclassified: number;
}

export interface GraphData {
	meta: GraphMeta;
	nodes: GraphNode[];
	links: GraphLink[];
}

// ─── Runes State ──────────────────────────────────────────────────────────────

export const graphData = $state<GraphData>({
	meta: { total_nodes: 0, total_edges: 0, generated_at: '', pillars: 0, unclassified: 0 },
	nodes: [],
	links: []
});

export const selectedNodeId = $state<{ value: string | null }>({ value: null });
export const isLoading = $state<{ value: boolean }>({ value: false });
export const errorMsg = $state<{ value: string | null }>({ value: null });
export const filterGroup = $state<{ value: 'all' | 'pillar' | 'cluster' | 'unclassified' }>({ value: 'all' });

// ─── Derived ──────────────────────────────────────────────────────────────────

export const pillarNodes = $derived(graphData.nodes.filter((n) => n.is_pillar));
export const unclassifiedCount = $derived(graphData.nodes.filter((n) => n.group === 'unclassified').length);
export const aiSuggestedCount = $derived(graphData.links.filter((l) => !l.is_confirmed).length);
export const activeNode = $derived(
	selectedNodeId.value ? graphData.nodes.find((n) => n.id === selectedNodeId.value) ?? null : null
);

export const filteredNodes = $derived(
	filterGroup.value === 'all'
		? graphData.nodes
		: graphData.nodes.filter((n) => n.group === filterGroup.value)
);

// ─── Actions ──────────────────────────────────────────────────────────────────

export async function fetchGraph(apiBase: string): Promise<void> {
	isLoading.value = true;
	errorMsg.value = null;
	try {
		const res = await fetch(`${apiBase}/api/v1/seo/graph`, { credentials: 'include' });
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		const data: GraphData = await res.json();
		graphData.meta = data.meta;
		graphData.nodes = data.nodes;
		graphData.links = data.links;
	} catch (e) {
		errorMsg.value = e instanceof Error ? e.message : 'Không thể tải graph.';
	} finally {
		isLoading.value = false;
	}
}

/**
 * Override edge — Optimistic update khi admin drag-and-drop node.
 * Cập nhật local state ngay, sau đó confirm với server.
 * Rollback nếu API fail.
 */
export async function overrideEdge(
	apiBase: string,
	edgeId: string,
	newSourceNodeId: string,
	newTargetNodeId: string
): Promise<void> {
	// 1. Snapshot for rollback
	const snapshot = [...graphData.links];

	// 2. Optimistic update
	const edge = graphData.links.find((l) => l.id === edgeId);
	if (edge) {
		edge.source = newSourceNodeId;
		edge.target = newTargetNodeId;
		edge.link_type = 'manual';
		edge.is_confirmed = true;
		edge.color = '#10b981'; // Emerald — manual
	}

	try {
		const res = await fetch(`${apiBase}/api/v1/seo/edges/${edgeId}`, {
			method: 'PATCH',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				source_node_id: newSourceNodeId,
				target_node_id: newTargetNodeId,
				link_type: 'manual',
				is_confirmed: true
			})
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
	} catch (e) {
		// 3. Rollback on failure
		graphData.links = snapshot;
		errorMsg.value = 'Override thất bại. Đã rollback.';
	}
}

/**
 * Toggle Pillar designation on a node.
 * Updates local state and calls PATCH /seo/nodes/:id.
 */
export async function togglePillar(
	apiBase: string,
	nodeId: string,
	isPillar: boolean,
	pillarTopic?: string
): Promise<void> {
	const snapshot = graphData.nodes.map((n) => ({ ...n }));
	const node = graphData.nodes.find((n) => n.id === nodeId);
	if (node) {
		node.is_pillar = isPillar;
		node.group = isPillar ? 'pillar' : 'cluster';
		node.color = isPillar ? '#6366f1' : '#a5b4fc';
		node.val = isPillar ? 20 : 8;
		if (pillarTopic) node.pillar_topic = pillarTopic;
	}

	try {
		const res = await fetch(`${apiBase}/api/v1/seo/nodes/${nodeId}`, {
			method: 'PATCH',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ is_pillar: isPillar, pillar_topic: pillarTopic })
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
	} catch {
		graphData.nodes = snapshot;
		errorMsg.value = 'Cập nhật Pillar thất bại. Đã rollback.';
	}
}

/**
 * Trigger manual AI matching for a specific entity.
 */
export async function triggerMatch(
	apiBase: string,
	entityType: 'article' | 'product',
	entityId: string
): Promise<{ match_tier: string; ai_confidence: number | null } | null> {
	try {
		const res = await fetch(`${apiBase}/api/v1/seo/match`, {
			method: 'POST',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ entity_type: entityType, entity_id: entityId })
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		const result = await res.json();
		// Refresh graph sau khi match
		await fetchGraph(apiBase);
		return result;
	} catch {
		return null;
	}
}
