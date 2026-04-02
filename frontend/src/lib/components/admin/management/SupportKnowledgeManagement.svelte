<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, fly, scale } from 'svelte/transition';
    import { supportKbAdmin as kb } from '$lib/state/admin/supportKnowledge.svelte';
    import { nanobot } from '$lib/state/nanobot.svelte';
    import XohiLogo from '$lib/components/admin/XohiLogo.svelte';
    import Search from "lucide-svelte/icons/search";
    import Plus from "lucide-svelte/icons/plus";
    import Trash2 from "lucide-svelte/icons/trash-2";
    import Edit3 from "lucide-svelte/icons/edit-3";
    import Star from "lucide-svelte/icons/star";
    import CheckSquare from "lucide-svelte/icons/check-square";
    import Square from "lucide-svelte/icons/square";
    import HelpCircle from "lucide-svelte/icons/help-circle";
    import SupportKnowledgeBulkActions from './SupportKnowledgeBulkActions.svelte';

    const categories = ["all", "GENERAL", "POLICY", "SHIPPING", "PRODUCT", "PROMO"];
    let search = $state("");
    let category = $state("all");

    onMount(async () => {
        await kb.fetchItems();
    });

    async function handleSearch() {
        await kb.fetchItems(category === "all" ? undefined : category, search);
    }

    function formatDate(dateStr: string) {
        return new Date(dateStr).toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: 'short', day: 'numeric'
        });
    }

    let isAllSelected = $derived(kb.items.length > 0 && kb.items.every(item => kb.selectedIds.includes(item.id)));
</script>

<div class="w-full h-full flex flex-col bg-[#050505] text-white font-['Inter'] relative overflow-hidden">
    <!-- Header: Strategic Control -->
    <div class="px-8 py-6 border-b border-white/5 bg-black/40 backdrop-blur-md flex justify-between items-center z-10">
        <div class="flex items-center gap-4">
            <div class="p-3 bg-white/5 rounded-2xl border border-white/10">
                <HelpCircle size={24} class="text-white/60" />
            </div>
            <div>
                <h1 class="text-xl font-black tracking-tight uppercase">Helen Brain</h1>
                <p class="text-[10px] text-gray-500 font-bold tracking-widest uppercase opacity-60">Neural Knowledge Base v2.2</p>
            </div>
        </div>

        <div class="flex items-center gap-3">
            <button 
                onclick={() => kb.openEdit()}
                class="bg-white text-black px-6 py-3 rounded-xl font-bold text-xs tracking-tight hover:scale-105 active:scale-95 transition-all shadow-[0_5px_15px_rgba(255,255,255,0.1)] flex items-center gap-2"
            >
                <Plus size={16} strokeWidth={3} /> THÊM TRI THỨC
            </button>
        </div>
    </div>

    <!-- Filters: Intelligence Routing -->
    <div class="px-8 py-4 border-b border-white/5 bg-black/20 flex gap-4 items-center z-10">
        <div class="relative flex-1 group">
            <input 
                type="text" 
                bind:value={search}
                oninput={handleSearch}
                placeholder="Tìm kiếm chủ đề hoặc nội dung tri thức..."
                class="w-full bg-white/5 border border-white/10 rounded-xl px-12 py-3 outline-none focus:border-white/30 focus:bg-white/[0.07] transition-all text-sm font-medium"
            />
            <div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-white transition-colors">
                <Search size={16} />
            </div>
        </div>
        
        <select 
            bind:value={category} 
            onchange={handleSearch}
            class="bg-white/5 border border-white/10 rounded-xl px-5 py-3 outline-none focus:border-white/30 appearance-none text-[10px] font-black tracking-widest cursor-pointer pr-10 transition-all uppercase"
        >
            {#each categories as cat}
                <option value={cat}>{cat}</option>
            {/each}
        </select>

        <button 
            onclick={kb.toggleSelectAll}
            class="p-3 rounded-xl border border-white/10 hover:bg-white/5 transition-all {isAllSelected ? 'text-white border-white/30' : 'text-gray-500'}"
            title="Chọn tất cả"
        >
            {#if isAllSelected}
                <CheckSquare size={18} />
            {:else}
                <Square size={18} />
            {/if}
        </button>
    </div>

    <!-- Main Content: Data Modules -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-8">
        {#if kb.loading && kb.items.length === 0}
            <div class="h-full flex flex-col items-center justify-center opacity-50">
                <XohiLogo variant="simple" size={60} />
                <p class="mt-4 text-[10px] font-black tracking-[0.3em] uppercase animate-pulse">Syncing Helen Brain...</p>
            </div>
        {:else if kb.items.length === 0}
            <div class="h-full flex flex-col items-center justify-center text-gray-600">
                <HelpCircle size={48} class="opacity-10 mb-4" />
                <p class="text-sm font-medium tracking-tight">Thưa Sếp, chưa có tri thức nào trong danh mục này.</p>
            </div>
        {:else}
            <div class="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {#each kb.items as item (item.id)}
                    <div 
                        class="kb-card group relative bg-white/[0.02] border border-white/5 rounded-3xl p-6 hover:bg-white/[0.04] hover:border-white/20 transition-all duration-300 {kb.selectedIds.includes(item.id) ? 'active-selection' : ''}"
                        in:fly={{ y: 20, duration: 400 }}
                    >
                        <div class="flex justify-between items-start mb-4">
                            <div class="flex items-center gap-2">
                                <button 
                                    onclick={() => kb.toggleSelect(item.id)}
                                    class="p-1 rounded-md transition-colors {kb.selectedIds.includes(item.id) ? 'text-white' : 'text-gray-600 hover:text-gray-400'}"
                                >
                                    {#if kb.selectedIds.includes(item.id)}
                                        <CheckSquare size={16} />
                                    {:else}
                                        <Square size={16} />
                                    {/if}
                                </button>
                                <span class="px-2 py-0.5 rounded-full bg-white/5 text-[8px] font-black uppercase tracking-widest text-white/40 group-hover:text-white/60 transition-colors">
                                    {item.category}
                                </span>
                                {#if item.priority > 0}
                                    <Star size={12} class="text-yellow-500 fill-yellow-500" />
                                {/if}
                            </div>

                            <!-- Neural Toggle -->
                            <button 
                                onclick={() => kb.toggleActive(item.id, !item.is_active)}
                                class="relative w-8 h-4 rounded-full transition-colors cursor-pointer {item.is_active ? 'bg-white/20' : 'bg-red-500/10'}"
                            >
                                <div class="absolute top-0.5 left-0.5 w-3 h-3 rounded-full transition-all {item.is_active ? 'translate-x-4 bg-white shadow-[0_0_8px_rgba(255,255,255,1)]' : 'bg-red-500/50'}"></div>
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
                            <span class="text-[8px] font-mono text-gray-700 uppercase tracking-tighter">{formatDate(item.created_at)}</span>
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Bulk Actions Component -->
    <SupportKnowledgeBulkActions />

    <!-- Neural Editor Modal -->
    {#if kb.showModal}
        <div class="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/90 backdrop-blur-md" in:fade>
            <div 
                class="w-full max-w-xl bg-[#0a0a0a] border border-white/10 rounded-[2.5rem] p-10 shadow-2xl relative overflow-hidden"
                in:scale={{ start: 0.9, duration: 400 }}
            >
                <!-- Backdrop Decoration -->
                <div class="absolute -right-20 -top-20 w-60 h-60 bg-white/[0.02] rounded-full blur-[100px] pointer-events-none"></div>

                <div class="flex justify-between items-center mb-8">
                    <div>
                        <h2 class="text-2xl font-black tracking-tighter uppercase">Biên tập Tri thức</h2>
                        <p class="text-[9px] text-gray-500 font-black tracking-[0.2em] uppercase">Neural Source Configuration</p>
                    </div>
                    <button onclick={() => kb.showModal = false} class="p-3 hover:bg-white/5 rounded-full text-gray-500 hover:text-white transition-all">✕</button>
                </div>

                <div class="grid gap-6">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="field">
                            <label class="block text-[9px] font-black uppercase text-gray-600 mb-2 tracking-widest" for="category">Phân loại</label>
                            <input 
                                id="category"
                                list="cat-suggestions"
                                bind:value={kb.editingItem!.category}
                                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-white/30 text-[10px] font-black uppercase transition-all tracking-widest"
                            />
                            <datalist id="cat-suggestions">
                                {#each categories.filter(c => c !== "all") as c}
                                    <option value={c}>{c}</option>
                                {/each}
                            </datalist>
                        </div>
                        <div class="field">
                            <label class="block text-[9px] font-black uppercase text-gray-600 mb-2 tracking-widest" for="priority">Priority Star</label>
                            <input 
                                id="priority"
                                type="number" 
                                bind:value={kb.editingItem!.priority}
                                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-white/30 text-xs font-bold transition-all"
                            />
                        </div>
                    </div>

                    <div class="field">
                        <label class="block text-[9px] font-black uppercase text-gray-600 mb-2 tracking-widest" for="question">Mẫu câu hỏi (Trigger)</label>
                        <input 
                            id="question"
                            bind:value={kb.editingItem!.question}
                            placeholder="Ví dụ: Chính sách bảo hành như thế nào?"
                            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-white/30 text-xs font-bold transition-all"
                        />
                    </div>

                    <div class="field">
                        <label class="block text-[9px] font-black uppercase text-gray-600 mb-2 tracking-widest" for="answer">Câu trả lời (Output)</label>
                        <textarea 
                            id="answer"
                            bind:value={kb.editingItem!.answer}
                            placeholder="Nhập nội dung tri thức chuẩn để Helen học theo..."
                            rows="5"
                            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-white/30 text-xs font-medium leading-relaxed transition-all resize-none"
                        ></textarea>
                    </div>

                    <div class="flex items-center gap-4 py-2">
                        <label class="flex items-center gap-3 cursor-pointer group">
                            <div class="relative w-10 h-5 rounded-full transition-colors bg-white/5 border border-white/10 group-hover:border-white/30">
                                <input type="checkbox" bind:checked={kb.editingItem!.is_active} class="hidden" />
                                <div class="absolute top-1 left-1 w-3 h-3 rounded-full transition-all {kb.editingItem!.is_active ? 'translate-x-5 bg-white' : 'bg-gray-600'}"></div>
                            </div>
                            <span class="text-[9px] font-black uppercase tracking-widest {kb.editingItem!.is_active ? 'text-white' : 'text-gray-600'} transition-colors">Trạng thái Neuron</span>
                        </label>
                    </div>

                    <div class="flex gap-4 mt-6">
                        <button 
                            onclick={() => kb.saveItem(kb.editingItem!)}
                            class="flex-1 bg-white text-black py-4 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-gray-200 transition-all"
                        >
                            SYNC_KNOWLEDGE
                        </button>
                        <button 
                            onclick={() => kb.showModal = false}
                            class="px-8 bg-white/5 text-gray-500 py-4 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-white/10 hover:text-white transition-all"
                        >
                            CANCEL
                        </button>
                    </div>
                </div>
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
        background: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 0 30px rgba(255, 255, 255, 0.05) inset;
    }

    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
</style>
