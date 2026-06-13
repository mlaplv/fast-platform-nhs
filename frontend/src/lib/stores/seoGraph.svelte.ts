/**
 * SEO Graph Store — SvelteKit 5 Runes
 * 
 * State architecture cho interactive Pillar & Cluster network graph.
 * Pattern: Optimistic update → API confirm → rollback on fail.
 */

export interface GraphNode {
	id: string;
	entity_type: 'article' | 'product' | 'ARTICLE' | 'PRODUCT' | string;
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
export const selectedPillarId = $state<{ value: string | null }>({ value: null });
export const allPillars = $state<{ value: GraphNode[] }>({ value: [] });
export const isLoading = $state<{ value: boolean }>({ value: false });
export const errorMsg = $state<{ value: string | null }>({ value: null });
export const filterGroup = $state<{ value: 'all' | 'pillar' | 'cluster' | 'unclassified' | 'ai_suggested' }>({ value: 'all' });
export const isSidebarOpen = $state<{ value: boolean }>({ value: true });
export const batchSelectedIds = $state<{ value: Set<string> }>({ value: new Set() });

// ─── Derived ──────────────────────────────────────────────────────────────────

const _pillarNodes = $derived(graphData.nodes.filter((n) => n.is_pillar));
export const getPillarNodes = () => _pillarNodes;

const _unclassifiedCount = $derived(graphData.nodes.filter((n) => n.group === 'unclassified').length);
export const getUnclassifiedCount = () => _unclassifiedCount;

const _aiSuggestedCount = $derived(graphData.links.filter((l) => !l.is_confirmed).length);
export const getAiSuggestedCount = () => _aiSuggestedCount;

const _activeNode = $derived(
	selectedNodeId.value ? graphData.nodes.find((n) => n.id === selectedNodeId.value) ?? null : null
);
export const getActiveNode = () => _activeNode;

const _filteredNodes = $derived(
	filterGroup.value === 'all'
		? graphData.nodes
		: graphData.nodes.filter((n) => n.group === filterGroup.value)
);
export const getFilteredNodes = () => _filteredNodes;

// ─── Actions ──────────────────────────────────────────────────────────────────

export async function fetchGraph(apiBase: string, pillarId?: string | null): Promise<void> {
	isLoading.value = true;
	errorMsg.value = null;
	try {
		const targetPillarId = pillarId !== undefined ? pillarId : selectedPillarId.value;
		const pillarQuery = targetPillarId ? `&pillar_id=${targetPillarId}` : '';
		const res = await fetch(`${apiBase}/api/v1/seo/graph?t=${Date.now()}${pillarQuery}`, { credentials: 'include' });
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		const data: GraphData = await res.json();
		graphData.meta = data.meta;
		graphData.nodes = data.nodes;
		graphData.links = data.links;
		
		// Cache full list of pillars from a full graph load
		if (!targetPillarId) {
			allPillars.value = data.nodes.filter((n) => n.is_pillar);
		}
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
		await fetchGraph(apiBase);
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

/**
 * Trigger manual AI matching for all unclassified nodes.
 */
export async function triggerBulkMatch(
	apiBase: string
): Promise<{ success: number; failed: number; total_nodes_processed: number } | null> {
	try {
		const res = await fetch(`${apiBase}/api/v1/seo/match/bulk`, {
			method: 'POST',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' }
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		const result = await res.json();
		// Refresh graph sau khi match bulk
		await fetchGraph(apiBase);
		return result.data;
	} catch (e) {
		errorMsg.value = e instanceof Error ? e.message : 'Chạy AI Matching hàng loạt thất bại.';
		return null;
	}
}

/**
 * Batch assign multiple unclassified nodes to a single Pillar.
 * Creates a manual edge from pillar → each selected node.
 * Optimistic: updates local node group immediately, rolls back all on failure.
 */
export async function batchAssignPillar(
	apiBase: string,
	nodeIds: string[],
	pillarNodeId: string
): Promise<{ success: number; failed: number }> {
	if (!nodeIds.length) return { success: 0, failed: 0 };

	// Snapshot for rollback
	const snapshot = graphData.nodes.map((n) => ({ ...n }));
	const snapshotLinks = [...graphData.links];

	// Optimistic: mark selected nodes as cluster under the pillar
	for (const id of nodeIds) {
		const node = graphData.nodes.find((n) => n.id === id);
		if (node) {
			node.group = 'cluster';
			node.color = '#a5b4fc';
		}
	}

	try {
		const res = await fetch(`${apiBase}/api/v1/seo/edges/bulk`, {
			method: 'POST',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				source_node_id: pillarNodeId,
				target_node_ids: nodeIds,
				link_type: 'manual',
				is_confirmed: true
			})
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		
		const result = await res.json();
		const added = Number(result.data?.added || 0);
		const updated = Number(result.data?.updated || 0);
		
		// Clear batch selection and refresh graph
		batchSelectedIds.value = new Set();
		await fetchGraph(apiBase);
		return { success: added + updated, failed: 0 };
	} catch (e) {
		// Rollback on failure
		graphData.nodes = snapshot;
		graphData.links = snapshotLinks;
		errorMsg.value = e instanceof Error ? `Bulk assign thất bại: ${e.message}` : 'Bulk assign thất bại.';
		return { success: 0, failed: nodeIds.length };
	}
}

/**
 * Delete an edge/link by ID.
 * Returns true if successful.
 */
export async function deleteEdge(apiBase: string, edgeId: string): Promise<boolean> {
	// Snapshot for rollback
	const snapshotLinks = [...graphData.links];
	const snapshotNodes = graphData.nodes.map((n) => ({ ...n }));

	// Optimistic update: remove the link locally
	graphData.links = graphData.links.filter((l) => l.id !== edgeId);

	try {
		const res = await fetch(`${apiBase}/api/v1/seo/edges/${edgeId}`, {
			method: 'DELETE',
			credentials: 'include'
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		await fetchGraph(apiBase);
		return true;
	} catch (e) {
		// Rollback on failure
		graphData.links = snapshotLinks;
		graphData.nodes = snapshotNodes;
		errorMsg.value = 'Xóa liên kết thất bại. Đã rollback.';
		return false;
	}
}

/**
 * Delete a node from the SEO graph by ID.
 * Returns true if successful.
 */
export async function deleteNode(apiBase: string, nodeId: string): Promise<boolean> {
	// Snapshot for rollback
	const snapshotNodes = [...graphData.nodes];
	const snapshotLinks = [...graphData.links];

	// Optimistic update: filter out the node and its connected links
	graphData.nodes = graphData.nodes.filter((n) => n.id !== nodeId);
	graphData.links = graphData.links.filter((l) => {
		const srcId = typeof l.source === 'object' ? (l.source as GraphNode).id : l.source;
		const tgtId = typeof l.target === 'object' ? (l.target as GraphNode).id : l.target;
		return srcId !== nodeId && tgtId !== nodeId;
	});

	try {
		const res = await fetch(`${apiBase}/api/v1/seo/nodes/${nodeId}`, {
			method: 'DELETE',
			credentials: 'include'
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		await fetchGraph(apiBase);
		return true;
	} catch (e) {
		// Rollback on failure
		graphData.nodes = snapshotNodes;
		graphData.links = snapshotLinks;
		errorMsg.value = 'Xóa node khỏi đồ thị thất bại. Đã rollback.';
		return false;
	}
}


