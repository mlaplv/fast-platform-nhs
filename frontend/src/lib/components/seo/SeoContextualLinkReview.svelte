<script lang="ts">
	import { onMount } from 'svelte';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Edit2 from '@lucide/svelte/icons/edit-2';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import HelpCircle from '@lucide/svelte/icons/help-circle';
	import Link2 from '@lucide/svelte/icons/link-2';
	import type { Article } from '$lib/types';
	import { useNanobot } from '$lib/state/nanobot.svelte';
	import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
	import { apiClient } from '$lib/utils/apiClient';

	export interface SeoContextualLink {
		id: string;
		status: 'pending' | 'approved' | 'rejected' | 'applied';
		matched_entity_type: string;
		matched_entity_name: string;
		target_url: string;
		target_label: string | null;
		ai_confidence: number;
		original_sentence: string;
		linked_sentence: string;
		link_rel: string | null;
		anchor_text: string;
		ai_reasoning: string | null;
	}

	export interface LinkStats {
		pending: number;
		approved: number;
		rejected: number;
		applied: number;
	}

	export interface ReviewWidgetData {
		article_id?: string;
	}

	let {
		apiBase = import.meta.env.VITE_API_BASE ?? '',
		articleId = '',
		pillarId = '',
		reviewMode = 'article', // 'article' | 'pillar'
		data = null,
		isWidget = false,
		onClose = () => {}
	}: {
		apiBase?: string;
		articleId?: string;
		pillarId?: string;
		reviewMode?: 'article' | 'pillar';
		data?: ReviewWidgetData | null;
		isWidget?: boolean;
		onClose?: () => void;
	} = $props();

	const nanobot = useNanobot();

	// Component states
	let isLoading = $state(false);
	let isActioning = $state(false);
	let articleTitle = $state('');
	let isStale = $state(false);
	let links = $state<SeoContextualLink[]>([]);
	let stats = $state<LinkStats>({ pending: 0, approved: 0, rejected: 0, applied: 0 });
	let errorMessage = $state<string | null>(null);
	let successMessage = $state<string | null>(null);
	let articlesList = $state<Article[]>([]);

	// Filtering / sorting
	let statusFilter = $state<'all' | 'pending' | 'approved' | 'rejected' | 'applied'>('all');
	let offset = $state(0);
	const limit = 20;
	let hasMore = $state(true);
	
	// Link editing state
	let editingLinkId = $state<string | null>(null);
	let editingAnchorText = $state('');
	let editingTargetUrl = $state('');
	let editingRel = $state('');
	let editingTitle = $state('');
	let editingTarget = $state('');

	// Active targets
	let activeArticleId = $state<string>(articleId);
	let activePillarId = $state<string>(pillarId);

	// Custom Autocomplete Dropdown States
	let searchQuery = $state('');
	let showDropdown = $state(false);
	let articleLimit = 20;
	let articleOffset = $state(0);
	let isFetchingArticles = $state(false);
	let hasMoreArticles = $state(true);
	let debounceTimeout: ReturnType<typeof setTimeout>;

	const selectedArticleTitle = $derived(
		articlesList.find((a) => a.id === activeArticleId)?.title || '-- Chọn bài viết cần duyệt link SGE --'
	);

	const filteredLinks = $derived<SeoContextualLink[]>(
		(reviewMode === 'article' && !activeArticleId)
			? links
			: (statusFilter === 'all' ? links : links.filter((l) => l.status === statusFilter))
	);

	// Sync active targets with props
	$effect(() => {
		if (reviewMode === 'article') {
			if (data && data.article_id) {
				activeArticleId = data.article_id;
			} else if (articleId) {
				activeArticleId = articleId;
			}
		} else {
			if (data && data.pillar_id) {
				activePillarId = data.pillar_id;
			} else if (pillarId) {
				activePillarId = pillarId;
			}
		}
	});

	$effect(() => {
		if (reviewMode === 'article') {
			if (activeArticleId) {
				fetchContextualLinks();
			} else {
				links = [];
				stats = { pending: 0, approved: 0, rejected: 0, applied: 0 };
				isStale = false;
				articleTitle = '';
			}
		} else {
			if (activePillarId) {
				fetchContextualLinks();
			} else {
				links = [];
				stats = { pending: 0, approved: 0, rejected: 0, applied: 0 };
				isStale = false;
				articleTitle = '';
			}
		}
	});

	onMount(async () => {
		if (reviewMode === 'article') {
			await fetchArticles();
		}
	});

	async function fetchArticles(append = false) {
		if (isFetchingArticles) return;
		isFetchingArticles = true;
		
		if (!append) {
			articleOffset = 0;
			hasMoreArticles = true;
		}

		try {
			const queryParams = new URLSearchParams({
				limit: String(articleLimit),
				offset: String(articleOffset),
				category: 'Bài viết'
			});
			if (searchQuery.trim()) {
				queryParams.append('search', searchQuery.trim());
			}

			const result = await apiClient.get<any>(`/articles?${queryParams.toString()}`);
			const fetched = (result.data || []) as Article[];

			if (append) {
				const existingIds = new Set(articlesList.map(a => a.id));
				articlesList = [...articlesList, ...fetched.filter(a => !existingIds.has(a.id))];
			} else {
				articlesList = fetched;
			}

			hasMoreArticles = fetched.length >= articleLimit;
		} catch (e) {
			console.error('Error fetching articles:', e);
		} finally {
			isFetchingArticles = false;
		}
	}

	function handleSearchInput(e: Event) {
		const target = e.target as HTMLInputElement;
		searchQuery = target.value;
		
		clearTimeout(debounceTimeout);
		debounceTimeout = setTimeout(() => {
			fetchArticles(false);
		}, 300);
	}

	async function loadMoreArticles() {
		if (!hasMoreArticles || isFetchingArticles) return;
		articleOffset += articleLimit;
		await fetchArticles(true);
	}

	async function fetchContextualLinks(append = false) {
		isLoading = true;
		errorMessage = null;
		try {
			if (reviewMode === 'article') {
				if (activeArticleId) {
					const resData = await apiClient.get<any>(`/seo/contextual-links/${activeArticleId}`);
					articleTitle = resData.article_title as string;
					isStale = resData.is_stale as boolean;
					links = (resData.links || []) as SeoContextualLink[];
					stats = (resData.stats || { pending: 0, approved: 0, rejected: 0, applied: 0 }) as LinkStats;
					hasMore = false;
				} else {
					const statusParam = statusFilter === 'all' ? '' : `&status=${statusFilter}`;
					const resData = await apiClient.get<any>(`/seo/contextual-links?limit=${limit}&offset=${offset}${statusParam}`);
					articleTitle = 'Tất cả bài viết SGE';
					isStale = false;
					
					const newLinks = (resData.links || []) as SeoContextualLink[];
					if (append) {
						links = [...links, ...newLinks];
					} else {
						links = newLinks;
					}
					
					stats = (resData.stats || { pending: 0, approved: 0, rejected: 0, applied: 0 }) as LinkStats;
					hasMore = newLinks.length === limit;
				}
			} else {
				if (!activePillarId) return;
				const resData = await apiClient.get<any>(`/seo/contextual-links/pillar/${activePillarId}`);
				articleTitle = `Pillar: ${resData.pillar_title as string}`;
				isStale = false;
				links = (resData.links || []) as SeoContextualLink[];
				stats = (resData.stats || { pending: 0, approved: 0, rejected: 0, applied: 0 }) as LinkStats;
				hasMore = false;
			}
		} catch (e) {
			errorMessage = e instanceof Error ? e.message : 'Không thể tải đề xuất liên kết.';
			nanobot.showToast(errorMessage, 'error');
		} finally {
			isLoading = false;
		}
	}

	function handleLoadMore() {
		if (isLoading || !hasMore) return;
		offset += limit;
		fetchContextualLinks(true);
	}

	async function handleUpdateStatus(linkId: string, status: 'approved' | 'rejected') {
		isActioning = true;
		errorMessage = null;
		successMessage = null;
		try {
			const result = await apiClient.patch<any>(`/seo/contextual-links/${linkId}`, { status });
			if (result.data?.error) {
				errorMessage = result.message as string;
				nanobot.showToast(errorMessage, 'error');
			} else {
				// Fast local update with Svelte 5 deep state re-assignment
				const index = links.findIndex((l) => l.id === linkId);
				if (index !== -1) {
					const oldStatus = links[index].status;
					if (oldStatus !== status) {
						stats[oldStatus as keyof LinkStats]--;
						stats[status]++;
						// Re-assign object to trigger deep reactivity
						links[index] = { ...links[index], status };
						// Re-assign array and stats to force re-render
						links = [...links];
						stats = { ...stats };
					}
				}
				const actionText = status === 'approved' ? 'duyệt' : 'từ chối';
				nanobot.showToast(`Đã ${actionText} liên kết thành công!`, 'success');
			}
		} catch (e) {
			errorMessage = e instanceof Error ? e.message : 'Không thể cập nhật trạng thái.';
			nanobot.showToast(errorMessage, 'error');
		} finally {
			isActioning = false;
		}
	}

	function startEditing(link: SeoContextualLink) {
		editingLinkId = link.id;
		editingAnchorText = link.anchor_text;
		editingTargetUrl = link.target_url;
		editingRel = link.link_rel || '';
		editingTitle = link.link_title || '';
		editingTarget = link.link_target || '';
	}

	async function handleSaveEdit(linkId: string) {
		if (!editingAnchorText.trim()) return;
		isActioning = true;
		errorMessage = null;
		successMessage = null;
		try {
			const result = await apiClient.patch<any>(`/seo/contextual-links/${linkId}`, {
				anchor_text: editingAnchorText,
				target_url: editingTargetUrl,
				link_rel: editingRel || null,
				link_title: editingTitle || null,
				link_target: editingTarget || null
			});
			
			if (result.data?.error) {
				errorMessage = result.message as string;
				nanobot.showToast(errorMessage, 'error');
			} else {
				// Update locally with Svelte 5 deep state re-assignment
				const index = links.findIndex((l) => l.id === linkId);
				if (index !== -1) {
					const updatedLink = { ...links[index] };
					updatedLink.anchor_text = editingAnchorText;
					updatedLink.target_url = editingTargetUrl;
					updatedLink.link_rel = editingRel || null;
					updatedLink.link_title = editingTitle || null;
					updatedLink.link_target = editingTarget || null;
					
					// Rebuild linked sentence for UI
					const attrs = [];
					if (updatedLink.link_rel && updatedLink.link_rel !== 'dofollow') {
						attrs.push(`rel="${updatedLink.link_rel}"`);
					}
					if (updatedLink.link_title) {
						attrs.push(`title="${updatedLink.link_title}"`);
					}
					if (updatedLink.link_target) {
						attrs.push(`target="${updatedLink.link_target}"`);
					}
					const attrStr = attrs.length ? ' ' + attrs.join(' ') : '';
					updatedLink.linked_sentence = updatedLink.original_sentence.replace(
						editingAnchorText,
						`<a href="${updatedLink.target_url}" class="sge-contextual-link" data-sge-source="ai"${attrStr} style="color:#6366f1; text-decoration:underline;">${editingAnchorText}</a>`,
						1
					);
					
					// Re-assign object to trigger deep reactivity
					links[index] = updatedLink;
					// Re-assign array to force re-render
					links = [...links];
				}
				editingLinkId = null;
				successMessage = 'Đã cập nhật các thuộc tính SEO / SGE của link.';
				nanobot.showToast(successMessage, 'success');
			}
		} catch (e) {
			errorMessage = e instanceof Error ? e.message : 'Không thể lưu thay đổi.';
			nanobot.showToast(errorMessage, 'error');
		} finally {
			isActioning = false;
		}
	}

	async function handleApplyAll() {
		errorMessage = null;
		successMessage = null;

		if (reviewMode === 'article') {
			if (!activeArticleId) return;
			if (!confirm('Bạn có chắc muốn chèn các liên kết đã duyệt (Approved) vào nội dung bài viết gốc?')) return;
			isActioning = true;
			try {
				const result = await apiClient.post<any>(`/seo/contextual-links/${activeArticleId}/apply`, {});
				if (Number(result.data?.applied_count) > 0) {
					successMessage = `Đã cập nhật bài viết thành công! Đã chèn ${result.data.applied_count} liên kết.`;
					nanobot.showToast(successMessage, 'success');
					await fetchContextualLinks();
				} else if (Number(result.data?.skipped_stale) > 0) {
					errorMessage = `Không thể apply. Bài viết đã bị sửa đổi nội dung. Cần chạy lại phân tích.`;
					nanobot.showToast(errorMessage, 'error');
				} else if (Number(result.data?.skipped_inject_fail) > 0) {
					errorMessage = `Không thể chèn ${result.data.skipped_inject_fail} link do cấu trúc HTML không tương thích. Hãy chạy Phân tích lại.`;
					nanobot.showToast(errorMessage, 'warning');
				} else {
					successMessage = 'Không có liên kết Approved nào được chèn.';
					nanobot.showToast(successMessage, 'info');
				}
			} catch (e) {
				errorMessage = e instanceof Error ? e.message : 'Không thể thực thi chèn liên kết.';
				nanobot.showToast(errorMessage, 'error');
			} finally {
				isActioning = false;
			}
		} else {
			// Pillar mode: apply all approved contextual links from all source cluster articles in a single bulk backend request
			const approvedLinks = links.filter((l) => l.status === 'approved');
			if (approvedLinks.length === 0) return;

			if (!confirm(`Bạn có chắc muốn chèn liên kết đã duyệt vào các bài viết Cluster gốc liên quan?`)) return;

			isActioning = true;
			try {
				const result = await apiClient.post<any>(`/seo/contextual-links/pillar/${activePillarId}/apply`, {});
				
				const applied = Number(result.data?.applied_count || 0);
				const skipped = Number(result.data?.skipped_stale || 0);
				const injectFail = Number(result.data?.skipped_inject_fail || 0);
				const processed = Number(result.data?.processed_articles || 0);

				if (applied > 0) {
					successMessage = `Đã chèn thành công ${applied} liên kết vào ${processed} bài viết Cluster.`;
					nanobot.showToast(successMessage, 'success');
					if (skipped > 0) {
						errorMessage = `Bỏ qua ${skipped} liên kết vì nội dung bài viết gốc đã bị thay đổi bên ngoài.`;
						nanobot.showToast(errorMessage, 'warning');
					}
					if (injectFail > 0) {
						nanobot.showToast(`${injectFail} link không khớp cấu trúc HTML, cần Phân tích lại.`, 'warning');
					}
					await fetchContextualLinks();
				} else if (skipped > 0) {
					errorMessage = `Không thể chèn liên kết. Toàn bộ ${skipped} liên kết đã bị hết hạn (do nội dung bài viết gốc đã thay đổi).`;
					nanobot.showToast(errorMessage, 'error');
				} else if (injectFail > 0) {
					errorMessage = `Không thể chèn ${injectFail} link do cấu trúc HTML không tương thích. Hãy chạy Phân tích lại.`;
					nanobot.showToast(errorMessage, 'warning');
				} else {
					successMessage = 'Không có liên kết nào được chèn.';
					nanobot.showToast(successMessage, 'info');
				}
			} catch (e) {
				errorMessage = e instanceof Error ? e.message : 'Không thể thực thi chèn liên kết hàng loạt.';
				nanobot.showToast(errorMessage, 'error');
			} finally {
				isActioning = false;
			}
		}
	}

	async function handleTriggerReanalysis() {
		if (reviewMode === 'article') {
			if (!activeArticleId) return;
			isActioning = true;
			errorMessage = null;
			successMessage = null;
			try {
				await apiClient.post<any>(`/seo/match`, { entity_type: 'article', entity_id: activeArticleId });
				successMessage = 'Hệ thống đã nhận lệnh và đang phân tích lại bài viết trong nền. Vui lòng làm mới sau 15-30 giây.';
				nanobot.showToast(successMessage, 'success');
			} catch (e) {
				errorMessage = e instanceof Error ? e.message : 'Không thể trigger phân tích lại.';
				nanobot.showToast(errorMessage, 'error');
			} finally {
				isActioning = false;
			}
		} else {
			// Pillar mode: trigger scan only for this pillar's cluster articles
			if (!activePillarId) return;
			isActioning = true;
			errorMessage = null;
			successMessage = null;
			try {
				const result = await apiClient.post<any>(`/seo/contextual-links/pillar/${activePillarId}/auto-link`, {});
				successMessage = result.message || 'Đã kích hoạt quét & tự động phân tích link ngữ cảnh cho các Cluster. Bạn sẽ nhận được thông báo chuông khi hoàn tất.';
				nanobot.showToast(successMessage, 'success');
			} catch (e) {
				errorMessage = e instanceof Error ? e.message : 'Không thể kích hoạt quét phân tích Pillar.';
				nanobot.showToast(errorMessage, 'error');
			} finally {
				isActioning = false;
			}
		}
	}
</script>

{#if isWidget}
	<!-- WIDGET MODE (inline rendering inside UniversalModal) -->
	<div class="widget-layout flex flex-col h-full w-full">
		<!-- Article selector bar -->
		<div class="selector-bar shrink-0">
			{#if reviewMode === 'article'}
				<div class="selector-container relative">
					<label class="selector-label">Chọn Bài viết:</label>
					
					<div class="custom-dropdown-wrapper">
						<button 
							type="button"
							class="custom-dropdown-trigger" 
							onclick={() => { showDropdown = !showDropdown; if (showDropdown && articlesList.length === 0) fetchArticles(false); }}
						>
							<span class="trigger-text" class:placeholder={!activeArticleId}>
								{selectedArticleTitle}
							</span>
							<span class="trigger-arrow" style="transform: {showDropdown ? 'rotate(180deg)' : 'rotate(0deg)'}">▼</span>
						</button>

						{#if showDropdown}
							<div class="dropdown-backdrop" onclick={() => showDropdown = false} role="none"></div>
							
							<div class="dropdown-panel">
								<div class="dropdown-search-container">
									<input 
										type="text" 
										class="dropdown-search-input" 
										placeholder="Gõ tên bài viết để tìm..." 
										value={searchQuery}
										oninput={handleSearchInput}
										autofocus
									/>
									{#if isFetchingArticles}
										<div class="search-spinner"></div>
									{/if}
								</div>

								<div 
									class="dropdown-list" 
									onscroll={(e) => {
										const el = e.currentTarget;
										if (el.scrollHeight - el.scrollTop - el.clientHeight < 20) {
											loadMoreArticles();
										}
									}}
								>
									{#if articlesList.length === 0 && !isFetchingArticles}
										<div class="dropdown-empty">Không tìm thấy bài viết</div>
									{:else}
										<button 
											type="button"
											class="dropdown-item" 
											class:selected={activeArticleId === ''} 
											onclick={() => { activeArticleId = ''; showDropdown = false; }}
										>
											-- Chọn bài viết cần duyệt link SGE --
										</button>
										
										{#each articlesList as art (art.id)}
											<button 
												type="button"
												class="dropdown-item" 
												class:selected={activeArticleId === art.id} 
												onclick={() => { activeArticleId = art.id; showDropdown = false; }}
											>
												<span class="item-title">{art.title}</span>
												<span class="item-status" class:live={art.status === 'PUBLISHED'}>
													{art.status === 'PUBLISHED' ? 'Live' : 'Nháp'}
												</span>
											</button>
										{/each}

										{#if isFetchingArticles && articleOffset > 0}
											<div class="dropdown-loading-more">Đang tải thêm...</div>
										{/if}
									{/if}
								</div>
							</div>
						{/if}
					</div>
				</div>
				
				{#if activeArticleId}
					<button class="reanalysis-btn" onclick={handleTriggerReanalysis} disabled={isActioning}>
						<RefreshCw class="w-3 h-3 {isActioning ? 'animate-spin' : ''}" />
						Phân tích lại bài viết
					</button>
				{/if}
			{:else}
				<div class="selector-container">
					<label class="selector-label">Duyệt Link Về Pillar Node:</label>
					<span class="text-sm font-semibold text-white ml-2">{articleTitle || 'Đang tải...'}</span>
				</div>
				<button class="reanalysis-btn" onclick={handleTriggerReanalysis} disabled={isActioning}>
					<RefreshCw class="w-3 h-3 {isActioning ? 'animate-spin' : ''}" />
					Quét lại tất cả Cluster
				</button>
			{/if}
		</div>

		<!-- Banners -->
		{#if isStale && reviewMode === 'article' && activeArticleId}
			<div class="alert-banner warning">
				<AlertTriangle class="w-4 h-4" />
				<div class="banner-text">
					<strong>Nội dung bài viết đã thay đổi!</strong> Các đề xuất liên kết này có thể đã lỗi thời. Khuyên dùng chạy lại Phân tích.
				</div>
			</div>
		{/if}

		{#if errorMessage}
			<div class="alert-banner error">
				<AlertTriangle class="w-4 h-4" />
				<div class="banner-text">{errorMessage}</div>
			</div>
		{/if}

		{#if successMessage}
			<div class="alert-banner success">
				<Check class="w-4 h-4" />
				<div class="banner-text">{successMessage}</div>
			</div>
		{/if}

		{#if (reviewMode === 'article' && activeArticleId) || (reviewMode === 'pillar' && activePillarId)}
			<!-- Stats and Filters -->
			<section class="stats-filter-bar">
				<div class="status-filters">
					<button class="filter-tab" class:active={statusFilter === 'all'} onclick={() => statusFilter = 'all'}>
						Tất cả ({links.length})
					</button>
					<button class="filter-tab pending" class:active={statusFilter === 'pending'} onclick={() => statusFilter = 'pending'}>
						Chờ duyệt ({stats.pending})
					</button>
					<button class="filter-tab approved" class:active={statusFilter === 'approved'} onclick={() => statusFilter = 'approved'}>
						Đã duyệt ({stats.approved})
					</button>
					<button class="filter-tab rejected" class:active={statusFilter === 'rejected'} onclick={() => statusFilter = 'rejected'}>
						Đã từ chối ({stats.rejected})
					</button>
					<button class="filter-tab applied" class:active={statusFilter === 'applied'} onclick={() => statusFilter = 'applied'}>
						Đã chèn ({stats.applied})
					</button>
				</div>

				<div class="action-buttons">
					<button class="btn refresh" onclick={fetchContextualLinks} disabled={isLoading} title="Tải lại danh sách">
						<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin' : ''}" />
						Làm mới
					</button>
					{#if stats.approved > 0}
						<button class="btn apply" onclick={handleApplyAll} disabled={isActioning}>
							<Link2 class="w-3.5 h-3.5" />
							Chèn liên kết ({stats.approved})
						</button>
					{/if}
				</div>
			</section>

			<!-- Scrollable content -->
			<div class="widget-body-scroll flex-1 overflow-y-auto p-4 bg-[#0a0a14]">
				{#if isLoading}
					<div class="loading-state">
						<div class="spinner"></div>
						<p>Đang tải các đề xuất liên kết SGE...</p>
					</div>
				{:else if filteredLinks.length === 0}
					<div class="empty-state">
						<HelpCircle class="w-12 h-12 text-stone-600" />
						<p>Không có đề xuất liên kết nào cho bộ lọc này.</p>
					</div>
				{:else}
					<div class="links-list">
						{#each filteredLinks as link (link.id)}
							<div class="link-card" class:pending={link.status === 'pending'} class:approved={link.status === 'approved'} class:rejected={link.status === 'rejected'} class:applied={link.status === 'applied'}>
								<!-- Card Header -->
								<div class="card-header">
									<div class="entity-info">
										<span class="entity-badge" class:pain={link.matched_entity_type === 'PAIN_POINT'} class:feature={link.matched_entity_type === 'FEATURE'} class:brand={link.matched_entity_type === 'BRAND'} class:ingredient={link.matched_entity_type === 'INGREDIENT'} class:symptom={link.matched_entity_type === 'SYMPTOM'}>
											{link.matched_entity_type}
										</span>
										<strong class="entity-name">{link.matched_entity_name}</strong>
										<span class="target-connector">⟶</span>
										<span class="target-node" title={link.target_url}>
											🎯 {link.target_label || 'Pillar'}
										</span>
										{#if reviewMode === 'pillar' && link.source_article_title}
											<span class="source-article-badge" title={link.source_article_title}>
												📝 Từ: {link.source_article_title}
											</span>
										{/if}
									</div>

									<div class="confidence-badge" style="border-color: rgba(99, 102, 241, {link.ai_confidence})">
										🤖 Độ tin cậy: {Math.round(link.ai_confidence * 100)}%
									</div>
								</div>

								<!-- Sentence Compare -->
								<div class="sentence-comparison">
									<div class="sentence-box original">
										<div class="box-label">Câu gốc:</div>
										<p class="sentence-text">{link.original_sentence}</p>
									</div>
									
									<div class="sentence-box proposed">
										<div class="box-label">Đề xuất chèn:</div>
										<p class="sentence-text linked-text">
											{@html link.linked_sentence}
										</p>
									</div>
								</div>

								<!-- Card Footer / Actions -->
								<div class="card-footer">
									{#if link.ai_reasoning}
										<div class="reasoning-text" title={link.ai_reasoning}>
											💡 <em>Lý do:</em> {link.ai_reasoning}
										</div>
									{/if}

									<div class="footer-actions">
										<!-- Rel metadata info -->
										{#if link.link_rel}
											<span class="rel-badge">rel="{link.link_rel}"</span>
										{/if}
										{#if link.link_title}
											<span class="rel-badge" title={link.link_title}>title="{link.link_title}"</span>
										{/if}
										{#if link.link_target}
											<span class="rel-badge">target="{link.link_target}"</span>
										{/if}

										{#if link.status !== 'applied'}
											<button class="action-btn edit" onclick={() => startEditing(link)} disabled={isActioning}>
												<Edit2 class="w-3 h-3" /> Sửa
											</button>
											
											<button class="action-btn approve" class:active={link.status === 'approved'} onclick={() => handleUpdateStatus(link.id, 'approved')} disabled={isActioning}>
												<Check class="w-3.5 h-3.5" /> Duyệt
											</button>
											
											<button class="action-btn reject" class:active={link.status === 'rejected'} onclick={() => handleUpdateStatus(link.id, 'rejected')} disabled={isActioning}>
												<X class="w-3.5 h-3.5" /> Từ chối
											</button>
										{:else}
											<span class="applied-status-badge">✓ Đã cập nhật vào bài viết</span>
										{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{:else}
			<!-- GLOBAL DASHBOARD VIEW: render khi chưa chọn bài viết -->
			<!-- Thống kê toàn sàn -->
			<section class="stats-filter-bar">
				<div class="status-filters">
					<button class="filter-tab" class:active={statusFilter === 'all'} onclick={() => statusFilter = 'all'}>
						Tất cả gợi ý ({links.length})
					</button>
					<button class="filter-tab pending" class:active={statusFilter === 'pending'} onclick={() => statusFilter = 'pending'}>
						Chờ duyệt ({stats.pending})
					</button>
					<button class="filter-tab approved" class:active={statusFilter === 'approved'} onclick={() => statusFilter = 'approved'}>
						Đã duyệt ({stats.approved})
					</button>
					<button class="filter-tab rejected" class:active={statusFilter === 'rejected'} onclick={() => statusFilter = 'rejected'}>
						Đã từ chối ({stats.rejected})
					</button>
					<button class="filter-tab applied" class:active={statusFilter === 'applied'} onclick={() => statusFilter = 'applied'}>
						Đã chèn ({stats.applied})
					</button>
				</div>

				<div class="action-buttons">
					<button class="btn refresh" onclick={fetchContextualLinks} disabled={isLoading}>
						<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin' : ''}" /> Tải lại
					</button>
					{#if stats.approved > 0}
						<button class="btn apply" onclick={handleApplyAll} disabled={isActioning}>
							🚀 Áp dụng {stats.approved} link đã duyệt
						</button>
					{/if}
				</div>
			</section>

			<!-- Danh sách gợi ý toàn sàn -->
			<div class="widget-body-scroll modal-body-scroll">
				{#if isLoading}
					<div class="loading-state">
						<div class="spinner"></div>
						<p>Đang tải danh sách liên kết SGE toàn hệ thống...</p>
					</div>
				{:else if filteredLinks.length === 0}
					<div class="empty-state">
						<HelpCircle class="w-12 h-12 text-gray-600 mb-2" />
						<p>Không có đề xuất liên kết nào phù hợp với bộ lọc.</p>
					</div>
				{:else}
					<div class="links-grid">
						{#each filteredLinks as link (link.id)}
							<div class="link-card" class:pending={link.status === 'pending'} class:approved={link.status === 'approved'} class:applied={link.status === 'applied'}>
								<!-- Header -->
								<div class="card-header">
									<div class="entity-info">
										<span class="entity-badge {link.matched_entity_type}">
											{link.matched_entity_type}
										</span>
										<strong class="entity-name">{link.matched_entity_name}</strong>
										<span class="target-connector">➔</span>
										<span class="target-node" title={link.target_url}>{link.target_label || 'Pillar'}</span>
										
										<!-- Hiển thị bài viết nguồn trên Dashboard toàn sàn -->
										<span class="source-article-badge" title="Bài viết nguồn">
											📄 {link.source_article_title || 'Nguồn'}
										</span>
									</div>

									<div class="confidence-badge">
										AI: {Math.round(link.ai_confidence * 100)}%
									</div>
								</div>

								<!-- Câu văn so sánh -->
								<div class="sentence-comparison">
									<div class="sentence-box original">
										<div class="box-label">Câu gốc:</div>
										<p class="sentence-text">{link.original_sentence}</p>
									</div>
									
									<div class="sentence-box proposed">
										<div class="box-label">Đề xuất chèn:</div>
										<p class="sentence-text linked-text">
											{@html link.linked_sentence}
										</p>
									</div>
								</div>

								<!-- Card Footer / Actions -->
								<div class="card-footer">
									{#if link.ai_reasoning}
										<div class="reasoning-text" title={link.ai_reasoning}>
											💡 <em>Lý do:</em> {link.ai_reasoning}
										</div>
									{/if}

									<div class="footer-actions">
											{#if link.link_rel}
												<span class="rel-badge">rel="{link.link_rel}"</span>
											{/if}
											{#if link.link_title}
												<span class="rel-badge" title={link.link_title}>title="{link.link_title}"</span>
											{/if}
											{#if link.link_target}
												<span class="rel-badge">target="{link.link_target}"</span>
											{/if}

											{#if link.status !== 'applied'}
												<button class="action-btn edit" onclick={() => startEditing(link)} disabled={isActioning}>
													<Edit2 class="w-3.5 h-3.5" /> Sửa
												</button>
												
												<button class="action-btn approve" class:active={link.status === 'approved'} onclick={() => handleUpdateStatus(link.id, 'approved')} disabled={isActioning}>
													<Check class="w-3.5 h-3.5" /> Duyệt
												</button>
												
												<button class="action-btn reject" class:active={link.status === 'rejected'} onclick={() => handleUpdateStatus(link.id, 'rejected')} disabled={isActioning}>
													<X class="w-3.5 h-3.5" /> Từ chối
												</button>
											{:else}
												<span class="applied-status-badge">✓ Đã cập nhật vào bài viết</span>
											{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>

					{#if hasMore}
						<div class="load-more-container">
							<button class="load-more-btn" onclick={handleLoadMore} disabled={isLoading}>
								{#if isLoading}
									<RefreshCw class="w-3.5 h-3.5 animate-spin" /> Đang tải thêm...
								{:else}
									Xem thêm đề xuất (Load More)
								{/if}
							</button>
						</div>
					{/if}
				{/if}
			</div>
		{/if}
	</div>
{:else}
	<!-- STANDALONE MODAL MODE (popup overlay) -->
	<div class="review-modal-backdrop" onclick={onClose} onkeydown={(e) => e.key === 'Escape' && onClose()} role="button" tabindex="0">
		<div class="review-modal-container" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="button" tabindex="0">
			<!-- Modal Header -->
			<header class="modal-header">
				<div class="header-details">
					<div class="modal-badge">SGE CONTEXTUAL LINK REVIEW</div>
					<h2 class="modal-title" title={articleTitle}>Duyệt liên kết: {articleTitle || 'Đang tải...'}</h2>
				</div>
				<button class="close-btn" onclick={onClose}>✕</button>
			</header>

			<!-- Info / Status Banner -->
			{#if isStale && reviewMode === 'article'}
				<div class="alert-banner warning">
					<AlertTriangle class="w-4 h-4" />
					<div class="banner-text">
						<strong>Nội dung bài viết đã thay đổi!</strong> Các đề xuất liên kết này có thể đã lỗi thời. Khuyên dùng: 
						<button class="banner-action-btn" onclick={handleTriggerReanalysis} disabled={isActioning}>Phân tích lại bài viết</button>
					</div>
				</div>
			{/if}

			{#if errorMessage}
				<div class="alert-banner error">
					<AlertTriangle class="w-4 h-4" />
					<div class="banner-text">{errorMessage}</div>
				</div>
			{/if}

			{#if successMessage}
				<div class="alert-banner success">
					<Check class="w-4 h-4" />
					<div class="banner-text">{successMessage}</div>
				</div>
			{/if}

			<!-- Stats and Filters -->
			<section class="stats-filter-bar">
				<div class="status-filters">
					<button class="filter-tab" class:active={statusFilter === 'all'} onclick={() => statusFilter = 'all'}>
						Tất cả ({links.length})
					</button>
					<button class="filter-tab pending" class:active={statusFilter === 'pending'} onclick={() => statusFilter = 'pending'}>
						Chờ duyệt ({stats.pending})
					</button>
					<button class="filter-tab approved" class:active={statusFilter === 'approved'} onclick={() => statusFilter = 'approved'}>
						Đã duyệt ({stats.approved})
					</button>
					<button class="filter-tab rejected" class:active={statusFilter === 'rejected'} onclick={() => statusFilter = 'rejected'}>
						Đã từ chối ({stats.rejected})
					</button>
					<button class="filter-tab applied" class:active={statusFilter === 'applied'} onclick={() => statusFilter = 'applied'}>
						Đã chèn ({stats.applied})
					</button>
				</div>

				<div class="action-buttons">
					<button class="btn refresh" onclick={fetchContextualLinks} disabled={isLoading} title="Tải lại danh sách">
						<RefreshCw class="w-3.5 h-3.5 {isLoading ? 'animate-spin' : ''}" />
						Làm mới
					</button>
					{#if reviewMode === 'pillar' && activePillarId}
						<button class="btn refresh" onclick={handleTriggerReanalysis} disabled={isActioning} title="Quét tìm đề xuất mới từ các Cluster trỏ về Pillar hiện tại">
							<RefreshCw class="w-3.5 h-3.5 {isActioning ? 'animate-spin' : ''}" />
							Quét lại Cluster
						</button>
					{:else if reviewMode === 'article' && activeArticleId}
						<button class="btn refresh" onclick={handleTriggerReanalysis} disabled={isActioning} title="Phân tích lại bài viết này">
							<RefreshCw class="w-3.5 h-3.5 {isActioning ? 'animate-spin' : ''}" />
							Phân tích lại
						</button>
					{/if}
					{#if stats.approved > 0}
						<button class="btn apply" onclick={handleApplyAll} disabled={isActioning}>
							<Link2 class="w-3.5 h-3.5" />
							Chèn liên kết ({stats.approved})
						</button>
					{/if}
				</div>
			</section>

			<!-- Content List -->
			<div class="modal-body-scroll">
				{#if isLoading}
					<div class="loading-state">
						<div class="spinner"></div>
						<p>Đang tải các đề xuất liên kết AI...</p>
					</div>
				{:else if filteredLinks.length === 0}
					<div class="empty-state">
						<HelpCircle class="w-12 h-12 text-gray-600" />
						<p>Không có đề xuất liên kết nào cho bộ lọc này.</p>
					</div>
				{:else}
					<div class="links-list">
						{#each filteredLinks as link (link.id)}
							<div class="link-card" class:pending={link.status === 'pending'} class:approved={link.status === 'approved'} class:rejected={link.status === 'rejected'} class:applied={link.status === 'applied'}>
								<!-- Card Header -->
								<div class="card-header">
									<div class="entity-info">
										<span class="entity-badge" class:pain={link.matched_entity_type === 'PAIN_POINT'} class:feature={link.matched_entity_type === 'FEATURE'} class:brand={link.matched_entity_type === 'BRAND'} class:ingredient={link.matched_entity_type === 'INGREDIENT'} class:symptom={link.matched_entity_type === 'SYMPTOM'}>
											{link.matched_entity_type}
										</span>
										<strong class="entity-name">{link.matched_entity_name}</strong>
										<span class="target-connector">⟶</span>
										<span class="target-node" title={link.target_url}>
											🎯 {link.target_label || 'Pillar'}
										</span>
										{#if reviewMode === 'pillar' && link.source_article_title}
											<span class="source-article-badge" title={link.source_article_title}>
												📝 Từ: {link.source_article_title}
											</span>
										{/if}
									</div>

									<div class="confidence-badge" style="border-color: rgba(99, 102, 241, {link.ai_confidence})">
										🤖 Độ tin cậy: {Math.round(link.ai_confidence * 100)}%
									</div>
								</div>

								<!-- Sentence Compare -->
								<div class="sentence-comparison">
									<div class="sentence-box original">
										<div class="box-label">Câu gốc:</div>
										<p class="sentence-text">{link.original_sentence}</p>
									</div>
									
									<div class="sentence-box proposed">
										<div class="box-label">Đề xuất chèn:</div>
										<p class="sentence-text linked-text">
											{@html link.linked_sentence}
										</p>
									</div>
								</div>

								<!-- Card Footer / Actions -->
								<div class="card-footer">
									{#if link.ai_reasoning}
										<div class="reasoning-text" title={link.ai_reasoning}>
											💡 <em>Lý do:</em> {link.ai_reasoning}
										</div>
									{/if}

										<!-- Rel metadata info -->
										{#if link.link_rel}
											<span class="rel-badge">rel="{link.link_rel}"</span>
										{/if}
										{#if link.link_title}
											<span class="rel-badge" title={link.link_title}>title="{link.link_title}"</span>
										{/if}
										{#if link.link_target}
											<span class="rel-badge">target="{link.link_target}"</span>
										{/if}

										{#if link.status !== 'applied'}
											<button class="action-btn edit" onclick={() => startEditing(link)} disabled={isActioning}>
												<Edit2 class="w-3 h-3" /> Sửa
											</button>
											
											<button class="action-btn approve" class:active={link.status === 'approved'} onclick={() => handleUpdateStatus(link.id, 'approved')} disabled={isActioning}>
												<Check class="w-3.5 h-3.5" /> Duyệt
											</button>
											
											<button class="action-btn reject" class:active={link.status === 'rejected'} onclick={() => handleUpdateStatus(link.id, 'rejected')} disabled={isActioning}>
												<X class="w-3.5 h-3.5" /> Từ chối
											</button>
										{:else}
											<span class="applied-status-badge">✓ Đã cập nhật vào bài viết</span>
										{/if}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<!-- Floating Modal Chỉnh Sửa Link SGE Nổi Lên Chuyên Nghiệp -->
{#if editingLinkId}
	<div class="edit-modal-overlay" style="z-index: {Z_INDEX_ADMIN.MODAL_CONFIRM}">
		<div class="edit-modal-backdrop" onclick={() => editingLinkId = null}></div>
		<div class="edit-modal-card">
			<div class="edit-modal-header">
				<h3 class="edit-modal-title">🛠️ CHỈNH SỬA THUỘC TÍNH SGE LINK</h3>
				<button class="close-modal-btn" onclick={() => editingLinkId = null}>✕</button>
			</div>
			
			<div class="edit-modal-body">
				<div class="form-row">
					<label class="form-label">Từ khóa mỏ neo (Anchor Text):</label>
					<input 
						type="text" 
						class="edit-text-input" 
						placeholder="Nhập Anchor text" 
						bind:value={editingAnchorText}
					/>
					<small class="form-help">Bắt buộc phải khớp với cụm từ trong câu gốc.</small>
				</div>
				
				<div class="form-row">
					<label class="form-label">Đường dẫn đích (Target URL):</label>
					<input 
						type="text" 
						class="edit-text-input" 
						placeholder="https://..." 
						bind:value={editingTargetUrl}
					/>
					<small class="form-help">URL đích chèn vào thẻ a (mặc định lấy theo Pillar).</small>
				</div>
				
				<div class="form-row">
					<label class="form-label">Thuộc tính SEO Rel:</label>
					<select class="edit-select-input" bind:value={editingRel}>
						<option value="">dofollow (Truyền sức mạnh link juice - Khuyên dùng)</option>
						<option value="nofollow">nofollow (Không truyền sức mạnh link)</option>
						<option value="sponsored">sponsored (Link tài trợ / Quảng cáo / Có trả phí)</option>
						<option value="ugc">ugc (Nội dung do người dùng tự tạo / Bình luận)</option>
					</select>
					<small class="form-help">Giúp Bot tìm kiếm hiểu rõ quan hệ giữa hai liên kết bài viết.</small>
				</div>

				<div class="form-row">
					<label class="form-label">Tiêu đề mô tả khi hover (Title Attribute):</label>
					<input 
						type="text" 
						class="edit-text-input" 
						placeholder="Nhập tiêu đề mô tả..." 
						bind:value={editingTitle}
					/>
					<small class="form-help">Hiển thị tooltip gợi ý cho người đọc và hỗ trợ bot SEO.</small>
				</div>

				<div class="form-row">
					<label class="form-label">Cách mở liên kết (Target Attribute):</label>
					<select class="edit-select-input" bind:value={editingTarget}>
						<option value="">Cùng Tab (Khuyên dùng để tối ưu Session duration)</option>
						<option value="_blank">Tab mới (target="_blank")</option>
					</select>
					<small class="form-help">Điều hướng người dùng khi click vào liên kết.</small>
				</div>
			</div>
			
			<div class="edit-modal-footer">
				<button class="action-btn cancel" onclick={() => editingLinkId = null}>Hủy</button>
				<button class="action-btn save" onclick={() => handleSaveEdit(editingLinkId)} disabled={isActioning}>
					✓ Lưu thay đổi
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Widget layout styling */
	.widget-layout {
		background: #06060c;
		height: 100%;
		font-family: inherit;
	}

	.selector-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1.25rem;
		background: #0f0f1d;
		border-bottom: 1px solid rgba(0, 243, 255, 0.1);
		gap: 1rem;
	}

	.selector-container {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.selector-label {
		font-family: monospace;
		font-size: 0.75rem;
		color: #00f3ff;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		white-space: nowrap;
	}

	.selector-select {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(0, 243, 255, 0.2);
		border-radius: 6px;
		color: #e2e8f0;
		font-size: 0.8rem;
		padding: 0.4rem 0.75rem;
		width: 380px;
		max-width: 100%;
		outline: none;
		transition: all 0.2s;
	}
	.selector-select:focus {
		border-color: #00f3ff;
		box-shadow: 0 0 8px rgba(0, 243, 255, 0.15);
	}

	/* Custom Dropdown Styling (UI/UX Pro-Max) */
	.custom-dropdown-wrapper {
		position: relative;
		width: 380px;
		max-width: 100%;
		z-index: 100;
	}

	.custom-dropdown-trigger {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(0, 243, 255, 0.2);
		border-radius: 6px;
		color: #e2e8f0;
		font-size: 0.8rem;
		padding: 0.45rem 0.85rem;
		width: 100%;
		display: flex;
		justify-content: space-between;
		align-items: center;
		cursor: pointer;
		text-align: left;
		transition: all 0.2s ease;
	}
	.custom-dropdown-trigger:hover {
		border-color: rgba(0, 243, 255, 0.5);
		background: rgba(0, 243, 255, 0.03);
	}
	.custom-dropdown-trigger:focus {
		border-color: #00f3ff;
		box-shadow: 0 0 8px rgba(0, 243, 255, 0.15);
	}
	.trigger-text {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		padding-right: 0.5rem;
	}
	.trigger-text.placeholder {
		color: #64748b;
	}
	.trigger-arrow {
		font-size: 0.65rem;
		color: #64748b;
		transition: transform 0.2s;
	}

	/* Backdrop */
	.dropdown-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 999;
	}

	/* Dropdown Panel */
	.dropdown-panel {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		margin-top: 4px;
		background: #0f0f1a;
		border: 1px solid rgba(0, 243, 255, 0.25);
		border-radius: 8px;
		box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.6);
		z-index: 1000;
		display: flex;
		flex-direction: column;
		max-height: 320px;
		overflow: hidden;
	}

	/* Search bar */
	.dropdown-search-container {
		position: relative;
		padding: 6px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		display: flex;
		align-items: center;
	}
	.dropdown-search-input {
		width: 100%;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		color: #fff;
		font-size: 0.8rem;
		padding: 0.4rem 0.6rem;
		outline: none;
		transition: border-color 0.2s;
	}
	.dropdown-search-input:focus {
		border-color: rgba(0, 243, 255, 0.5);
	}
	.search-spinner {
		position: absolute;
		right: 14px;
		width: 12px;
		height: 12px;
		border: 2px solid rgba(0, 243, 255, 0.2);
		border-top-color: #00f3ff;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	/* List items */
	.dropdown-list {
		overflow-y: auto;
		max-height: 260px;
		display: flex;
		flex-direction: column;
		padding: 4px 0;
	}
	.dropdown-item {
		width: 100%;
		background: transparent;
		border: none;
		padding: 0.55rem 0.85rem;
		color: #94a3b8;
		font-size: 0.78rem;
		text-align: left;
		cursor: pointer;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.75rem;
		transition: all 0.15s;
	}
	.dropdown-item:hover {
		background: rgba(0, 243, 255, 0.06);
		color: #fff;
	}
	.dropdown-item.selected {
		background: rgba(0, 243, 255, 0.12);
		color: #00f3ff;
		font-weight: 500;
	}
	.item-title {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		flex-grow: 1;
	}
	.item-status {
		font-size: 0.65rem;
		padding: 1px 4px;
		border-radius: 3px;
		background: rgba(255, 255, 255, 0.05);
		color: #64748b;
		white-space: nowrap;
	}
	.item-status.live {
		background: rgba(16, 185, 129, 0.1);
		color: #10b981;
	}

	.dropdown-empty {
		padding: 1rem;
		text-align: center;
		color: #64748b;
		font-size: 0.75rem;
	}
	.dropdown-loading-more {
		padding: 0.5rem;
		text-align: center;
		color: #64748b;
		font-size: 0.7rem;
	}

	.relative {
		position: relative;
	}

	.reanalysis-btn {
		background: rgba(0, 243, 255, 0.08);
		border: 1px solid rgba(0, 243, 255, 0.25);
		border-radius: 6px;
		color: #00f3ff;
		font-size: 0.72rem;
		font-weight: 600;
		padding: 0.4rem 0.85rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.35rem;
		transition: all 0.2s;
	}
	.reanalysis-btn:hover:not(:disabled) {
		background: rgba(0, 243, 255, 0.15);
		box-shadow: 0 0 10px rgba(0, 243, 255, 0.1);
	}

	.widget-body-scroll {
		background: #06060b;
	}

	/* Common modal structure */
	.review-modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.85);
		backdrop-filter: blur(8px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 99999;
		padding: 2rem;
		cursor: default;
	}

	.review-modal-container {
		width: 100%;
		max-width: 1100px;
		height: 90vh;
		background: #0f0f1a;
		border: 1px solid rgba(99, 102, 241, 0.25);
		border-radius: 12px;
		box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		outline: none;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.5rem;
		background: rgba(26, 26, 46, 0.6);
		border-bottom: 1px solid rgba(99, 102, 241, 0.15);
		flex-shrink: 0;
	}

	.modal-badge {
		font-family: monospace;
		font-size: 0.65rem;
		letter-spacing: 0.2em;
		color: #6366f1;
		margin-bottom: 0.2rem;
	}

	.modal-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #ffffff;
		margin: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		max-width: 800px;
	}

	.close-btn {
		background: transparent;
		border: none;
		color: #64748b;
		font-size: 1.2rem;
		cursor: pointer;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		transition: all 0.2s;
	}
	.close-btn:hover {
		color: #ffffff;
		background: rgba(255, 255, 255, 0.05);
	}

	.alert-banner {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1.5rem;
		font-size: 0.8rem;
		line-height: 1.5;
		flex-shrink: 0;
	}
	.alert-banner.warning {
		background: rgba(245, 158, 11, 0.12);
		border-bottom: 1px solid rgba(245, 158, 11, 0.2);
		color: #fbd578;
	}
	.alert-banner.error {
		background: rgba(239, 68, 68, 0.12);
		border-bottom: 1px solid rgba(239, 68, 68, 0.2);
		color: #fca5a5;
	}
	.alert-banner.success {
		background: rgba(16, 185, 129, 0.12);
		border-bottom: 1px solid rgba(16, 185, 129, 0.2);
		color: #6ee7b7;
	}

	.banner-text {
		flex: 1;
	}

	.banner-action-btn {
		background: #d97706;
		border: none;
		color: white;
		padding: 0.2rem 0.6rem;
		font-size: 0.72rem;
		font-weight: 600;
		border-radius: 4px;
		cursor: pointer;
		margin-left: 0.5rem;
		transition: background 0.15s;
	}
	.banner-action-btn:hover:not(:disabled) {
		background: #b45309;
	}

	.stats-filter-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1.5rem;
		background: rgba(255, 255, 255, 0.01);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		flex-wrap: wrap;
		gap: 0.75rem;
		flex-shrink: 0;
	}

	.status-filters {
		display: flex;
		gap: 0.25rem;
		background: rgba(0, 0, 0, 0.2);
		padding: 2px;
		border-radius: 6px;
		border: 1px solid rgba(255, 255, 255, 0.05);
	}

	.filter-tab {
		background: transparent;
		border: none;
		color: #64748b;
		padding: 0.35rem 0.75rem;
		font-size: 0.75rem;
		font-weight: 500;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s;
	}
	.filter-tab:hover {
		color: #e2e8f0;
	}
	.filter-tab.active {
		background: rgba(255, 255, 255, 0.05);
		color: #ffffff;
		font-weight: 600;
	}
	.filter-tab.pending.active {
		background: rgba(245, 158, 11, 0.15);
		color: #fbbf24;
	}
	.filter-tab.approved.active {
		background: rgba(16, 185, 129, 0.15);
		color: #34d399;
	}
	.filter-tab.rejected.active {
		background: rgba(239, 68, 68, 0.15);
		color: #fca5a5;
	}
	.filter-tab.applied.active {
		background: rgba(99, 102, 241, 0.15);
		color: #a5b4fc;
	}

	.action-buttons {
		display: flex;
		gap: 0.5rem;
	}

	.btn {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.4rem 0.8rem;
		font-size: 0.75rem;
		font-weight: 600;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s;
	}
	.btn.refresh {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(255, 255, 255, 0.1);
		color: #94a3b8;
	}
	.btn.refresh:hover {
		background: rgba(255, 255, 255, 0.08);
		color: #ffffff;
	}
	.btn.apply {
		background: rgba(16, 185, 129, 0.15);
		border: 1px solid rgba(16, 185, 129, 0.35);
		color: #34d399;
	}
	.btn.apply:hover {
		background: rgba(16, 185, 129, 0.25);
	}

	.modal-body-scroll {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem;
	}

	.loading-state, .empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 250px;
		gap: 1rem;
		color: #64748b;
		font-size: 0.85rem;
	}

	.spinner {
		width: 2rem;
		height: 2rem;
		border: 3px solid rgba(0, 243, 255, 0.1);
		border-top-color: #00f3ff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.links-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.link-card {
		background: rgba(255, 255, 255, 0.015);
		border: 1px solid rgba(255, 255, 255, 0.04);
		border-radius: 8px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.85rem;
		transition: all 0.2s;
	}
	.link-card:hover {
		background: rgba(255, 255, 255, 0.025);
		border-color: rgba(99, 102, 241, 0.12);
	}
	.link-card.approved {
		border-left: 4px solid #10b981;
	}
	.link-card.rejected {
		border-left: 4px solid #ef4444;
		opacity: 0.6;
	}
	.link-card.applied {
		border-left: 4px solid #6366f1;
		background: rgba(99, 102, 241, 0.01);
	}
	.link-card.pending {
		border-left: 4px solid #f59e0b;
	}

	.card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.entity-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.entity-badge {
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-family: monospace;
		font-size: 0.62rem;
		font-weight: 700;
	}
	.entity-badge.pain { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }
	.entity-badge.feature { background: rgba(99, 102, 241, 0.15); color: #a5b4fc; }
	.entity-badge.brand { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }
	.entity-badge.ingredient { background: rgba(245, 158, 11, 0.15); color: #fbd578; }
	.entity-badge.symptom { background: rgba(168, 85, 247, 0.15); color: #d8b4fe; }

	.entity-name {
		font-size: 0.8rem;
		color: #ffffff;
	}

	.target-connector {
		color: #475569;
		font-size: 0.8rem;
	}

	.target-node {
		font-size: 0.8rem;
		color: #fbbf24;
		background: rgba(245, 158, 11, 0.08);
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
	}
	
	.source-article-badge {
		font-size: 0.72rem;
		color: #a5b4fc;
		background: rgba(99, 102, 241, 0.12);
		padding: 0.15rem 0.45rem;
		border-radius: 4px;
		border: 1px solid rgba(99, 102, 241, 0.2);
		margin-left: 0.5rem;
		max-width: 280px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.confidence-badge {
		font-size: 0.7rem;
		color: #94a3b8;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.06);
		padding: 0.2rem 0.5rem;
		border-radius: 20px;
	}

	.sentence-comparison {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}
	@media (max-width: 768px) {
		.sentence-comparison {
			grid-template-columns: 1fr;
		}
	}

	.sentence-box {
		background: rgba(0, 0, 0, 0.15);
		border: 1px solid rgba(255, 255, 255, 0.03);
		border-radius: 6px;
		padding: 0.65rem;
	}

	.box-label {
		font-size: 0.65rem;
		color: #475569;
		margin-bottom: 0.3rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.sentence-text {
		font-size: 0.78rem;
		line-height: 1.6;
		margin: 0;
		color: #cbd5e1;
	}

	.linked-text {
		color: #ffffff;
	}

	.linked-text :global(a) {
		color: #38bdf8;
		text-decoration: underline;
		text-underline-offset: 2px;
		font-weight: 600;
	}

	.card-footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		border-top: 1px solid rgba(255, 255, 255, 0.03);
		padding-top: 0.6rem;
		margin-top: 0.2rem;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.reasoning-text {
		font-size: 0.72rem;
		color: #64748b;
		max-width: 60%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.footer-actions {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		margin-left: auto;
	}

	.action-btn {
		background: transparent;
		border: 1px solid rgba(255, 255, 255, 0.08);
		color: #94a3b8;
		padding: 0.25rem 0.5rem;
		font-size: 0.7rem;
		font-weight: 600;
		border-radius: 4px;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.25rem;
		transition: all 0.15s;
	}
	.action-btn:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.05);
		color: #ffffff;
	}
	
	.action-btn.approve {
		border-color: rgba(16, 185, 129, 0.15);
		color: #10b981;
	}
	.action-btn.approve:hover, .action-btn.approve.active {
		background: rgba(16, 185, 129, 0.1);
		border-color: #10b981;
	}

	.action-btn.reject {
		border-color: rgba(239, 68, 68, 0.15);
		color: #ef4444;
	}
	.action-btn.reject:hover, .action-btn.reject.active {
		background: rgba(239, 68, 68, 0.1);
		border-color: #ef4444;
	}

	.action-btn.edit {
		border-color: rgba(99, 102, 241, 0.15);
		color: #818cf8;
	}
	.action-btn.edit:hover {
		background: rgba(99, 102, 241, 0.1);
	}

	.rel-badge {
		font-family: monospace;
		font-size: 0.65rem;
		background: rgba(255, 255, 255, 0.04);
		color: #818cf8;
		padding: 0.15rem 0.35rem;
		border-radius: 3px;
		margin-right: 0.4rem;
	}

	.applied-status-badge {
		font-size: 0.72rem;
		color: #818cf8;
		font-weight: 600;
	}

	/* Edit form styling (UI/UX Pro-Max) */
	.edit-inputs-card {
		background: #0d0d18;
		border: 1px solid rgba(0, 243, 255, 0.2);
		border-radius: 8px;
		padding: 1rem;
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
		margin-top: 0.5rem;
	}

	.form-row {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		text-align: left;
	}

	.form-label {
		font-size: 0.72rem;
		font-weight: 600;
		color: #00f3ff;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.edit-text-input {
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(0, 243, 255, 0.25);
		border-radius: 4px;
		color: #ffffff;
		font-size: 0.8rem;
		padding: 0.45rem 0.65rem;
		width: 100%;
		outline: none;
		transition: all 0.2s;
	}
	.edit-text-input:focus {
		border-color: #00f3ff;
		box-shadow: 0 0 6px rgba(0, 243, 255, 0.15);
	}

	.edit-select-input {
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(0, 243, 255, 0.25);
		border-radius: 4px;
		color: #ffffff;
		font-size: 0.8rem;
		padding: 0.45rem 0.65rem;
		width: 100%;
		outline: none;
		cursor: pointer;
		transition: all 0.2s;
	}
	.edit-select-input:focus {
		border-color: #00f3ff;
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.5rem;
		margin-top: 0.2rem;
	}

	.action-btn.save {
		background: #10b981;
		color: white;
		border: none;
	}
	.action-btn.save:hover {
		background: #059669;
	}
	
	.action-btn.cancel {
		background: rgba(255, 255, 255, 0.05);
		border: none;
	}

	.load-more-container {
		display: flex;
		justify-content: center;
		padding: 1.5rem 0;
		border-top: 1px solid rgba(255, 255, 255, 0.03);
		margin-top: 1rem;
	}

	.load-more-btn {
		background: rgba(99, 102, 241, 0.08);
		border: 1px solid rgba(99, 102, 241, 0.25);
		border-radius: 6px;
		color: #a5b4fc;
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.5rem 1.5rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		transition: all 0.2s;
	}

	.load-more-btn:hover:not(:disabled) {
		background: rgba(99, 102, 241, 0.18);
		color: #ffffff;
		border-color: #6366f1;
		box-shadow: 0 0 10px rgba(99, 102, 241, 0.15);
	}
	
	.load-more-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Floating Modal Chỉnh Sửa Link SGE Nổi Lên Chuyên Nghiệp */
	.edit-modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;
	}

	.edit-modal-backdrop {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.7);
		backdrop-filter: blur(4px);
	}

	.edit-modal-card {
		position: relative;
		background: #0c0d16;
		border: 1px solid rgba(0, 243, 255, 0.35);
		border-radius: 12px;
		width: 100%;
		max-width: 580px;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		animation: modalFadeIn 0.25s ease-out;
		z-index: 1001;
	}

	.edit-modal-header {
		padding: 1.25rem 1.5rem;
		border-bottom: 1px solid rgba(0, 243, 255, 0.15);
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: rgba(0, 243, 255, 0.02);
	}

	.edit-modal-title {
		font-family: monospace;
		font-size: 0.9rem;
		font-weight: 700;
		color: #00f3ff;
		margin: 0;
		letter-spacing: 0.05em;
	}

	.close-modal-btn {
		background: none;
		border: none;
		color: #94a3b8;
		font-size: 1.2rem;
		cursor: pointer;
		transition: color 0.2s;
	}
	.close-modal-btn:hover {
		color: #ffffff;
	}

	.edit-modal-body {
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
		max-height: 65vh;
		overflow-y: auto;
	}

	/* Scrollbar custom for body */
	.edit-modal-body::-webkit-scrollbar {
		width: 6px;
	}
	.edit-modal-body::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.2);
	}
	.edit-modal-body::-webkit-scrollbar-thumb {
		background: rgba(0, 243, 255, 0.2);
		border-radius: 3px;
	}

	.form-help {
		font-size: 0.7rem;
		color: #64748b;
		margin-top: 0.2rem;
	}

	.edit-modal-footer {
		padding: 1rem 1.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
		background: rgba(0, 243, 255, 0.01);
		display: flex;
		justify-content: flex-end;
		gap: 0.75rem;
	}

	@keyframes modalFadeIn {
		from {
			opacity: 0;
			transform: scale(0.96);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}
</style>