<script lang="ts">
	import {
		selectedNodeId,
		activeNode,
		pillarNodes,
		graphData,
		togglePillar,
		triggerMatch,
		overrideEdge
	} from '$lib/stores/seoGraph.svelte';

	let { apiBase }: { apiBase: string } = $props();

	let selectedPillarId = $state('');
	let isMatching = $state(false);
	let matchResult = $state<{ match_tier: string; ai_confidence: number | null } | null>(null);

	// Reset khi active node thay đổi
	$effect(() => {
		if (activeNode) {
			selectedPillarId = '';
			matchResult = null;
		}
	});

	// Tìm edge hiện tại của active node (source là pillar → target là node)
	const currentEdge = $derived(
		activeNode
			? graphData.links.find((l) => l.target === activeNode!.id || l.source === activeNode!.id)
			: null
	);

	async function handleTogglePillar() {
		if (!activeNode) return;
		await togglePillar(apiBase, activeNode.id, !activeNode.is_pillar, activeNode.pillar_topic ?? undefined);
	}

	async function handleReassign() {
		if (!activeNode || !selectedPillarId || !currentEdge) return;
		await overrideEdge(apiBase, currentEdge.id, selectedPillarId, activeNode.id);
	}

	async function handleManualMatch() {
		if (!activeNode) return;
		isMatching = true;
		matchResult = await triggerMatch(apiBase, activeNode.entity_type as 'article' | 'product', activeNode.entity_id);
		isMatching = false;
	}

	function getTierLabel(tier: string): string {
		const map: Record<string, string> = {
			auto: '✅ Tự động (vector)',
			ai_suggested: '🤖 AI đề xuất',
			unclassified: '⚠️ Chưa phân loại'
		};
		return map[tier] ?? tier;
	}
</script>

<div class="sidebar">
	{#if !activeNode}
		<div class="empty-hint">
			<span class="hint-icon">👆</span>
			<p>Nhấp vào một node<br />để xem chi tiết</p>
		</div>
	{:else}
		<!-- Node Info -->
		<div class="node-card" class:pillar={activeNode.is_pillar}>
			<div class="node-type-badge" class:is-pillar={activeNode.is_pillar}>
				{activeNode.is_pillar ? '⭐ Pillar Page' : activeNode.group === 'unclassified' ? '⚠️ Chưa phân loại' : '🔗 Cluster'}
			</div>
			<h2 class="node-title">{activeNode.label}</h2>
			<div class="node-meta">
				<span class="meta-chip">{activeNode.entity_type}</span>
				{#if activeNode.pillar_topic}
					<span class="meta-chip topic">{activeNode.pillar_topic}</span>
				{/if}
			</div>
			{#if activeNode.url}
				<a href={activeNode.url} target="_blank" class="node-url">
					🔗 {activeNode.slug}
				</a>
			{/if}
		</div>

		<!-- Edge Info -->
		{#if currentEdge}
			<div class="section">
				<h3 class="section-title">Liên kết hiện tại</h3>
				<div class="edge-info" class:confirmed={currentEdge.is_confirmed} class:ai={!currentEdge.is_confirmed}>
					<span class="edge-type">
						{currentEdge.is_confirmed ? '✅' : '🟠'} {currentEdge.link_type}
					</span>
					{#if currentEdge.ai_confidence !== null}
						<div class="confidence-bar">
							<div class="bar-fill" style="width:{Math.round((currentEdge.ai_confidence ?? 0) * 100)}%"></div>
							<span class="bar-label">{Math.round((currentEdge.ai_confidence ?? 0) * 100)}% confident</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Actions -->
		<div class="section">
			<h3 class="section-title">Hành động</h3>

			<!-- Toggle Pillar -->
			<button class="action-btn" class:active={activeNode.is_pillar} onclick={handleTogglePillar}>
				{activeNode.is_pillar ? '⭐ Bỏ Pillar' : '⭐ Đặt làm Pillar'}
			</button>

			<!-- Reassign Pillar -->
			{#if !activeNode.is_pillar && pillarNodes.length > 0}
				<div class="reassign-group">
					<label for="pillar-select" class="select-label">Gán vào Pillar khác</label>
					<select id="pillar-select" class="pillar-select" bind:value={selectedPillarId}>
						<option value="">-- Chọn Pillar --</option>
						{#each pillarNodes as p}
							<option value={p.id}>{p.label}</option>
						{/each}
					</select>
					<button
						class="action-btn confirm"
						onclick={handleReassign}
						disabled={!selectedPillarId || !currentEdge}
					>
						✔ Xác nhận gán
					</button>
				</div>
			{/if}

			<!-- Manual AI Match -->
			<button class="action-btn match" onclick={handleManualMatch} disabled={isMatching}>
				{isMatching ? '⏳ Đang phân tích...' : '🤖 Chạy AI Matching'}
			</button>

			{#if matchResult}
				<div class="match-result" class:success={matchResult.match_tier !== 'unclassified'}>
					<div>{getTierLabel(matchResult.match_tier)}</div>
					{#if matchResult.ai_confidence}
						<div class="match-conf">{Math.round(matchResult.ai_confidence * 100)}% confidence</div>
					{/if}
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.sidebar {
		grid-column: 2;
		grid-row: 1 / 3;
		background: #13131f;
		border-left: 1px solid rgba(99,102,241,0.15);
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.empty-hint {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 0.75rem;
		color: #475569;
		padding: 2rem;
		text-align: center;
	}
	.hint-icon { font-size: 2rem; }
	.empty-hint p { font-size: 0.85rem; line-height: 1.6; margin: 0; }

	.node-card {
		padding: 1.25rem;
		border-bottom: 1px solid rgba(99,102,241,0.1);
		background: linear-gradient(135deg, rgba(99,102,241,0.05), transparent);
	}
	.node-card.pillar { background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.05)); }

	.node-type-badge {
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #64748b;
		margin-bottom: 0.5rem;
	}
	.node-type-badge.is-pillar { color: #a5b4fc; }

	.node-title {
		font-size: 0.95rem;
		font-weight: 600;
		color: #e2e8f0;
		margin: 0 0 0.75rem;
		line-height: 1.4;
	}

	.node-meta { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
	.meta-chip {
		font-size: 0.68rem;
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		background: rgba(99,102,241,0.15);
		color: #a5b4fc;
		border: 1px solid rgba(99,102,241,0.2);
	}
	.meta-chip.topic { background: rgba(245,158,11,0.1); color: #fbbf24; border-color: rgba(245,158,11,0.2); }

	.node-url {
		font-size: 0.72rem;
		color: #6366f1;
		text-decoration: none;
		display: block;
		margin-top: 0.25rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.node-url:hover { color: #a5b4fc; }

	.section {
		padding: 1rem 1.25rem;
		border-bottom: 1px solid rgba(99,102,241,0.08);
	}
	.section-title {
		font-size: 0.72rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #475569;
		margin: 0 0 0.75rem;
	}

	.edge-info {
		padding: 0.6rem 0.8rem;
		border-radius: 8px;
		border: 1px solid;
		font-size: 0.8rem;
	}
	.edge-info.confirmed { border-color: rgba(99,102,241,0.3); background: rgba(99,102,241,0.08); }
	.edge-info.ai { border-color: rgba(249,115,22,0.3); background: rgba(249,115,22,0.08); }

	.edge-type { color: #e2e8f0; font-weight: 500; }

	.confidence-bar {
		position: relative;
		height: 4px;
		background: rgba(255,255,255,0.08);
		border-radius: 2px;
		margin-top: 0.5rem;
		overflow: hidden;
	}
	.bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #6366f1, #a5b4fc);
		border-radius: 2px;
		transition: width 0.5s ease;
	}
	.bar-label {
		position: absolute;
		right: 0;
		top: -16px;
		font-size: 0.65rem;
		color: #64748b;
	}

	.action-btn {
		width: 100%;
		padding: 0.6rem;
		border-radius: 8px;
		border: 1px solid rgba(99,102,241,0.25);
		background: rgba(99,102,241,0.1);
		color: #a5b4fc;
		cursor: pointer;
		font-size: 0.82rem;
		font-weight: 500;
		margin-bottom: 0.5rem;
		transition: all 0.2s;
		text-align: center;
	}
	.action-btn:hover:not(:disabled) {
		background: rgba(99,102,241,0.2);
		transform: translateY(-1px);
	}
	.action-btn.active { background: rgba(99,102,241,0.25); border-color: #6366f1; }
	.action-btn.confirm { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); color: #6ee7b7; }
	.action-btn.match { background: rgba(249,115,22,0.1); border-color: rgba(249,115,22,0.3); color: #fdba74; }
	.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }

	.reassign-group { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.5rem; }
	.select-label { font-size: 0.72rem; color: #64748b; }
	.pillar-select {
		width: 100%;
		padding: 0.5rem;
		border-radius: 6px;
		background: #1a1a2e;
		border: 1px solid rgba(99,102,241,0.2);
		color: #e2e8f0;
		font-size: 0.8rem;
	}

	.match-result {
		padding: 0.6rem;
		border-radius: 8px;
		background: rgba(239,68,68,0.1);
		border: 1px solid rgba(239,68,68,0.2);
		font-size: 0.8rem;
		color: #fca5a5;
	}
	.match-result.success {
		background: rgba(16,185,129,0.1);
		border-color: rgba(16,185,129,0.2);
		color: #6ee7b7;
	}
	.match-conf { font-size: 0.7rem; color: #64748b; margin-top: 0.2rem; }
</style>
