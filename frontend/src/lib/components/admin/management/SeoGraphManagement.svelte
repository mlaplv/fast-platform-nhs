<script lang="ts">
	import { onMount } from 'svelte';
	import SeoGraphCanvas from '$lib/components/seo/SeoGraphCanvas.svelte';
	import SeoGraphSidebar from '$lib/components/seo/SeoGraphSidebar.svelte';
	import SeoGraphToolbar from '$lib/components/seo/SeoGraphToolbar.svelte';
	import {
		graphData,
		isLoading,
		errorMsg,
		fetchGraph,
		getUnclassifiedCount,
		getAiSuggestedCount,
		getPillarNodes,
		isSidebarOpen,
		batchSelectedIds,
		batchAssignPillar
	} from '$lib/stores/seoGraph.svelte';

	const API_BASE = import.meta.env.VITE_API_BASE ?? '';

	let showBatchPanel = $state(false);
	let batchTargetPillarId = $state('');
	let isBatchAssigning = $state(false);
	let batchResult = $state<{ success: number; failed: number } | null>(null);

	// Unclassified nodes for batch selection list
	const unclassifiedNodes = $derived(graphData.nodes.filter((n) => n.group === 'unclassified'));

	onMount(async () => {
		await fetchGraph(API_BASE);
	});

	async function handleRefresh() {
		await fetchGraph(API_BASE);
	}

	function toggleBatchNode(nodeId: string) {
		const next = new Set(batchSelectedIds.value);
		next.has(nodeId) ? next.delete(nodeId) : next.add(nodeId);
		batchSelectedIds.value = next;
	}

	function selectAllUnclassified() {
		batchSelectedIds.value = new Set(unclassifiedNodes.map((n) => n.id));
	}

	function clearBatchSelection() {
		batchSelectedIds.value = new Set();
		batchTargetPillarId = '';
		batchResult = null;
	}

	async function handleBatchAssign() {
		if (!batchTargetPillarId || !batchSelectedIds.value.size) return;
		isBatchAssigning = true;
		batchResult = null;
		batchResult = await batchAssignPillar(API_BASE, [...batchSelectedIds.value], batchTargetPillarId);
		isBatchAssigning = false;
		batchTargetPillarId = '';
	}
</script>

<div class="seo-graph-widget-container">
	<!-- Header Stats inside widget -->
	<header class="seo-graph-header shrink-0">
		<div class="header-left">
			<h3 class="text-sm font-bold text-white tracking-tight">Mạng lưới liên kết Pillar & Cluster</h3>
			<p class="header-subtitle">AI-powered internal linking visualizer</p>
		</div>
		<div class="header-stats">
			<div class="stat-chip pillar">
				<span class="stat-value">{graphData.meta.pillars}</span>
				<span class="stat-label">Pillars</span>
			</div>
			<div class="stat-chip cluster">
				<span class="stat-value">{graphData.meta.total_nodes - graphData.meta.pillars - getUnclassifiedCount()}</span>
				<span class="stat-label">Clusters</span>
			</div>
			<div class="stat-chip unclassified" class:alert={getUnclassifiedCount() > 0}>
				<span class="stat-value">{getUnclassifiedCount()}</span>
				<span class="stat-label">Chờ phân loại</span>
			</div>
			<div class="stat-chip ai" class:alert={getAiSuggestedCount() > 0}>
				<span class="stat-value">{getAiSuggestedCount()}</span>
				<span class="stat-label">AI đề xuất</span>
			</div>
		</div>
		{#if getUnclassifiedCount() > 0}
			<button
				class="btn-batch"
				class:active={showBatchPanel}
				onclick={() => { showBatchPanel = !showBatchPanel; clearBatchSelection(); }}
			>
				📋 Phân loại hàng loạt ({getUnclassifiedCount()})
			</button>
		{/if}
		<button class="btn-refresh" onclick={handleRefresh} disabled={isLoading.value}>
			{isLoading.value ? '⏳ Đang tải...' : '🔄 Làm mới'}
		</button>
	</header>

	<!-- Batch Assignment Panel -->
	{#if showBatchPanel}
		<div class="batch-panel shrink-0">
			<div class="batch-header">
				<span class="batch-title">📋 Gán hàng loạt vào Pillar</span>
				<div class="batch-controls">
					<button class="batch-ctrl-btn" onclick={selectAllUnclassified}>Chọn tất cả ({unclassifiedNodes.length})</button>
					<button class="batch-ctrl-btn" onclick={clearBatchSelection}>Bỏ chọn</button>
				</div>
			</div>

			<div class="batch-body">
				<div class="batch-node-list">
					{#each unclassifiedNodes as node (node.id)}
						<label class="batch-node-item" class:selected={batchSelectedIds.value.has(node.id)}>
							<input
								type="checkbox"
								checked={batchSelectedIds.value.has(node.id)}
								onchange={() => toggleBatchNode(node.id)}
							/>
							<span class="batch-node-type">{node.entity_type}</span>
							<span class="batch-node-label">{node.label}</span>
						</label>
					{/each}
					{#if unclassifiedNodes.length === 0}
						<p class="batch-empty">✅ Không có node chưa phân loại</p>
					{/if}
				</div>

				<div class="batch-actions">
					<div class="batch-selected-info">
						{batchSelectedIds.value.size} node đã chọn
					</div>
					<select class="batch-pillar-select" bind:value={batchTargetPillarId}>
						<option value="">-- Chọn Pillar đích --</option>
						{#each getPillarNodes() as p}
							<option value={p.id}>{p.label}</option>
						{/each}
					</select>
					<button
						class="batch-confirm-btn"
						onclick={handleBatchAssign}
						disabled={!batchTargetPillarId || !batchSelectedIds.value.size || isBatchAssigning}
					>
						{isBatchAssigning ? '⏳ Đang xử lý...' : '✔ Gán ' + batchSelectedIds.value.size + ' node'}
					</button>
					{#if batchResult}
						<div class="batch-result" class:ok={batchResult.failed === 0}>
							✅ {batchResult.success} thành công{batchResult.failed > 0 ? `, ⚠️ ${batchResult.failed} lỗi` : ''}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	{#if errorMsg.value}
		<div class="error-banner shrink-0">⚠️ {errorMsg.value}</div>
	{/if}

	<!-- Main Layout -->
	<div class="seo-graph-layout flex-1 min-h-0" class:full-view={!isSidebarOpen.value}>
		<!-- Toolbar -->
		<SeoGraphToolbar apiBase={API_BASE} />

		<!-- Graph Canvas -->
		<div class="canvas-wrapper">
			{#if isLoading.value && graphData.nodes.length === 0}
				<div class="loading-screen">
					<div class="loading-spinner"></div>
					<p>Đang tải SEO graph...</p>
				</div>
			{:else}
				<SeoGraphCanvas apiBase={API_BASE} />
			{/if}
		</div>

		<!-- Sidebar -->
		{#if isSidebarOpen.value}
			<SeoGraphSidebar apiBase={API_BASE} />
		{/if}
	</div>
</div>

<style>
	.seo-graph-widget-container {
		height: 100%;
		width: 100%;
		display: flex;
		flex-direction: column;
		background: #0b0b10;
		color: #e2e8f0;
	}

	.seo-graph-header {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding: 0.75rem 1.25rem;
		background: rgba(26, 26, 46, 0.4);
		border-bottom: 1px solid rgba(99, 102, 241, 0.15);
		flex-wrap: wrap;
	}

	.header-subtitle {
		font-size: 0.75rem;
		color: #475569;
		margin: 0;
	}

	.header-stats {
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
	}

	.stat-chip {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.25rem 0.6rem;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.05);
		border-radius: 9999px;
		font-size: 0.72rem;
	}
	.stat-chip.pillar {
		border-color: rgba(245, 158, 11, 0.2);
		background: rgba(245, 158, 11, 0.04);
		color: #fbbf24;
	}
	.stat-chip.cluster {
		border-color: rgba(99, 102, 241, 0.2);
		background: rgba(99, 102, 241, 0.04);
		color: #818cf8;
	}
	.stat-chip.unclassified.alert {
		border-color: rgba(239, 68, 68, 0.3);
		background: rgba(239, 68, 68, 0.08);
		color: #fca5a5;
	}
	.stat-chip.ai.alert {
		border-color: rgba(249, 115, 22, 0.3);
		background: rgba(249, 115, 22, 0.08);
		color: #fdba74;
	}

	.stat-value {
		font-weight: 700;
	}
	.stat-label {
		color: #475569;
		font-size: 0.68rem;
	}

	.btn-refresh {
		margin-left: auto;
		padding: 0.35rem 0.75rem;
		border-radius: 6px;
		background: rgba(99, 102, 241, 0.15);
		border: 1px solid rgba(99, 102, 241, 0.3);
		color: #a5b4fc;
		font-weight: 600;
		font-size: 0.72rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	.btn-refresh:hover:not(:disabled) {
		background: rgba(99, 102, 241, 0.25);
	}
	.btn-batch {
		padding: 0.35rem 0.75rem;
		border-radius: 6px;
		background: rgba(245, 158, 11, 0.08);
		border: 1px solid rgba(245, 158, 11, 0.25);
		color: #fbbf24;
		font-weight: 600;
		font-size: 0.72rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	.btn-batch.active, .btn-batch:hover {
		background: rgba(245, 158, 11, 0.18);
		border-color: rgba(245, 158, 11, 0.4);
	}

	.batch-panel {
		background: rgba(15, 15, 25, 0.98);
		border-bottom: 1px solid rgba(245, 158, 11, 0.2);
		padding: 0.75rem 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		max-height: 280px;
		overflow: hidden;
	}
	.batch-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	.batch-title {
		font-size: 0.78rem;
		font-weight: 700;
		color: #fbbf24;
	}
	.batch-controls { display: flex; gap: 0.5rem; }
	.batch-ctrl-btn {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		background: transparent;
		border: 1px solid rgba(255,255,255,0.1);
		color: #94a3b8;
		font-size: 0.68rem;
		cursor: pointer;
	}
	.batch-ctrl-btn:hover { background: rgba(255,255,255,0.05); }
	.batch-body {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 1rem;
		overflow: hidden;
	}
	.batch-node-list {
		overflowy: auto;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		max-height: 180px;
	}
	.batch-node-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.3rem 0.5rem;
		border-radius: 5px;
		cursor: pointer;
		font-size: 0.75rem;
		color: #94a3b8;
		transition: background 0.15s;
	}
	.batch-node-item:hover { background: rgba(255,255,255,0.04); }
	.batch-node-item.selected { background: rgba(245, 158, 11, 0.07); color: #e2e8f0; }
	.batch-node-type {
		padding: 0.1rem 0.35rem;
		border-radius: 3px;
		background: rgba(99,102,241,0.15);
		color: #818cf8;
		font-size: 0.62rem;
		text-transform: uppercase;
		white-space: nowrap;
	}
	.batch-node-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.batch-empty { color: #475569; font-size: 0.78rem; text-align: center; padding: 1rem; }
	.batch-actions {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		min-width: 220px;
		align-items: flex-start;
	}
	.batch-selected-info {
		font-size: 0.72rem;
		color: #64748b;
	}
	.batch-pillar-select {
		width: 100%;
		padding: 0.35rem 0.5rem;
		border-radius: 6px;
		background: #0f0f1a;
		border: 1px solid rgba(99,102,241,0.25);
		color: #e2e8f0;
		font-size: 0.75rem;
	}
	.batch-confirm-btn {
		width: 100%;
		padding: 0.4rem;
		border-radius: 6px;
		background: rgba(245, 158, 11, 0.15);
		border: 1px solid rgba(245, 158, 11, 0.35);
		color: #fbbf24;
		font-weight: 700;
		font-size: 0.75rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	.batch-confirm-btn:hover:not(:disabled) { background: rgba(245, 158, 11, 0.25); }
	.batch-confirm-btn:disabled { opacity: 0.4; cursor: not-allowed; }
	.batch-result {
		font-size: 0.72rem;
		padding: 0.3rem 0.5rem;
		border-radius: 4px;
		background: rgba(239, 68, 68, 0.08);
		color: #fca5a5;
		width: 100%;
	}
	.batch-result.ok { background: rgba(16, 185, 129, 0.08); color: #6ee7b7; }

	.btn-refresh:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.error-banner {
		padding: 0.5rem 1.25rem;
		background: rgba(239, 68, 68, 0.08);
		border-bottom: 1px solid rgba(239, 68, 68, 0.15);
		color: #fca5a5;
		font-size: 0.78rem;
		text-align: center;
	}

	.seo-graph-layout {
		display: grid;
		grid-template-columns: 1fr 320px;
		grid-template-rows: auto 1fr;
		height: 100%;
		overflow: hidden;
		transition: grid-template-columns 0.3s ease;
	}

	.seo-graph-layout.full-view {
		grid-template-columns: 1fr;
	}

	.canvas-wrapper {
		grid-column: 1;
		grid-row: 2;
		position: relative;
		background: #07070a;
		overflow: hidden;
		height: 100%;
		width: 100%;
	}

	.loading-screen {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: rgba(7, 7, 10, 0.85);
		gap: 0.75rem;
		z-index: 10;
	}

	.loading-spinner {
		width: 1.5rem;
		height: 1.5rem;
		border: 2px solid rgba(99, 102, 241, 0.15);
		border-top-color: #6366f1;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>
