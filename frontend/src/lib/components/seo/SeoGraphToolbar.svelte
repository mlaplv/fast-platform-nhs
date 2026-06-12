<script lang="ts">
	import { filterGroup, graphData, fetchGraph } from '$lib/stores/seoGraph.svelte';

	let { apiBase }: { apiBase: string } = $props();

	const groups = [
		{ value: 'all', label: 'Tất cả', icon: '🕸️' },
		{ value: 'pillar', label: 'Pillars', icon: '⭐' },
		{ value: 'cluster', label: 'Clusters', icon: '🔗' },
		{ value: 'unclassified', label: 'Chưa phân loại', icon: '⚠️' }
	] as const;

	async function handleReconcile() {
		const res = await fetch(`${apiBase}/api/v1/seo/reconcile`, {
			method: 'POST',
			credentials: 'include'
		});
		if (res.ok) await fetchGraph(apiBase);
	}
</script>

<div class="toolbar" role="toolbar" aria-label="SEO Graph Toolbar">
	<!-- Group filter -->
	<div class="filter-group" role="group" aria-label="Lọc theo nhóm">
		{#each groups as g}
			<button
				class="filter-btn"
				class:active={filterGroup.value === g.value}
				onclick={() => (filterGroup.value = g.value)}
				aria-pressed={filterGroup.value === g.value}
			>
				<span>{g.icon}</span>
				<span>{g.label}</span>
			</button>
		{/each}
	</div>

	<!-- Stats quick view -->
	<div class="toolbar-divider"></div>
	<div class="quick-stats">
		<span class="qs-item">{graphData.meta.total_nodes} nodes</span>
		<span class="qs-sep">·</span>
		<span class="qs-item">{graphData.meta.total_edges} edges</span>
	</div>

	<!-- Reconcile -->
	<div class="toolbar-actions">
		<button class="reconcile-btn" onclick={handleReconcile} title="Dọn dẹp orphan nodes ngay">
			🧹 Dọn dẹp
		</button>
	</div>
</div>

<style>
	.toolbar {
		grid-column: 1;
		grid-row: 1;
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.6rem 1rem;
		background: rgba(19,19,31,0.95);
		border-bottom: 1px solid rgba(99,102,241,0.12);
		flex-wrap: wrap;
	}

	.filter-group {
		display: flex;
		gap: 0.3rem;
	}

	.filter-btn {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.3rem 0.7rem;
		border-radius: 6px;
		border: 1px solid rgba(99,102,241,0.15);
		background: transparent;
		color: #64748b;
		cursor: pointer;
		font-size: 0.78rem;
		font-weight: 500;
		transition: all 0.15s;
	}
	.filter-btn:hover { background: rgba(99,102,241,0.1); color: #a5b4fc; }
	.filter-btn.active {
		background: rgba(99,102,241,0.2);
		border-color: rgba(99,102,241,0.4);
		color: #a5b4fc;
	}

	.toolbar-divider {
		width: 1px;
		height: 20px;
		background: rgba(99,102,241,0.15);
	}

	.quick-stats {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.75rem;
		color: #475569;
	}
	.qs-sep { color: #334155; }

	.toolbar-actions { margin-left: auto; }

	.reconcile-btn {
		padding: 0.3rem 0.75rem;
		border-radius: 6px;
		border: 1px solid rgba(16,185,129,0.2);
		background: rgba(16,185,129,0.08);
		color: #6ee7b7;
		cursor: pointer;
		font-size: 0.75rem;
		transition: all 0.15s;
	}
	.reconcile-btn:hover { background: rgba(16,185,129,0.15); }
</style>
