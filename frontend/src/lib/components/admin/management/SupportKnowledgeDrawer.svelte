<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import Save from "@lucide/svelte/icons/save";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Activity from "@lucide/svelte/icons/activity";
  import HelpCircle from "@lucide/svelte/icons/help-circle";
  import Star from "@lucide/svelte/icons/star";
  import Power from "@lucide/svelte/icons/power";
  import PowerOff from "@lucide/svelte/icons/power-off";
import X from "@lucide/svelte/icons/x";
import ChevronDown from "@lucide/svelte/icons/chevron-down";
import UploadCloud from "@lucide/svelte/icons/upload-cloud";
import FileText from "@lucide/svelte/icons/file-text";
    import { supportKbAdmin as kb } from '$lib/state/admin/supportKnowledge.svelte';
    import { portal } from "$lib/core/actions/portal";
    import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
    import { apiClient } from "$lib/utils/apiClient";

    let {
        isOpen = $bindable(),
        onClose
    } = $props<{
        isOpen: boolean;
        onClose: () => void;
    }>();

    const categories = ["GENERAL", "POLICY", "SHIPPING", "PRODUCT", "PROMO"];
    
    let products = $state<{id: string, name: string}[]>([]);
    let isProductDropdownOpen = $state(false);
    let productSearchQuery = $state("");
    let fileInput: HTMLInputElement;
    let isUploadingPDF = $state(false);

    async function handleUpload(file: File) {
        if (!file) return;
        isUploadingPDF = true;
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('folder', 'rag_documents');
            const res = await apiClient.upload<{data: {url: string}}>('/api/v1/admin/media/upload', formData);
            if (res && res.data && res.data.url) {
                kb.editingItem!.source_url = res.data.url;
            }
        } catch (e) {
            console.error(e);
            alert("Lỗi tải file lên!");
        } finally {
            isUploadingPDF = false;
        }
    }

    let filteredProducts = $derived.by(() => {
        if (!productSearchQuery) return products;
        const searchLower = productSearchQuery.toLowerCase().trim();
        
        return products.filter(p => {
            const nameLower = p.name.toLowerCase();
            // 1. Direct substring match (either way)
            if (nameLower.includes(searchLower)) return true;
            if (searchLower.includes(nameLower)) return true;
            
            // 2. Word by word match (if all words in the search query exist in the product name)
            const searchWords = searchLower.split(/\s+/).filter(w => w.length > 0);
            if (searchWords.length > 0 && searchWords.every(w => nameLower.includes(w))) return true;
            
            return false;
        });
    });

    let selectedProductName = $derived.by(() => {
        if (!kb.editingItem?.product_id) return "-- Áp dụng cho toàn bộ cửa hàng (Tri thức chung) --";
        return products.find(p => p.id === kb.editingItem.product_id)?.name || kb.editingItem.product_id;
    });

    $effect(() => {
        if (isOpen && products.length === 0) {
            apiClient.get('/api/v1/products?limit=100').then((res: any) => {
                if (res && res.data) {
                    products = res.data;
                }
            }).catch(console.error);
        }
    });
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
                        <h2 class="text-base font-black text-cyan-400 tracking-tighter ">
                            Neural Sync
                        </h2>
                        <p class="text-[9px] font-mono text-cyan-500/40 tracking-[0.2em]">Core Database Synchronization</p>
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
                        <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="category">Neural_Category</label>
                        <div class="relative group">
                            <select 
                                id="category"
                                bind:value={kb.editingItem.category}
                                class="w-full bg-[#111]/80 border border-white/5 rounded-2xl px-6 py-4 text-[10px] font-mono font-black tracking-widest text-cyan-400 outline-none focus:border-cyan-500/30 transition-all shadow-inner cursor-pointer appearance-none group-hover:bg-[#111]"
                            >
                                {#each categories as c}
                                    <option value={c}>{c}</option>
                                {/each}
                            </select>
                            <div class="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-cyan-500/30 group-hover:text-cyan-400 transition-colors">
                                <HelpCircle size={12} />
                            </div>
                        </div>
                        <p class="text-[10px] text-gray-500 italic px-2 leading-relaxed">
                            <span class="text-cyan-500/60 font-bold">Tip:</span> Phân loại tri thức. VD: Chọn 'POLICY' cho chính sách đổi trả, 'PRODUCT' cho kiến thức sản phẩm.
                        </p>
                    </div>
                    <div class="space-y-3">
                        <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="priority">Priority_Weight</label>
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
                            class="w-full bg-white/10 border border-white/20 rounded-2xl px-6 py-4 text-xs font-mono font-bold text-cyan-400 outline-none focus:border-cyan-500/50 transition-all text-center" 
                        />
                        <p class="text-[10px] text-gray-500 italic px-2 leading-relaxed text-center mt-1">
                            Trọng số ưu tiên (0-100). Số càng lớn, AI càng ưu tiên lấy dữ liệu này khi câu hỏi bị trùng lặp.
                        </p>
                    </div>
                </div>

                <div class="space-y-3">
                    <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="question">
                        {#if !kb.editingItem.source_type || kb.editingItem.source_type === 'TEXT'}
                            Neural_Input (Câu hỏi / Prompt Kích hoạt)
                        {:else}
                            Neural_Title (Tên Tài Liệu / Chủ Đề Chính)
                        {/if}
                    </label>
                    <input 
                        id="question"
                        bind:value={kb.editingItem.question}
                        type="text" 
                        placeholder={(!kb.editingItem.source_type || kb.editingItem.source_type === 'TEXT') ? "Ví dụ: Chính sách đổi trả hàng là gì?..." : "Ví dụ: Hướng dẫn sử dụng chi tiết sản phẩm A..."}
                        class="w-full bg-white/10 border border-white/20 rounded-2xl px-6 py-4 text-sm font-bold text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-500/50 transition-all shadow-inner"
                    />
                    <p class="text-[10px] text-gray-500 italic px-2 leading-relaxed">
                        {#if !kb.editingItem.source_type || kb.editingItem.source_type === 'TEXT'}
                            <span class="text-cyan-500/60 font-bold">Tip:</span> Đây là "câu mồi" để Vector DB tìm ra tri thức này. VD: "Thời gian giao hàng mất bao lâu?".
                        {:else}
                            <span class="text-cyan-500/60 font-bold">Tip:</span> Đặt tên rõ ràng để AI hiểu nội dung tài liệu. VD: "Tài liệu đào tạo thành phần Niacinamide".
                        {/if}
                    </p>
                </div>

                <div class="space-y-3">
                    <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="product_id">Target_Product_ID (Tùy chọn)</label>
                    <div class="relative">
                        <!-- Clickable Header -->
                        <div 
                            class="w-full bg-white/10 border border-white/20 rounded-2xl px-6 py-4 text-sm font-bold text-cyan-400 outline-none cursor-pointer hover:bg-[#222] flex justify-between items-center transition-all shadow-inner"
                            onclick={() => isProductDropdownOpen = !isProductDropdownOpen}
                        >
                            <span class="truncate pr-4">{selectedProductName}</span>
                            <ChevronDown size={14} class="text-cyan-500/50 flex-shrink-0" />
                        </div>

                        <!-- Dropdown Menu -->
                        {#if isProductDropdownOpen}
                            <!-- Transparent Backdrop to close on click outside -->
                            <!-- svelte-ignore a11y_click_events_have_key_events -->
                            <!-- svelte-ignore a11y_no_static_element_interactions -->
                            <div class="fixed inset-0 z-40" onclick={() => isProductDropdownOpen = false}></div>

                            <div class="absolute z-50 mt-2 w-full bg-[#0a0a0a] border border-white/20 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-64 shadow-cyan-900/20">
                                <!-- Search Input -->
                                <div class="p-3 border-b border-white/10 sticky top-0 bg-[#0a0a0a] z-10">
                                    <input 
                                        type="text" 
                                        bind:value={productSearchQuery}
                                        placeholder="🔍 Tìm tên sản phẩm..."
                                        class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-500/50 font-medium"
                                        onclick={(e) => e.stopPropagation()}
                                        onkeydown={(e) => e.stopPropagation()}
                                    />
                                </div>
                                
                                <!-- Options -->
                                <div class="overflow-y-auto custom-scrollbar">
                                    <button 
                                        class="w-full text-left px-5 py-4 text-xs font-bold text-cyan-400/80 hover:bg-cyan-500/10 hover:text-cyan-400 transition-colors border-b border-white/5"
                                        onclick={() => { kb.editingItem.product_id = null; isProductDropdownOpen = false; productSearchQuery = ""; }}
                                    >
                                        -- Áp dụng cho toàn bộ cửa hàng (Tri thức chung) --
                                    </button>
                                    {#each filteredProducts as p}
                                        <button 
                                            class="w-full text-left px-5 py-3 text-xs text-gray-300 hover:bg-cyan-500/10 hover:text-cyan-400 transition-colors border-b border-white/5 truncate font-medium"
                                            onclick={() => { kb.editingItem!.product_id = p.id; isProductDropdownOpen = false; productSearchQuery = ""; }}
                                        >
                                            {p.name}
                                        </button>
                                    {/each}
                                    {#if filteredProducts.length === 0}
                                        <div class="p-4 text-center text-xs text-gray-500">Không tìm thấy sản phẩm nào</div>
                                    {/if}
                                </div>
                            </div>
                        {/if}
                    </div>
                    <p class="text-[10px] text-gray-500 italic px-2 leading-relaxed">
                        <span class="text-cyan-500/60 font-bold">Tip:</span> Nếu tri thức này chỉ đúng với 1 sản phẩm cụ thể (VD: "Cách dùng Sữa rửa mặt X"), hãy chọn sản phẩm đó. AI sẽ ưu tiên lấy nếu khách đang xem đúng món hàng này.
                    </p>
                </div>

                <div class="grid grid-cols-2 gap-6">
                    <div class="space-y-3">
                        <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="source_type">Data_Source_Type</label>
                        <div class="relative group">
                            <select 
                                id="source_type"
                                value={kb.editingItem.source_type || 'TEXT'}
                                onchange={(e) => kb.editingItem!.source_type = e.currentTarget.value as any}
                                class="w-full bg-white/10 border border-white/20 rounded-2xl px-6 py-4 text-[10px] font-mono font-black tracking-widest text-cyan-400 outline-none focus:border-cyan-500/50 transition-all shadow-inner cursor-pointer appearance-none group-hover:bg-[#222]"
                            >
                                <option value="TEXT">RAW_TEXT (Nhập tay)</option>
                                <option value="URL">WEB_URL (Link bài viết)</option>
                                <option value="PDF">DOCUMENT (File PDF, DOCX)</option>
                            </select>
                            <div class="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-cyan-500/30 group-hover:text-cyan-400 transition-colors">
                                <HelpCircle size={12} />
                            </div>
                        </div>
                        <p class="text-[10px] text-gray-500 italic px-2 leading-relaxed">
                            <span class="text-cyan-500/60 font-bold">Tip:</span> Quyết định nguồn tri thức. <b>TEXT</b>: Nhập tay 1 câu trả lời. <b>URL</b>: Gắn link bài báo/blog. <b>PDF</b>: Gắn file tài liệu dài.
                        </p>
                    </div>
                </div>

                <div class="space-y-3">
                    <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="answer">Neural_Output (Prepared Response / Knowledge)</label>
                    {#if !kb.editingItem.source_type || kb.editingItem.source_type === 'TEXT'}
                        <textarea 
                            id="answer"
                            bind:value={kb.editingItem.answer}
                            rows="8"
                            placeholder="RESPONSE_DATA: Nhập tri thức chuẩn hóa để Helen phản hồi khách hàng..."
                            class="w-full bg-white/10 border border-white/20 rounded-3xl px-6 py-5 text-sm font-medium leading-relaxed text-gray-200 placeholder:text-white/30 focus:outline-none focus:border-cyan-500/50 transition-all shadow-inner resize-none font-mono"
                        ></textarea>
                        <p class="text-[10px] text-gray-500 italic px-2 leading-relaxed">
                            <span class="text-cyan-500/60 font-bold">Tip:</span> Đây là dữ liệu Helen sẽ đọc và lấy làm cơ sở để trả lời. Hãy viết chuẩn, ngắn gọn và có cấu trúc. AI có thể viết lại theo tone giọng riêng nên không cần quá chau chuốt văn phong.
                        </p>
                    {:else if kb.editingItem.source_type === 'URL'}
                        <textarea 
                            bind:value={kb.editingItem.source_url}
                            rows="4"
                            placeholder="Nhập 1 hoặc nhiều đường dẫn URL bài viết/blog (Mỗi link 1 dòng)..."
                            class="w-full bg-white/10 border border-white/20 rounded-2xl px-6 py-4 text-sm font-medium text-cyan-300 placeholder:text-white/30 focus:outline-none focus:border-cyan-500/50 transition-all shadow-inner font-mono resize-none"
                        ></textarea>
                        <p class="text-[10px] text-gray-500 italic px-2 leading-relaxed">
                            <span class="text-cyan-500/60 font-bold">Tip:</span> Bạn có thể nhập nhiều link (mỗi link 1 dòng). Crawler sẽ tự động quét và băm vào Vector DB để huấn luyện Helen. VD: <code>https://vnexpress.net/abc</code>.
                        </p>
                    {:else if kb.editingItem.source_type === 'PDF'}
                        <div 
                            class="relative w-full border-2 border-dashed border-white/20 rounded-3xl p-8 hover:border-cyan-500/50 transition-colors bg-white/5 flex flex-col items-center justify-center cursor-pointer group"
                            onclick={() => fileInput.click()}
                            aria-hidden="true"
                        >
                            <input 
                                bind:this={fileInput}
                                type="file" 
                                accept=".pdf,.doc,.docx"
                                class="hidden"
                                onchange={(e) => {
                                    const file = e.currentTarget.files?.[0];
                                    if (file) handleUpload(file);
                                }}
                            />
                            {#if isUploadingPDF}
                                <div class="text-cyan-400 font-bold animate-pulse flex flex-col items-center gap-3">
                                    <Activity class="animate-spin-slow" size={32} />
                                    <span>Đang tải file lên...</span>
                                </div>
                            {:else if kb.editingItem.source_url}
                                <div class="flex flex-col items-center gap-2">
                                    <FileText size={32} class="text-green-400" />
                                    <div class="text-green-400 font-bold truncate max-w-[300px] px-4">{kb.editingItem.source_url.split('/').pop() || "Đã đính kèm File"}</div>
                                    <div class="text-[10px] text-gray-500 mt-2 hover:text-cyan-400 transition-colors">Bấm để tải file khác</div>
                                </div>
                            {:else}
                                <div class="text-white/30 group-hover:text-cyan-400 transition-colors mb-4 scale-150">
                                    <UploadCloud size={32} />
                                </div>
                                <div class="text-sm font-bold text-gray-300 group-hover:text-cyan-300 transition-colors">Kéo thả hoặc click để tải lên File PDF/DOC</div>
                            {/if}
                        </div>
                        <p class="text-[10px] text-gray-500 italic px-2 leading-relaxed">
                            <span class="text-cyan-500/60 font-bold">Tip:</span> File sẽ được tự động tải lên Server. Sau đó Worker chạy ngầm sẽ bóc tách text và đưa vào Vector DB.
                        </p>
                    {/if}
                </div>

                <!-- Heartbeat Selection -->
                <div class="space-y-4">
                    <div class="text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1">Activation_Protocol</div>
                    <button
                        onclick={() => kb.editingItem!.is_active = !kb.editingItem!.is_active}
                        class="w-full p-6 rounded-3xl bg-white/[0.02] border border-white/5 flex items-center justify-between group/status transition-all hover:bg-cyan-500/[0.02] hover:border-cyan-500/20"
                    >
                        <div class="flex items-center gap-5">
                            <div class="w-14 h-7 rounded-full transition-colors duration-500 relative {kb.editingItem.is_active ? 'bg-cyan-500' : 'bg-red-500/20'}">
                                <div class="absolute top-1 left-1 w-5 h-5 rounded-full bg-white transition-transform duration-500 {kb.editingItem.is_active ? 'translate-x-7' : ''} shadow-lg shadow-black/50"></div>
                            </div>
                            <span class="text-[11px] font-black tracking-[0.1em] {kb.editingItem.is_active ? 'text-cyan-400' : 'text-red-500'}">
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
                        class="flex-1 py-5 rounded-2xl bg-cyan-500 text-black text-[11px] font-black tracking-widest hover:bg-cyan-400 active:scale-[0.98] transition-all shadow-[0_15px_40px_-5px_rgba(8,145,178,0.4)] disabled:opacity-50 flex items-center justify-center relative group/save overflow-hidden"
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
                        class="px-8 py-5 rounded-2xl bg-white/5 border border-white/5 text-gray-500 hover:text-white hover:bg-white/10 hover:border-white/10 font-mono text-[10px] font-black tracking-widest transition-all"
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
