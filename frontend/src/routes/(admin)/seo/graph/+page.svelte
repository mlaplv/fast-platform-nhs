<script lang="ts">
	import { onMount } from 'svelte';
	import type { PageData } from './$types';
	import SeoGraphCanvas from '$lib/components/seo/SeoGraphCanvas.svelte';
	import SeoGraphSidebar from '$lib/components/seo/SeoGraphSidebar.svelte';
	import SeoGraphToolbar from '$lib/components/seo/SeoGraphToolbar.svelte';
	import {
		graphData,
		isLoading,
		errorMsg,
		fetchGraph,
		pillarNodes,
		unclassifiedCount,
		aiSuggestedCount
	} from '$lib/stores/seoGraph.svelte';

	let { data }: { data: PageData } = $props();

	const API_BASE = import.meta.env.VITE_API_BASE ?? '';

	// Hydrate store with SSR data on mount
	$effect(() => {
		if (data.graphData) {
			graphData.meta = data.graphData.meta;
			graphData.nodes = data.graphData.nodes;
			graphData.links = data.graphData.links;
		}
	});

	async function handleRefresh() {
		await fetchGraph(API_BASE);
	}
</script>

<svelte:head>
	<title>SEO Pillar & Cluster Network | Admin</title>
	<meta name="description" content="Quản lý mạng lưới liên kết Pillar & Cluster cho SEO nội trang." />
</svelte:head>

<div class="seo-graph-page">
	<!-- Header -->
	<header class="seo-graph-header">
		<div class="header-left">
			<h1>🕸️ SEO Pillar & Cluster Network</h1>
			<p class="header-subtitle">Mạng lưới liên kết nội trang tự động</p>
		</div>
		<div class="header-stats">
			<div class="stat-chip pillar">
				<span class="stat-value">{graphData.meta.pillars}</span>
				<span class="stat-label">Pillars</span>
			</div>
			<div class="stat-chip cluster">
				<span class="stat-value">{graphData.meta.total_nodes - graphData.meta.pillars - unclassifiedCount}</span>
				<span class="stat-label">Clusters</span>
			</div>
			<div class="stat-chip unclassified" class:alert={unclassifiedCount > 0}>
				<span class="stat-value">{unclassifiedCount}</span>
				<span class="stat-label">Chờ phân loại</span>
			</div>
			<div class="stat-chip ai" class:alert={aiSuggestedCount > 0}>
				<span class="stat-value">{aiSuggestedCount}</span>
				<span class="stat-label">AI đề xuất</span>
			</div>
		</div>
		<button class="btn-refresh" onclick={handleRefresh} disabled={isLoading.value}>
			{isLoading.value ? '⏳ Đang tải...' : '🔄 Làm mới'}
		</button>
	</header>

	{#if errorMsg.value}
		<div class="error-banner">⚠️ {errorMsg.value}</div>
	{/if}

	<!-- Main Layout -->
	<div class="seo-graph-layout">
		<!-- Toolbar -->
		<SeoGraphToolbar apiBase={API_BASE} />

		<!-- Graph Canvas -->
		<div class="canvas-wrapper">
			{#if isLoading.value && graphData.nodes.length === 0}
				<div class="loading-screen">
					<div class="loading-spinner"></div>
					<p>Đang tải SEO graph...</p>
				</div>
			{:else if graphData.nodes.length === 0}
				<div class="empty-state">
					<div class="empty-icon">🕸️</div>
					<h3>Graph chưa có dữ liệu</h3>
					<p>Đăng ký bài viết hoặc sản phẩm vào SEO graph để bắt đầu.</p>
				</div>
			{:else}
				<SeoGraphCanvas apiBase={API_BASE} />
			{/if}
		</div>

		<!-- Sidebar -->
		<SeoGraphSidebar apiBase={API_BASE} />
	</div>
</div>

<style>
	.seo-graph-page {
		display: flex;
		flex-direction: column;
		height: 100vh;
		background: #0f0f17;
		color: #e2e8f0;
		font-family: 'Inter', system-ui, sans-serif;
	}

	.seo-graph-header {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding: 1rem 1.5rem;
		background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
		border-bottom: 1px solid rgba(99, 102, 241, 0.2);
		flex-wrap: wrap;
	}

	.header-left h1 {
		font-size: 1.25rem;
		font-weight: 700;
		margin: 0;
		background: linear-gradient(135deg, #a5b4fc, #6366f1);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.header-subtitle {
		font-size: 0.75rem;
		color: #64748b;
		margin: 0;
	}

	.header-stats {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		margin-left: auto;
	}

	.stat-chip {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.4rem 0.8rem;
		border-radius: 8px;
		min-width: 70px;
		border: 1px solid rgba(255,255,255,0.08);
		transition: all 0.2s;
	}
	.stat-chip.pillar { background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.3); }
	.stat-chip.cluster { background: rgba(165,180,252,0.1); }
	.stat-chip.unclassified { background: rgba(245,158,11,0.1); }
	.stat-chip.ai { background: rgba(249,115,22,0.1); }
	.stat-chip.alert { animation: pulse-alert 2s infinite; }

	@keyframes pulse-alert {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	.stat-value {
		font-size: 1.25rem;
		font-weight: 700;
	}
	.stat-label {
		font-size: 0.65rem;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.btn-refresh {
		padding: 0.5rem 1rem;
		border-radius: 8px;
		background: rgba(99,102,241,0.2);
		color: #a5b4fc;
		border: 1px solid rgba(99,102,241,0.3);
		cursor: pointer;
		font-size: 0.85rem;
		transition: all 0.2s;
	}
	.btn-refresh:hover:not(:disabled) {
		background: rgba(99,102,241,0.35);
		transform: translateY(-1px);
	}
	.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }

	.error-banner {
		padding: 0.75rem 1.5rem;
		background: rgba(239,68,68,0.15);
		border-bottom: 1px solid rgba(239,68,68,0.3);
		color: #fca5a5;
		font-size: 0.85rem;
	}

	.seo-graph-layout {
		display: grid;
		grid-template-columns: 1fr 320px;
		grid-template-rows: auto 1fr;
		flex: 1;
		overflow: hidden;
	}

	.canvas-wrapper {
		grid-column: 1;
		grid-row: 2;
		position: relative;
		overflow: hidden;
		background: radial-gradient(ellipse at center, #1a1a2e 0%, #0f0f17 100%);
	}

	.loading-screen, .empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 1rem;
		color: #475569;
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid rgba(99,102,241,0.2);
		border-top-color: #6366f1;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin { to { transform: rotate(360deg); } }

	.empty-icon { font-size: 3rem; }
	.empty-state h3 { font-size: 1.1rem; color: #64748b; margin: 0; }
	.empty-state p { font-size: 0.85rem; color: #475569; margin: 0; text-align: center; max-width: 300px; }
</style>
