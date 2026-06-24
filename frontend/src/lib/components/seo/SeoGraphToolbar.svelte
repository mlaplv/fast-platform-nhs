<script lang="ts">
	import {
		filterGroup,
		graphData,
		fetchGraph,
		selectedNodeId,
		isSidebarOpen,
		selectedPillarId,
		allPillars
	} from '$lib/stores/seoGraph.svelte';
	import type { GraphNode } from '$lib/stores/seoGraph.svelte';

	let { apiBase }: { apiBase: string } = $props();

	let searchQuery = $state('');
	let isDropdownOpen = $state(false);

	const groups = [
		{ value: 'all', label: 'Tất cả', icon: '🕸️' },
		{ value: 'pillar', label: 'Pillars', icon: '⭐' },
		{ value: 'cluster', label: 'Clusters', icon: '🔗' },
		{ value: 'unclassified', label: 'Chờ phân loại', icon: '⚠️' },
		{ value: 'ai_suggested', label: 'AI đề xuất', icon: '🤖' }
	] as const;

	const filteredSuggestions = $derived(
		searchQuery.trim() === ''
			? []
			: graphData.nodes.filter(
					(n) =>
						n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
						n.slug.toLowerCase().includes(searchQuery.toLowerCase())
			  ).slice(0, 8)
	);

	function selectNode(node: GraphNode) {
		selectedNodeId.value = node.id;
		isSidebarOpen.value = true;
		searchQuery = '';
		isDropdownOpen = false;
	}

	async function handlePillarChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		const val = target.value || null;
		selectedPillarId.value = val;
		selectedNodeId.value = null; // Clear selected node
		await fetchGraph(apiBase);
		if (val) {
			selectedNodeId.value = val;
			isSidebarOpen.value = true;
		}
	}

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
				class="filter-btn {g.value}"
				class:active={filterGroup.value === g.value}
				onclick={() => (filterGroup.value = g.value)}
				aria-pressed={filterGroup.value === g.value}
			>
				<span>{g.icon}</span>
				<span>{g.label}</span>
			</button>
		{/each}
	</div>

	<!-- Pillar sub-graph selector -->
	<div class="toolbar-divider"></div>
	<div class="pillar-selector-container">
		<select class="pillar-select" value={selectedPillarId.value || ''} onchange={handlePillarChange}>
			<option value="">🕸️ Toàn bộ đồ thị (Mạng lưới tổng)</option>
			{#each allPillars.value as p}
				<option value={p.id}>⭐ Pillar: {p.label}</option>
			{/each}
		</select>
	</div>

	<!-- Search box -->
	<div class="toolbar-divider"></div>
	<div class="search-container">
		<input
			type="text"
			placeholder="🔍 Tìm bài viết, sản phẩm..."
			bind:value={searchQuery}
			onfocus={() => (isDropdownOpen = true)}
			onblur={() => setTimeout(() => (isDropdownOpen = false), 200)}
			class="search-input"
		/>
		{#if isDropdownOpen && filteredSuggestions.length > 0}
			<div class="search-dropdown">
				{#each filteredSuggestions as node}
					<button class="suggestion-item" onclick={() => selectNode(node)}>
						<span class="type-icon">{node.is_pillar ? '⭐' : node.group === 'unclassified' ? '⚠️' : '🔗'}</span>
						<span class="label-text">{node.label}</span>
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<div class="toolbar-divider"></div>
	<div class="quick-stats">
		<span class="qs-item">{graphData.meta.total_nodes} nodes</span>
		<span class="qs-sep">·</span>
		<span class="qs-item">{graphData.meta.total_edges} edges</span>
	</div>

	<!-- Reconcile & Full View -->
	<div class="toolbar-actions">
		<button
			class="fullview-btn"
			onclick={() => (isSidebarOpen.value = !isSidebarOpen.value)}
			title="Bật/Tắt sidebar toàn cảnh"
		>
			{isSidebarOpen.value ? '👁️ Toàn cảnh' : '👁️ Hiện Sidebar'}
		</button>
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
		background: rgba(19, 19, 31, 0.95);
		border-bottom: 1px solid rgba(99, 102, 241, 0.12);
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
		border: 1px solid rgba(99, 102, 241, 0.12);
		background: rgba(255, 255, 255, 0.02);
		color: #94a3b8;
		cursor: pointer;
		font-size: 0.78rem;
		font-weight: 500;
		transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.filter-btn:hover {
		background: rgba(99, 102, 241, 0.1);
		color: #e2e8f0;
	}
	.filter-btn.active.all {
		background: rgba(99, 102, 241, 0.15);
		border-color: rgba(99, 102, 241, 0.4);
		color: #a5b4fc;
		box-shadow: 0 0 10px rgba(99, 102, 241, 0.15);
	}
	.filter-btn.active.pillar {
		background: rgba(99, 102, 241, 0.22);
		border-color: rgba(99, 102, 241, 0.5);
		color: #818cf8;
		box-shadow: 0 0 12px rgba(99, 102, 241, 0.2);
	}
	.filter-btn.active.cluster {
		background: rgba(165, 180, 252, 0.15);
		border-color: rgba(165, 180, 252, 0.45);
		color: #c7d2fe;
		box-shadow: 0 0 10px rgba(165, 180, 252, 0.15);
	}
	.filter-btn.active.unclassified {
		background: rgba(245, 158, 11, 0.15);
		border-color: rgba(245, 158, 11, 0.45);
		color: #fde047;
		box-shadow: 0 0 10px rgba(245, 158, 11, 0.15);
	}
	.filter-btn.active.ai_suggested {
		background: rgba(249, 115, 22, 0.15);
		border-color: rgba(249, 115, 22, 0.45);
		color: #fdba74;
		box-shadow: 0 0 10px rgba(249, 115, 22, 0.15);
	}

	.search-container {
		position: relative;
		display: flex;
		align-items: center;
		min-width: 240px;
	}

	.search-input {
		width: 100%;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(99, 102, 241, 0.15);
		border-radius: 6px;
		padding: 0.35rem 0.75rem;
		font-size: 0.78rem;
		color: #e2e8f0;
		outline: none;
		transition: all 0.2s;
	}

	.search-input:focus {
		border-color: rgba(99, 102, 241, 0.4);
		background: rgba(255, 255, 255, 0.08);
		box-shadow: 0 0 8px rgba(99, 102, 241, 0.15);
	}

	.search-dropdown {
		position: absolute;
		top: calc(100% + 5px);
		left: 0;
		right: 0;
		background: #13131f;
		border: 1px solid rgba(99, 102, 241, 0.25);
		border-radius: 6px;
		max-height: 250px;
		overflow-y: auto;
		z-index: 1000;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
	}

	.suggestion-item {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		background: transparent;
		border: none;
		border-bottom: 1px solid rgba(255, 255, 255, 0.03);
		color: #94a3b8;
		text-align: left;
		cursor: pointer;
		font-size: 0.75rem;
		transition: all 0.15s;
	}

	.suggestion-item:last-child {
		border-bottom: none;
	}

	.suggestion-item:hover {
		background: rgba(99, 102, 241, 0.12);
		color: #e2e8f0;
	}

	.type-icon {
		font-size: 0.8rem;
		flex-shrink: 0;
	}

	.label-text {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.toolbar-divider {
		width: 1px;
		height: 20px;
		background: rgba(99, 102, 241, 0.15);
	}

	.quick-stats {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.75rem;
		color: #475569;
	}
	.qs-sep {
		color: #334155;
	}

	.toolbar-actions {
		display: flex;
		align-items: center;
		margin-left: auto;
	}

	.fullview-btn {
		padding: 0.3rem 0.75rem;
		border-radius: 6px;
		border: 1px solid rgba(99, 102, 241, 0.25);
		background: rgba(99, 102, 241, 0.08);
		color: #a5b4fc;
		cursor: pointer;
		font-size: 0.75rem;
		margin-right: 0.5rem;
		transition: all 0.15s;
	}

	.fullview-btn:hover {
		background: rgba(99, 102, 241, 0.18);
	}

	.reconcile-btn {
		padding: 0.3rem 0.75rem;
		border-radius: 6px;
		border: 1px solid rgba(16, 185, 129, 0.2);
		background: rgba(16, 185, 129, 0.08);
		color: #6ee7b7;
		cursor: pointer;
		font-size: 0.75rem;
		transition: all 0.15s;
	}
	.reconcile-btn:hover {
		background: rgba(16, 185, 129, 0.15);
	}

	.pillar-selector-container {
		display: flex;
		align-items: center;
	}

	.pillar-select {
		background: #0f0f1c;
		border: 1px solid rgba(99, 102, 241, 0.3);
		border-radius: 6px;
		color: #e2e8f0;
		font-size: 0.78rem;
		font-weight: 500;
		padding: 0.35rem 0.75rem;
		outline: none;
		cursor: pointer;
		max-width: 250px;
		transition: all 0.2s;
	}

	.pillar-select:focus {
		border-color: #6366f1;
		box-shadow: 0 0 8px rgba(99, 102, 241, 0.25);
	}
</style>
