<script lang="ts">
    import { fade, fly } from "svelte/transition";
    import { 
        X, Save, RefreshCw, Activity, HelpCircle, Star, Power, PowerOff
    } from "lucide-svelte";
    import { supportKbAdmin as kb } from '$lib/state/admin/supportKnowledge.svelte';
    import { portal } from "$lib/core/actions/portal";
    import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

    let {
        isOpen = $bindable(),
        onClose
    } = $props<{
        isOpen: boolean;
        onClose: () => void;
    }>();

    const categories = ["GENERAL", "POLICY", "SHIPPING", "PRODUCT", "PROMO"];
</script>

{#if isOpen && kb.editingItem}
    <div use:portal class="relative" style="z-index: {Z_INDEX_ADMIN.MODAL};">
        <!-- Backdrop -->
        <div
            class="fixed inset-0 bg-black/90 backdrop-blur-md"
            style="z-index: {Z_INDEX_ADMIN.OVERLAY};"
            transition:fade={{ duration: 300 }}
            onclick={onClose}
            aria-label="Close drawer"
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === 'Escape' && onClose()}
        ></div>

        <!-- Drawer Panel: Neural Sync (Right Aligned) -->
        <div
            class="fixed top-0 right-0 h-full w-[500px] max-w-full bg-[#020202] border-l border-cyan-500/10 shadow-[-30px_0_60px_rgba(0,0,0,0.9)] flex flex-col overflow-hidden"
            transition:fly={{ x: 500, duration: 400, opacity: 1 }}
            style="z-index: {Z_INDEX_ADMIN.MODAL + 10};"
        >
            <!-- Header -->
            <div class="h-20 flex items-center justify-between px-8 border-b border-cyan-500/10 relative bg-black/40">
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                        <Activity size={18} class="text-cyan-400 animate-pulse" />
                    </div>
                    <div>
                        <h2 class="text-base font-black text-cyan-400 tracking-tighter uppercase">
                            Neural Sync
                        </h2>
                        <p class="text-[9px] font-mono text-cyan-500/40 uppercase tracking-[0.2em]">Core Database Synchronization</p>
                    </div>
                </div>
                <button 
                    onclick={onClose}
                    class="w-10 h-10 flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/5 rounded-full transition-all border border-transparent hover:border-white/10"
                >
                    <X size={20} />
                </button>

                <div class="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent"></div>
            </div>

            <!-- Form Body -->
            <div class="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-10">
                <div class="grid grid-cols-2 gap-6">
                    <div class="space-y-3">
                        <label class="block text-[9px] font-mono font-black uppercase text-cyan-500/40 tracking-widest ml-1" for="category">Neural_Category</label>
                        <div class="relative group">
                            <select 
                                id="category"
                                bind:value={kb.editingItem.category}
                                class="w-full bg-[#111]/80 border border-white/5 rounded-2xl px-6 py-4 text-[10px] font-mono font-black uppercase tracking-widest text-cyan-400 outline-none focus:border-cyan-500/30 transition-all shadow-inner cursor-pointer appearance-none group-hover:bg-[#111]"
                            >
                                {#each categories as c}
                                    <option value={c}>{c}</option>
                                {/each}
                            </select>
                            <div class="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-cyan-500/30 group-hover:text-cyan-400 transition-colors">
                                <HelpCircle size={12} />
                            </div>
                        </div>
                    </div>
                    <div class="space-y-3">
                        <label class="block text-[9px] font-mono font-black uppercase text-cyan-500/40 tracking-widest ml-1" for="priority">Priority_Weight</label>
                        <input 
                            id="priority"
                            type="text" 
                            inputmode="numeric"
                            value={kb.editingItem.priority}
                            oninput={(e) => {
                                const val = e.currentTarget.value.replace(/[^0-9]/g, '');
                                kb.editingItem!.priority = val ? parseInt(val) : 0;
                                e.currentTarget.value = kb.editingItem!.priority.toString();
                            }}
                            class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-xs font-mono font-bold text-cyan-400 outline-none focus:border-cyan-500/30 transition-all text-center" 
                        />
                    </div>
                </div>

                <div class="space-y-3">
                    <label class="block text-[9px] font-mono font-black uppercase text-cyan-500/40 tracking-widest ml-1" for="question">Neural_Input (Trigger Prompt / Question)</label>
                    <input 
                        id="question"
                        bind:value={kb.editingItem.question}
                        type="text" 
                        placeholder="PROMPT_ENTRY: Ví dụ: Chính sách đổi trả hàng..."
                        class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-sm font-bold text-white placeholder:text-white/5 focus:outline-none focus:border-cyan-500/30 transition-all shadow-inner"
                    />
                </div>

                <div class="space-y-3">
                    <label class="block text-[9px] font-mono font-black uppercase text-cyan-500/40 tracking-widest ml-1" for="answer">Neural_Output (Prepared Response / Knowledge)</label>
                    <textarea 
                        id="answer"
                        bind:value={kb.editingItem.answer}
                        rows="8"
                        placeholder="RESPONSE_DATA: Nhập tri thức chuẩn hóa để Helen phản hồi khách hàng..."
                        class="w-full bg-white/[0.03] border border-white/5 rounded-3xl px-6 py-5 text-sm font-medium leading-relaxed text-gray-300 placeholder:text-white/5 focus:outline-none focus:border-cyan-500/30 transition-all shadow-inner resize-none font-mono"
                    ></textarea>
                </div>

                <!-- Heartbeat Selection -->
                <div class="space-y-4">
                    <div class="text-[9px] font-mono font-black text-cyan-500/40 uppercase tracking-widest ml-1">Activation_Protocol</div>
                    <button
                        onclick={() => kb.editingItem!.is_active = !kb.editingItem!.is_active}
                        class="w-full p-6 rounded-3xl bg-white/[0.02] border border-white/5 flex items-center justify-between group/status transition-all hover:bg-cyan-500/[0.02] hover:border-cyan-500/20"
                    >
                        <div class="flex items-center gap-5">
                            <div class="w-14 h-7 rounded-full transition-colors duration-500 relative {kb.editingItem.is_active ? 'bg-cyan-500' : 'bg-red-500/20'}">
                                <div class="absolute top-1 left-1 w-5 h-5 rounded-full bg-white transition-transform duration-500 {kb.editingItem.is_active ? 'translate-x-7' : ''} shadow-lg shadow-black/50"></div>
                            </div>
                            <span class="text-[11px] font-black uppercase tracking-[0.1em] {kb.editingItem.is_active ? 'text-cyan-400' : 'text-red-500'}">
                                {kb.editingItem.is_active ? 'Neural_Active' : 'Neural_Offline'}
                            </span>
                        </div>
                        <Activity size={20} class={kb.editingItem.is_active ? 'text-cyan-500 shadow-[0_0_15px_rgba(6,182,212,0.5)]' : 'text-zinc-800'} />
                    </button>
                </div>

                <!-- Footer Operations -->
                <div class="pt-10 flex gap-4">
                    <button 
                        onclick={async () => {
                            await kb.saveItem(kb.editingItem!);
                            onClose();
                        }}
                        disabled={kb.loading}
                        class="flex-1 py-5 rounded-2xl bg-cyan-500 text-black text-[11px] font-black uppercase tracking-widest hover:bg-cyan-400 active:scale-[0.98] transition-all shadow-[0_15px_40px_-5px_rgba(8,145,178,0.4)] disabled:opacity-50 flex items-center justify-center relative group/save overflow-hidden"
                    >
                        {#if kb.loading}
                            <RefreshCw size={18} class="animate-spin mr-3 font-black" strokeWidth={3} />
                            EXECUTING...
                        {:else}
                            EXECUTE_SYNC
                        {/if}
                        <div class="absolute inset-0 bg-white/20 -translate-x-full group-hover/save:translate-x-full transition-transform duration-1000 pointer-events-none"></div>
                    </button>
                    <button 
                        onclick={onClose}
                        class="px-8 py-5 rounded-2xl bg-white/5 border border-white/5 text-gray-500 hover:text-white hover:bg-white/10 hover:border-white/10 font-mono text-[10px] font-black uppercase tracking-widest transition-all"
                    >
                        ABORT
                    </button>
                </div>
            </div>
            
            <!-- Strategic Blur Gradient -->
            <div class="absolute bottom-0 left-0 w-full h-20 bg-gradient-to-t from-[#020202] to-transparent pointer-events-none"></div>
        </div>
    </div>
{/if}

<style>
    .custom-scrollbar::-webkit-scrollbar { width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(34, 211, 238, 0.1); border-radius: 4px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(34, 211, 238, 0.3); }

</style>
