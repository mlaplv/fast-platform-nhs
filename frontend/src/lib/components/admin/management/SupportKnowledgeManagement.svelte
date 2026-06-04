<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, fly, scale } from 'svelte/transition';
    import { supportKbAdmin as kb } from '$lib/state/admin/supportKnowledge.svelte';
    import { useNanobot } from '$lib/state/nanobot.svelte';
  const nanobot = useNanobot();
    import XohiLogo from '$lib/components/admin/XohiLogo.svelte';
    import Search from "@lucide/svelte/icons/search";
    import Plus from "@lucide/svelte/icons/plus";
    import Trash2 from "@lucide/svelte/icons/trash-2";
    import Edit3 from "@lucide/svelte/icons/edit-3";
    import Star from "@lucide/svelte/icons/star";
    import CheckSquare from "@lucide/svelte/icons/check-square";
    import Square from "@lucide/svelte/icons/square";
    import HelpCircle from "@lucide/svelte/icons/help-circle";
    import LayoutGrid from "@lucide/svelte/icons/layout-grid";
    import List from "@lucide/svelte/icons/list";
    import Network from "@lucide/svelte/icons/network";
    import RefreshCw from "@lucide/svelte/icons/refresh-cw";
    import SupportKnowledgeBulkActions from './SupportKnowledgeBulkActions.svelte';
    import SupportKnowledgeDrawer from './SupportKnowledgeDrawer.svelte';
    import KnowledgeGraphVisualizer from './KnowledgeGraphVisualizer.svelte';

    const categories = ["all", "GENERAL", "POLICY", "SHIPPING", "PRODUCT", "PROMO", "AUTO_LEARNED"];
    let search = $state("");
    let category = $state("all");

    // Sandbox & Inline Edit states (Elite V3.5 thưa sếp)
    let loadingSandbox = $state(false);
    let sandboxItems = $state<any[]>([]);
    let editingItem = $state<any>(null);
    const editCategories = ["GENERAL", "POLICY", "SHIPPING", "PRODUCT", "PROMO", "INFO_INGREDIENTS", "INFO_ADDRESS", "INFO_HOTLINE", "PRICE_QUERY", "INFO_SHIPPING"];

    onMount(async () => {
        await kb.fetchItems();
    });

    async function handleSearch() {
        if (category === "AUTO_LEARNED") {
            loadingSandbox = true;
            try {
                const res = await fetch('/api/v1/admin/support/knowledge/sandbox');
                if (res.ok) {
                    const data = await res.json();
                    sandboxItems = data.data || [];
                }
            } catch (e) {
                console.error("Failed to fetch sandbox:", e);
            } finally {
                loadingSandbox = false;
            }
        } else {
            await kb.fetchItems(category === "all" ? undefined : category, search);
        }
    }

    async function saveInlineEdit() {
        if (!editingItem) return;
        try {
            const res = await fetch(`/api/v1/admin/support/knowledge/${editingItem.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: editingItem.question,
                    answer: editingItem.answer,
                    category: editingItem.category
                })
            });
            if (res.ok) {
                nanobot.showToast("Đã lưu chỉnh sửa tri thức sandbox!", "success");
                editingItem = null;
                await handleSearch();
            } else {
                nanobot.showToast("Lưu chỉnh sửa thất bại.", "error");
            }
        } catch (e) {
            nanobot.showToast("Lỗi hệ thống khi chỉnh sửa.", "error");
        }
    }

    function formatDate(dateStr: string) {
        return new Date(dateStr).toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: 'short', day: 'numeric'
        });
    }

    let isAllSelected = $derived(kb.items.length > 0 && kb.items.every(item => kb.selectedIds.includes(item.id)));

    // Generate graph from Q&A data
    let graphData = $derived.by(() => {
        const nodes: any[] = [];
        const edges: any[] = [];
        const categoryMap = new Map();

        // Core Node
        nodes.push({ id: 'core', label: 'HELEN BRAIN', color: '#00f0ff', size: 30 });

        kb.items.forEach((item) => {
            // Category Nodes
            if (!categoryMap.has(item.category)) {
                categoryMap.set(item.category, `cat_${item.category}`);
                nodes.push({ id: `cat_${item.category}`, label: item.category, color: '#06b6d4', size: 25 });
                edges.push({ from: 'core', to: `cat_${item.category}` });
            }

            // Question Node
            const qId = `q_${item.id}`;
            nodes.push({ 
                id: qId, 
                label: item.question.length > 25 ? item.question.substring(0, 25) + '...' : item.question,
                title: item.question, // tooltip on hover
                color: item.is_active ? '#34d399' : '#f87171',
                size: 15
            });
            edges.push({ from: `cat_${item.category}`, to: qId });
            
            // Connect to tags or answer
            if (item.tags && item.tags.length > 0) {
                item.tags.forEach((tag: string) => {
                    const tagId = `tag_${tag}`;
                    if (!nodes.find(n => n.id === tagId)) {
                        nodes.push({ id: tagId, label: `#${tag}`, color: '#a78bfa', size: 10 });
                    }
                    edges.push({ from: qId, to: tagId });
                });
            } else {
                const ansId = `ans_${item.id}`;
                nodes.push({ id: ansId, label: "Answer", title: item.answer, color: '#60a5fa', size: 10 });
                edges.push({ from: qId, to: ansId, dashes: true });
            }
        });

        return { nodes, edges };
    });
</script>

<div class="w-full h-full flex flex-col bg-[#020202] text-white font-sans relative overflow-hidden">
    <!-- Header: Strategic Control -->
    <div class="px-8 py-6 border-b border-cyan-500/10 bg-black/40 backdrop-blur-md flex justify-between items-center z-10">
        <div class="flex items-center gap-4">
            <div class="p-3 bg-cyan-500/5 rounded-2xl border border-cyan-500/20">
                <HelpCircle size={24} class="text-cyan-400" />
            </div>
            <div>
                <h1 class="text-xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-200 to-white/40">Helen Brain</h1>
                <p class="text-[10px] text-cyan-500/60 font-mono font-bold tracking-widest ">Neural Knowledge Base v2.2</p>
            </div>
        </div>

        <div class="flex items-center gap-3">
            <button 
                onclick={() => kb.reindexBrain(nanobot)}
                disabled={kb.loading}
                class="bg-white/5 text-cyan-400 border border-cyan-500/20 px-6 py-3 rounded-xl font-black text-xs tracking-tight hover:bg-cyan-500/10 hover:border-cyan-500/50 active:scale-95 transition-all flex items-center gap-2 group {kb.loading ? 'opacity-50 cursor-wait' : ''}"
            >
                <RefreshCw size={16} class="group-hover:rotate-180 transition-transform duration-700 {kb.loading ? 'animate-spin' : ''}" /> BRAIN_REBUILD
            </button>

            <button 
                onclick={() => kb.openEdit()}
                class="bg-cyan-500 text-black px-6 py-3 rounded-xl font-black text-xs tracking-tight hover:bg-cyan-400 hover:scale-105 active:scale-95 transition-all shadow-[0_5px_20px_rgba(6,182,212,0.3)] flex items-center gap-2"
            >
                <Plus size={16} strokeWidth={4} /> TRAINING_SOURCE
            </button>
        </div>
    </div>

    <!-- Filters: Intelligence Routing -->
    <div class="px-8 py-4 border-b border-cyan-500/10 bg-black/20 flex gap-4 items-center z-10">
        <div class="relative flex-1 group">
            <input 
                type="text" 
                bind:value={search}
                oninput={handleSearch}
                placeholder="PROMPT_QUERY: Search neural pathways..."
                class="w-full bg-white/5 border border-white/10 rounded-xl px-12 py-3 outline-none focus:border-cyan-500/50 focus:bg-cyan-500/5 transition-all text-sm font-mono tracking-tight"
            />
            <div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-cyan-400 transition-colors">
                <Search size={16} />
            </div>
        </div>
        
        <select 
            bind:value={category} 
            onchange={handleSearch}
            class="bg-white/5 border border-white/10 rounded-xl px-5 py-3 outline-none focus:border-cyan-500/50 appearance-none text-[10px] font-mono font-black tracking-widest cursor-pointer pr-10 transition-all text-cyan-400"
        >
            {#each categories as cat}
                <option value={cat}>{cat}</option>
            {/each}
        </select>

        <button 
            onclick={kb.toggleSelectAll}
            class="p-3 rounded-xl border border-white/10 hover:bg-white/5 transition-all {isAllSelected ? 'text-cyan-400 border-cyan-400/50 bg-cyan-400/5' : 'text-gray-500'}"
            title="Chọn tất cả"
        >
            {#if isAllSelected}
                <CheckSquare size={18} />
            {:else}
                <Square size={18} />
            {/if}
        </button>
        
        <div class="h-8 w-px bg-white/10 mx-1"></div>

        <div class="flex bg-white/5 border border-white/10 rounded-xl p-1">
            <button 
                onclick={() => kb.viewMode = 'grid'}
                class="p-2 rounded-lg transition-all {kb.viewMode === 'grid' ? 'bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]' : 'text-gray-500 hover:text-gray-300'}"
                title="Dạng ô"
            >
                <LayoutGrid size={16} />
            </button>
            <button 
                onclick={() => kb.viewMode = 'list'}
                class="p-2 rounded-lg transition-all {kb.viewMode === 'list' ? 'bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]' : 'text-gray-500 hover:text-gray-300'}"
                title="Dạng danh sách"
            >
                <List size={16} />
            </button>
            <button 
                onclick={() => kb.viewMode = 'graph'}
                class="p-2 rounded-lg transition-all {kb.viewMode === 'graph' ? 'bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]' : 'text-gray-500 hover:text-gray-300'}"
                title="Bản đồ tri thức (Graph)"
            >
                <Network size={16} />
            </button>
        </div>
    </div>

    <!-- Main Content: Data Modules -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-8">
        {#if category === "AUTO_LEARNED"}
            {#if loadingSandbox}
                <div class="h-full flex flex-col items-center justify-center opacity-50">
                    <XohiLogo variant="simple" size={60} />
                    <p class="mt-4 text-[10px] font-black tracking-[0.3em] animate-pulse">Syncing Learning Sandbox...</p>
                </div>
            {:else if sandboxItems.length === 0}
                <div class="h-full flex flex-col items-center justify-center text-cyan-500/20">
                    <div class="p-8 rounded-full bg-cyan-500/[0.02] border border-cyan-500/10 mb-6">
                        <HelpCircle size={64} strokeWidth={1} />
                    </div>
                    <p class="text-sm font-mono font-bold tracking-tight text-cyan-500/40 ">Neural_Void: No sandboxed suggestions detected</p>
                </div>
            {:else}
                <div class="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                    {#each sandboxItems as item (item.id)}
                        <div class="kb-card group relative bg-[#0a0a0a] border border-indigo-500/20 rounded-3xl p-6 hover:bg-indigo-500/[0.03] hover:border-indigo-500/40 transition-all duration-300">
                            <div class="flex justify-between items-start mb-4">
                                <span class="px-2 py-0.5 rounded-full bg-indigo-500/10 text-[8px] font-mono font-black tracking-widest text-indigo-400 border border-indigo-500/20">
                                    {item.category}
                                </span>
                                <span class="text-[8px] font-mono text-gray-500">AUTO_LEARNED</span>
                            </div>

                            <h3 class="text-sm font-bold text-gray-200 mb-3 leading-snug line-clamp-2">
                                {item.question}
                            </h3>
                            
                            <p class="text-gray-500 text-[11px] leading-relaxed mb-6 line-clamp-3 italic">
                                "{item.answer}"
                            </p>

                            <div class="flex justify-between items-center mt-auto pt-4 border-t border-white/5">
                                <div class="flex gap-2">
                                    <button 
                                        onclick={() => editingItem = { ...item }}
                                        class="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-[9px] font-black text-gray-400 hover:text-white"
                                    >
                                        EDIT
                                    </button>
                                    <button 
                                        onclick={async () => {
                                            try {
                                                const res = await fetch(`/api/v1/admin/support/knowledge/sandbox/${item.id}/reject`, { method: 'POST' });
                                                if (res.ok) {
                                                    nanobot.showToast("Đã từ chối gợi ý tự học.", "success");
                                                    await handleSearch();
                                                }
                                            } catch (e) {
                                                nanobot.showToast("Từ chối thất bại.", "error");
                                            }
                                        }}
                                        class="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-[9px] font-black text-red-500 hover:bg-red-500/20"
                                    >
                                        DECLINE
                                    </button>
                                    <button 
                                        onclick={async () => {
                                            try {
                                                const res = await fetch(`/api/v1/admin/support/knowledge/sandbox/${item.id}/approve`, { method: 'POST' });
                                                if (res.ok) {
                                                    nanobot.showToast("Đã duyệt tri thức và sinh vector thành công!", "success");
                                                    await handleSearch();
                                                }
                                            } catch (e) {
                                                nanobot.showToast("Duyệt thất bại.", "error");
                                            }
                                        }}
                                        class="px-4 py-1.5 rounded-lg bg-cyan-500 text-black text-[9px] font-black hover:scale-105 active:scale-95 transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                                    >
                                        APPROVE
                                    </button>
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        {:else}
            {#if kb.loading && kb.items.length === 0}
                <div class="h-full flex flex-col items-center justify-center opacity-50">
                    <XohiLogo variant="simple" size={60} />
                    <p class="mt-4 text-[10px] font-black tracking-[0.3em] animate-pulse">Syncing Helen Brain...</p>
                </div>
            {:else if kb.items.length === 0}
                <div class="h-full flex flex-col items-center justify-center text-cyan-500/20">
                    <div class="p-8 rounded-full bg-cyan-500/[0.02] border border-cyan-500/10 mb-6 group-hover:scale-110 transition-transform">
                        <HelpCircle size={64} strokeWidth={1} />
                    </div>
                    <p class="text-sm font-mono font-bold tracking-tight text-cyan-500/40 ">Neural_Void: No knowledge sequences detected</p>
                </div>
            {:else}
                {#if kb.viewMode === 'grid'}
                <div class="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                    {#each kb.items as item (item.id)}
                        <div 
                            class="kb-card group relative bg-[#0a0a0a] border border-cyan-500/10 rounded-3xl p-6 hover:bg-cyan-500/[0.03] hover:border-cyan-500/40 transition-all duration-300 {kb.selectedIds.includes(item.id) ? 'active-selection' : ''}"
                            in:fly={{ y: 20, duration: 400 }}
                        >
                            <div class="flex justify-between items-start mb-4">
                                <div class="flex items-center gap-2">
                                    <button 
                                        onclick={() => kb.toggleSelect(item.id)}
                                        class="p-1 rounded-md transition-colors {kb.selectedIds.includes(item.id) ? 'text-cyan-400' : 'text-gray-600 hover:text-gray-400'}"
                                    >
                                        {#if kb.selectedIds.includes(item.id)}
                                            <CheckSquare size={16} class="fill-cyan-400/20" />
                                        {:else}
                                            <Square size={16} />
                                        {/if}
                                    </button>
                                    <span class="px-2 py-0.5 rounded-full bg-cyan-500/10 text-[8px] font-mono font-black tracking-widest text-cyan-400/60 group-hover:text-cyan-400 transition-colors border border-cyan-500/20">
                                        {item.category}
                                    </span>
                                    {#if item.priority > 0}
                                        <Star size={12} class="text-cyan-400 fill-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
                                    {/if}
                                </div>

                                <!-- Neural Toggle -->
                                <button 
                                    onclick={() => kb.toggleActive(item.id, !item.is_active)}
                                    class="relative w-8 h-4 rounded-full transition-colors cursor-pointer {item.is_active ? 'bg-cyan-500/20 border border-cyan-500/30' : 'bg-red-500/10 border border-red-500/20'}"
                                >
                                    <div class="absolute top-0.5 left-0.5 w-2.5 h-2.5 rounded-full transition-all {item.is_active ? 'translate-x-4 bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,1)]' : 'bg-red-500/50'}"></div>
                                </button>
                            </div>

                            <h3 class="text-sm font-bold text-gray-200 mb-3 leading-snug group-hover:text-white transition-colors line-clamp-2">
                                {item.question}
                            </h3>
                            
                            <p class="text-gray-500 text-[11px] leading-relaxed mb-6 line-clamp-3 group-hover:text-gray-400 transition-colors italic">
                                "{item.answer}"
                            </p>

                            <div class="flex justify-between items-center mt-auto pt-4 border-t border-white/5">
                                <div class="flex gap-1">
                                    <button onclick={() => kb.openEdit(item)} class="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-500 hover:text-white">
                                        <Edit3 size={14} />
                                    </button>
                                    <button onclick={() => kb.deleteItem(item.id)} class="p-1.5 hover:bg-red-500/20 rounded-lg transition-colors text-gray-500 hover:text-red-500">
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                                <span class="text-[8px] font-mono text-gray-700 tracking-tighter">{formatDate(item.created_at)}</span>
                            </div>
                        </div>
                    {/each}
                </div>
            {:else if kb.viewMode === 'list'}
                <!-- List View: Neural Table -->
                <div class="w-full bg-[#0a0a0a] border border-cyan-500/10 rounded-3xl overflow-hidden" in:fade>
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-cyan-500/5 border-b border-cyan-500/10">
                                <th class="p-5 w-12">
                                    <button onclick={kb.toggleSelectAll} class="text-gray-500 hover:text-cyan-400 transition-colors">
                                        {#if isAllSelected}
                                            <CheckSquare size={16} class="text-cyan-400" />
                                        {:else}
                                            <Square size={16} />
                                        {/if}
                                    </button>
                                </th>
                                <th class="p-5 text-[10px] font-mono font-black text-cyan-500/40 tracking-[0.2em]">Category</th>
                                <th class="p-5 text-[10px] font-mono font-black text-cyan-500/40 tracking-[0.2em]">Neural_Pathway (Question)</th>
                                <th class="p-5 text-[10px] font-mono font-black text-cyan-500/40 tracking-[0.2em]">Status</th>
                                <th class="p-5 text-right text-[10px] font-mono font-black text-cyan-500/40 tracking-[0.2em]">Operations</th>
                            </tr>
                        </thead>
                        <tbody>
                            {#each kb.items as item (item.id)}
                                <tr class="border-b border-white/5 hover:bg-cyan-500/[0.02] transition-colors {kb.selectedIds.includes(item.id) ? 'bg-cyan-500/[0.04]' : ''}">
                                    <td class="p-5">
                                        <button onclick={() => kb.toggleSelect(item.id)} class="text-gray-600 hover:text-cyan-400 {kb.selectedIds.includes(item.id) ? 'text-cyan-400' : ''}">
                                            {#if kb.selectedIds.includes(item.id)}
                                                <CheckSquare size={16} />
                                            {:else}
                                                <Square size={16} />
                                            {/if}
                                        </button>
                                    </td>
                                    <td class="p-5">
                                        <span class="px-2 py-1 rounded bg-cyan-500/10 text-[9px] font-black tracking-widest text-cyan-400 border border-cyan-500/20">
                                            {item.category}
                                        </span>
                                    </td>
                                    <td class="p-5">
                                        <div class="flex flex-col gap-1">
                                            <span class="text-xs font-bold text-gray-200 line-clamp-1">{item.question}</span>
                                            <span class="text-[10px] text-gray-500 italic line-clamp-1">"{item.answer}"</span>
                                        </div>
                                    </td>
                                    <td class="p-5">
                                        <button 
                                            onclick={() => kb.toggleActive(item.id, !item.is_active)}
                                            class="flex items-center gap-2 group/status"
                                        >
                                            <div class="w-2 h-2 rounded-full {item.is_active ? 'bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,1)]' : 'bg-red-500/50'}"></div>
                                            <span class="text-[9px] font-black tracking-widest {item.is_active ? 'text-cyan-500/60' : 'text-red-500/40'}">{item.is_active ? 'Active' : 'Offline'}</span>
                                        </button>
                                    </td>
                                    <td class="p-5 text-right">
                                        <div class="flex justify-end gap-2">
                                            <button onclick={() => kb.openEdit(item)} class="p-2 hover:bg-white/10 rounded-lg transition-colors text-gray-500 hover:text-white">
                                                <Edit3 size={14} />
                                            </button>
                                            <button onclick={() => kb.deleteItem(item.id)} class="p-2 hover:bg-red-500/20 rounded-lg transition-colors text-gray-500 hover:text-red-500">
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            {:else if kb.viewMode === 'graph'}
                <!-- Graph View: Visual Node Topology -->
                <div class="w-full h-full min-h-[600px]" in:fade>
                    <KnowledgeGraphVisualizer data={graphData} height="100%" />
                </div>
            {/if}
        {/if}
    {/if}
    </div>

    <!-- Bulk Actions Component -->
    <SupportKnowledgeBulkActions />

    <!-- Neural Drawer (Right Aligned Sync) -->
    <SupportKnowledgeDrawer 
        bind:isOpen={kb.showModal} 
        onClose={() => kb.showModal = false} 
    />

    <!-- Inline Edit Modal (Elite V3.5 thừa sếp!) -->
    {#if editingItem}
        <div class="absolute inset-0 z-[100] bg-black/90 backdrop-blur-3xl flex items-center justify-center p-8" in:fade>
            <div class="max-w-2xl w-full bg-gray-900/40 border border-indigo-500/30 rounded-[3rem] overflow-hidden flex flex-col h-[65vh] shadow-[0_0_50px_rgba(99,102,241,0.2)]" in:scale={{ start: 0.95 }}>
                <header class="p-8 border-b border-white/5 flex justify-between items-start">
                    <div>
                        <h2 class="text-2xl font-black italic tracking-tighter text-white">EDIT SANDBOX tri thức</h2>
                        <p class="text-[10px] font-mono text-indigo-400 tracking-[0.3em] mt-1">Chỉnh sửa Q&A trước khi duyệt chính thức</p>
                    </div>
                    <button 
                        onclick={() => editingItem = null}
                        class="p-4 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-all active:scale-90"
                    >
                        <RefreshCw size={20} class="rotate-45" />
                    </button>
                </header>

                <div class="flex-1 p-8 flex flex-col space-y-6 overflow-y-auto custom-scrollbar">
                    <div class="flex flex-col gap-2">
                        <label class="text-[9px] font-mono text-indigo-400 tracking-widest font-black">CATEGORY</label>
                        <select 
                            bind:value={editingItem.category}
                            class="bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 text-xs text-white"
                        >
                            {#each editCategories as cat}
                                <option value={cat}>{cat}</option>
                            {/each}
                        </select>
                    </div>
                    <div class="flex flex-col gap-2">
                        <label class="text-[9px] font-mono text-indigo-400 tracking-widest font-black">QUESTION</label>
                        <textarea
                            bind:value={editingItem.question}
                            class="bg-white/5 border border-white/10 rounded-xl p-4 outline-none focus:border-indigo-500 text-xs text-white resize-none h-20"
                        ></textarea>
                    </div>
                    <div class="flex flex-col gap-2">
                        <label class="text-[9px] font-mono text-indigo-400 tracking-widest font-black">ANSWER</label>
                        <textarea
                            bind:value={editingItem.answer}
                            class="bg-white/5 border border-white/10 rounded-xl p-4 outline-none focus:border-indigo-500 text-xs text-white resize-none h-32"
                        ></textarea>
                    </div>
                </div>

                <footer class="p-8 border-t border-white/5 flex justify-end gap-4 bg-black/20">
                    <button 
                        onclick={() => editingItem = null}
                        class="px-8 py-4 rounded-full bg-white/5 border border-white/10 text-xs font-black tracking-widest text-gray-400 hover:text-white transition-all active:scale-95"
                    >
                        CANCEL
                    </button>
                    <button 
                        onclick={saveInlineEdit}
                        class="px-10 py-4 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-black tracking-widest hover:scale-105 active:scale-95 transition-all shadow-[0_0_20px_rgba(99,102,241,0.4)]"
                    >
                        SAVE_CHANGES
                    </button>
                </footer>
            </div>
        </div>
    {/if}
</div>

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
        height: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.1);
    }

    .kb-card {
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    }
    .kb-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5);
    }

    .active-selection {
        background: rgba(6, 182, 212, 0.05) !important;
        border-color: rgba(6, 182, 212, 0.4) !important;
        box-shadow: 0 0 40px rgba(6, 182, 212, 0.1) inset, 0 0 20px rgba(6, 182, 212, 0.05);
    }

    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
</style>
