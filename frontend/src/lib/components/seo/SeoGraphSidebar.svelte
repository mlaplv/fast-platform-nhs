<script lang="ts">
	import {
		selectedNodeId,
		getActiveNode,
		getPillarNodes,
		graphData,
		togglePillar,
		triggerMatch,
		overrideEdge,
		isSidebarOpen,
		deleteEdge,
		deleteNode,
		type GraphNode
	} from '$lib/stores/seoGraph.svelte';
	import { apiClient } from '$lib/utils/apiClient';

	let { apiBase }: { apiBase: string } = $props();

	let selectedPillarId = $state('');
	let isMatching = $state(false);
	let matchResult = $state<{ match_tier: string; ai_confidence: number | null } | null>(null);
	let showReviewModal = $state(false);
	let isAutoLinking = $state(false);
	let notification = $state<{ message: string; type: 'success' | 'error' } | null>(null);

	import SeoContextualLinkReview from './SeoContextualLinkReview.svelte';

	// Auto clear notification after 5s
	$effect(() => {
		if (notification) {
			const timer = setTimeout(() => {
				notification = null;
			}, 5000);
			return () => clearTimeout(timer);
		}
	});

	async function handleAutoLink() {
		if (!getActiveNode()?.is_pillar) return;
		isAutoLinking = true;
		notification = null;
		try {
			const data = await apiClient.post<any>(`/seo/contextual-links/pillar/${getActiveNode()!.id}/auto-link`, {});
			if (data && !data.error) {
				notification = {
					message: data.message || 'Đã kích hoạt chạy Auto Link thành công.',
					type: 'success'
				};
			} else {
				notification = {
					message: data.message || 'Có lỗi xảy ra khi kích hoạt Auto Link.',
					type: 'error'
				};
			}
		} catch (err: any) {
			console.error('[AutoLink] Error:', err);
			notification = {
				message: err.message || 'Không thể kết nối đến máy chủ API.',
				type: 'error'
			};
		} finally {
			isAutoLinking = false;
		}
	}

	// Reset khi active node thay đổi
	$effect(() => {
		if (getActiveNode()) {
			selectedPillarId = '';
			matchResult = null;
		}
	});

	// Tìm edge hiện tại của active node (source là pillar → target là node)
	const currentEdge = $derived(
		getActiveNode()
			? graphData.links.find((l) => l.target === getActiveNode()!.id || l.source === getActiveNode()!.id)
			: null
	);

	async function handleTogglePillar() {
		if (!getActiveNode()) return;
		await togglePillar(apiBase, getActiveNode()!.id, !getActiveNode()!.is_pillar, getActiveNode()!.pillar_topic ?? undefined);
	}

	async function handleReassign() {
		if (!getActiveNode() || !selectedPillarId || !currentEdge) return;
		await overrideEdge(apiBase, currentEdge.id, selectedPillarId, getActiveNode()!.id);
	}

	async function handleManualMatch() {
		if (!getActiveNode()) return;
		isMatching = true;
		matchResult = await triggerMatch(apiBase, getActiveNode()!.entity_type as 'article' | 'product', getActiveNode()!.entity_id);
		isMatching = false;
	}

	async function handleDeleteLink() {
		if (!currentEdge) return;
		const success = await deleteEdge(apiBase, currentEdge.id);
		if (success) {
			selectedNodeId.value = null; // Deselect node sau khi gỡ
		}
	}

	let childClusters = $derived.by(() => {
		const active = getActiveNode();
		if (!active || !active.is_pillar) return [];
		const activeId = active.id;
		return graphData.links
			.filter((l) => {
			const srcId = typeof l.source === 'object' ? (l.source as GraphNode).id : l.source;
				return srcId === activeId;
			})
			.map((l) => {
				const tgtId = typeof l.target === 'object' ? (l.target as GraphNode).id : l.target;
				const targetNode = graphData.nodes.find((n) => n.id === tgtId);
				return {
					edgeId: l.id,
					node: targetNode || { label: 'Không xác định', id: tgtId }
				};
			});
	});

	async function handleDeleteChildLink(edgeId: string) {
		await deleteEdge(apiBase, edgeId);
	}

	async function handleDeleteNode() {
		if (!getActiveNode()) return;
		if (confirm(`Bạn có chắc muốn xóa node "${getActiveNode()!.label}" khỏi đồ thị SEO không? (Điều này không ảnh hưởng đến nội dung bài viết gốc trên trang web)`)) {
			const success = await deleteNode(apiBase, getActiveNode()!.id);
			if (success) {
				selectedNodeId.value = null;
			}
		}
	}

	function getTierLabel(tier: string): string {
		const map: Record<string, string> = {
			auto: '✅ Tự động (vector)',
			ai_suggested: '🤖 AI đề xuất',
			unclassified: '⚠️ Chưa phân loại'
		};
		return map[tier] ?? tier;
	}

	function getLinkTypeLabel(type: string): string {
		const map: Record<string, string> = {
			pillar_cluster: 'Cluster chính',
			related: 'Liên kết liên quan',
			manual: 'Gán thủ công',
			ai_suggested: 'AI đề xuất (Chờ duyệt)'
		};
		return map[type] ?? type;
	}
</script>

<div class="sidebar">
	{#if !getActiveNode()}
		<div class="empty-hint">
			<button class="collapse-btn absolute" onclick={() => (isSidebarOpen.value = false)} title="Thu gọn sidebar">
				✕
			</button>
			<span class="hint-icon">👆</span>
			<p>Nhấp vào một node<br />để xem chi tiết</p>
		</div>
	{:else}
		<!-- Node Info -->
		<div class="node-card" class:pillar={getActiveNode()?.is_pillar}>
			<div class="header-row">
				<div class="node-type-badge" class:is-pillar={getActiveNode()?.is_pillar}>
					{getActiveNode()?.is_pillar ? '⭐ Pillar Page' : getActiveNode()?.group === 'unclassified' ? '⚠️ Chưa phân loại' : '🔗 Cluster'}
				</div>
				<button class="collapse-btn" onclick={() => (isSidebarOpen.value = false)} title="Thu gọn sidebar">
					✕
				</button>
			</div>
			<h2 class="node-title">{getActiveNode()?.label}</h2>
			<div class="node-meta">
				<span class="meta-chip">{getActiveNode()?.entity_type}</span>
				{#if getActiveNode()?.pillar_topic}
					<span class="meta-chip topic">{getActiveNode()?.pillar_topic}</span>
				{/if}
			</div>
			{#if getActiveNode()?.url}
				<a href={getActiveNode()?.url} target="_blank" class="node-url">
					🔗 {getActiveNode()?.slug}
				</a>
			{/if}
		</div>

		<!-- Notification Banner -->
		{#if notification}
			<div class="notification-banner {notification.type}">
				{notification.message}
			</div>
		{/if}

		<!-- Edge Info -->
		{#if currentEdge}
			<div class="section">
				<h3 class="section-title">Liên kết hiện tại</h3>
				<div class="edge-info" class:confirmed={currentEdge.is_confirmed} class:ai={!currentEdge.is_confirmed}>
					<span class="edge-type">
						{currentEdge.is_confirmed ? '✅' : '🟠'} {getLinkTypeLabel(currentEdge.link_type)}
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
			<button class="action-btn" class:active={getActiveNode()?.is_pillar} onclick={handleTogglePillar}>
				{getActiveNode()?.is_pillar ? '⭐ Bỏ Pillar' : '⭐ Đặt làm Pillar'}
			</button>

			{#if getActiveNode()?.is_pillar}
				<button class="action-btn review" onclick={() => showReviewModal = true}>
					📋 Xem SGE Links về Pillar
				</button>
				<button class="action-btn auto-link" onclick={handleAutoLink} disabled={isAutoLinking}>
					{isAutoLinking ? '⏳ Đang quét đề xuất...' : '⚡ AI tìm đề xuất từ Clusters'}
				</button>
			{/if}

			<!-- Reassign Pillar -->
			{#if !getActiveNode()?.is_pillar && getPillarNodes().length > 0}
				<div class="reassign-group">
					<label for="pillar-select" class="select-label">Gán vào Pillar khác</label>
					<select id="pillar-select" class="pillar-select" bind:value={selectedPillarId}>
						<option value="">-- Chọn Pillar --</option>
						{#each getPillarNodes() as p}
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
			{#if !getActiveNode()?.is_pillar}
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

				<!-- Contextual Link Review for Articles -->
				{#if getActiveNode()?.entity_type?.toLowerCase() === 'article'}
					<button class="action-btn review" onclick={() => showReviewModal = true}>
						📋 Xem SGE Contextual Links
					</button>
				{/if}
			{/if}

			<!-- Delete Link (Gỡ khỏi Cluster) -->
			{#if currentEdge && getActiveNode()?.group === 'cluster'}
				<button class="action-btn delete-link" onclick={handleDeleteLink}>
					✕ Gỡ khỏi Cluster (Xóa liên kết)
				</button>
			{/if}

			<!-- Delete Node (Xóa khỏi đồ thị) -->
			<button class="action-btn delete-node" onclick={handleDeleteNode}>
				🗑 Xóa khỏi Đồ thị SEO
			</button>
		</div>

		<!-- Child Clusters List (If Pillar) -->
		{#if getActiveNode()?.is_pillar}
			<div class="section child-section">
				<h3 class="section-title">Các Cluster liên kết ({childClusters.length})</h3>
				{#if childClusters.length === 0}
					<p class="empty-child-text">Chưa có cluster con nào liên kết.</p>
				{:else}
					<div class="child-clusters-list">
						{#each childClusters as child}
							<div class="child-cluster-item">
								<span class="child-label" title={child.node.label}>{child.node.label}</span>
								<button class="remove-child-btn" onclick={() => handleDeleteChildLink(child.edgeId)} title="Gỡ liên kết">
									✕
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}

		<!-- AI SEO TIP -->
		<div class="ai-tip-card">
			<div class="tip-title">💡 Triết lý AI Matching</div>
			<p class="tip-content">
				Hệ thống AI của bạn phải nhận diện được các thực thể (Thương hiệu, Tính năng, Nỗi đau của khách hàng) chứ không chỉ đếm số lần xuất hiện của từ khóa.
			</p>
		</div>
	{/if}
</div>

{#if showReviewModal && getActiveNode()}
	{#if getActiveNode()!.is_pillar}
		<SeoContextualLinkReview
			apiBase={apiBase}
			pillarId={getActiveNode()!.id}
			reviewMode="pillar"
			onClose={() => showReviewModal = false}
		/>
	{:else}
		<SeoContextualLinkReview
			apiBase={apiBase}
			articleId={getActiveNode()!.entity_id}
			reviewMode="article"
			onClose={() => showReviewModal = false}
		/>
	{/if}
{/if}

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
		position: relative;
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

	.header-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.5rem;
		width: 100%;
	}

	.collapse-btn {
		background: transparent;
		border: none;
		color: #475569;
		cursor: pointer;
		font-size: 0.75rem;
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		transition: all 0.15s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.collapse-btn:hover {
		color: #e2e8f0;
		background: rgba(255, 255, 255, 0.05);
	}
	.collapse-btn.absolute {
		position: absolute;
		top: 0.75rem;
		right: 0.75rem;
	}

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
	.action-btn.delete-link { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.3); color: #fca5a5; }
	.action-btn.delete-link:hover:not(:disabled) { background: rgba(239,68,68,0.2); border-color: rgba(239,68,68,0.5); }
	.action-btn.review { background: rgba(139, 92, 246, 0.1); border-color: rgba(139, 92, 246, 0.3); color: #c084fc; }
	.action-btn.review:hover:not(:disabled) { background: rgba(139, 92, 246, 0.2); }
	.action-btn.auto-link { background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3); color: #fbbf24; }
	.action-btn.auto-link:hover:not(:disabled) { background: rgba(245, 158, 11, 0.2); }
	.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }

	.notification-banner {
		margin: 0.75rem 1.25rem 0;
		padding: 0.6rem 0.8rem;
		border-radius: 6px;
		font-size: 0.75rem;
		line-height: 1.4;
		border: 1px solid;
		animation: fadeIn 0.2s ease-in-out;
	}
	.notification-banner.success {
		background: rgba(16, 185, 129, 0.08);
		border-color: rgba(16, 185, 129, 0.25);
		color: #6ee7b7;
	}
	.notification-banner.error {
		background: rgba(239, 68, 68, 0.08);
		border-color: rgba(239, 68, 68, 0.25);
		color: #fca5a5;
	}
	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(-5px); }
		to { opacity: 1; transform: translateY(0); }
	}

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

	.ai-tip-card {
		margin: 1.25rem;
		padding: 0.85rem 1rem;
		background: rgba(99, 102, 241, 0.04);
		border: 1px dashed rgba(99, 102, 241, 0.2);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}
	.tip-title {
		font-size: 0.75rem;
		font-weight: 600;
		color: #a5b4fc;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}
	.tip-content {
		font-size: 0.72rem;
		color: #94a3b8;
		line-height: 1.5;
		margin: 0;
	}

	.action-btn.delete-node {
		background: rgba(239, 68, 68, 0.08);
		border-color: rgba(239, 68, 68, 0.25);
		color: #fca5a5;
		margin-top: 0.5rem;
	}
	.action-btn.delete-node:hover:not(:disabled) {
		background: rgba(239, 68, 68, 0.18);
		border-color: rgba(239, 68, 68, 0.5);
	}

	.child-section {
		margin-top: 1.25rem;
		border-top: 1px solid rgba(255, 255, 255, 0.06);
		padding-top: 1rem;
	}
	.empty-child-text {
		font-size: 0.75rem;
		color: #64748b;
		font-style: italic;
		padding: 0 1.25rem;
		margin: 0.25rem 0 0 0;
	}
	.child-clusters-list {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
		padding: 0 1.25rem;
		max-height: 240px;
		overflow-y: auto;
	}
	.child-cluster-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.05);
		border-radius: 6px;
		padding: 0.45rem 0.65rem;
		gap: 0.5rem;
	}
	.child-label {
		font-size: 0.75rem;
		color: #cbd5e1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		flex: 1;
	}
	.remove-child-btn {
		background: transparent;
		border: none;
		color: #ef4444;
		font-size: 0.8rem;
		cursor: pointer;
		padding: 0 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0.65;
		transition: all 0.2s;
	}
	.remove-child-btn:hover {
		opacity: 1;
		transform: scale(1.15);
	}
</style>
