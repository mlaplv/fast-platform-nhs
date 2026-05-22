<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import Save from "@lucide/svelte/icons/save";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Activity from "@lucide/svelte/icons/activity";
  import HelpCircle from "@lucide/svelte/icons/help-circle";
  import X from "@lucide/svelte/icons/x";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import UploadCloud from "@lucide/svelte/icons/upload-cloud";
  import FileText from "@lucide/svelte/icons/file-text";
  import Copy from "@lucide/svelte/icons/copy";
  import Check from "@lucide/svelte/icons/check";
  import Zap from "@lucide/svelte/icons/zap";
  
  import { supportKbAdmin as kb } from '$lib/state/admin/supportKnowledge.svelte';
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";

  let {
      isOpen = $bindable(),
      onClose
  } = $props<{
      isOpen: boolean;
      onClose: () => void;
  }>();

  const nanobot = useNanobot();
  const categories = ["GENERAL", "POLICY", "SHIPPING", "PRODUCT", "PROMO"];
  
  let products = $state<{id: string, name: string}[]>([]);
  let isProductDropdownOpen = $state(false);
  let productSearchQuery = $state("");
  let fileInput: HTMLInputElement;
  let isUploadingPDF = $state(false);
  let isExtracting = $state(false); // Trích xuất tức thời trên UI
  
  let answerTextarea = $state<HTMLTextAreaElement | null>(null);
  let lineNumContainer = $state<HTMLDivElement | null>(null);
  let isCopied = $state(false);

  async function copyToClipboard() {
      if (kb.editingItem?.answer) {
          await navigator.clipboard.writeText(kb.editingItem.answer);
          isCopied = true;
          nanobot.ui.showToast("Đã copy vào bộ nhớ tạm", "success");
          setTimeout(() => isCopied = false, 2000);
      }
  }

  // Reactive line count for Pro Read/Edit Column
  let lineNumbers = $derived.by(() => {
      const text = kb.editingItem?.answer || "";
      const lines = text.split('\n').length;
      return Array.from({ length: Math.max(lines, 1) }, (_, i) => i + 1);
  });

  // Reactive word/char count
  let charCount = $derived(kb.editingItem?.answer?.length || 0);
  let wordCount = $derived.by(() => {
      const text = kb.editingItem?.answer?.trim() || "";
      if (!text) return 0;
      return text.split(/\s+/).length;
  });

  function syncScroll(e: Event) {
      if (lineNumContainer && answerTextarea) {
          lineNumContainer.scrollTop = answerTextarea.scrollTop;
      }
  }

  // Frontend HTML Parser to bypass security magic byte checks for pure text extraction
  function parseHtmlToText(htmlString: string): string {
      const parser = new DOMParser();
      const doc = parser.parseFromString(htmlString, 'text/html');
      
      // Remove noisy/irrelevant elements
      const badTags = doc.querySelectorAll('script, style, nav, footer, header, svg, iframe, noscript');
      badTags.forEach(tag => tag.remove());
      
      const rawText = doc.body ? doc.body.textContent : doc.documentElement.textContent;
      if (!rawText) return "";
      
      // Clean up line breaks and excessive spaces
      const lines = rawText.split('\n').map(line => line.trim());
      return lines.filter(line => line.length > 0).join('\n');
  }

  // Unified Ingestion: Extract content from link or file immediately, output to TEXT area on right
  async function triggerExtraction() {
      if (!kb.editingItem?.source_url) {
          nanobot.ui.showToast("Vui lòng tải lên file tài liệu hoặc nhập link URL trước khi bóc tách!", "warning");
          return;
      }
      
      // Nhận diện link cục bộ và hướng dẫn Sếp bằng Modal chung hệ thống
      if (kb.editingItem.source_type === 'URL' && kb.editingItem.source_url.startsWith('file://')) {
          await nanobot.ui.showConfirm({
              title: "⚠️ [ĐƯỜNG DẪN CỤC BỘ]",
              message: "Đường dẫn file:// chỉ tồn tại trên máy tính cá nhân của Sếp. Máy chủ Docker không thể truy cập được đường dẫn này!\n\n👉 Giải pháp: Vui lòng chuyển Data_Source_Type sang 'HTML_FILE', sau đó chọn tải file HTML đó trực tiếp lên. Hệ thống sẽ bóc tách hoàn hảo 100% ngay lập tức!",
              confirmText: "ĐÃ HIỂU",
              cancelText: ""
          });
          return;
      }
      
      isExtracting = true;
      try {
          const res = await apiClient.post<{ok: boolean, text?: string, error?: string}>('/api/v1/admin/support/knowledge/extract', {
              source_type: kb.editingItem.source_type,
              source_url: kb.editingItem.source_url
          });
          
          if (res && res.ok && res.text) {
              kb.editingItem = { ...kb.editingItem, answer: res.text };
              nanobot.ui.showToast("Bóc tách tri thức thành công! ⚡ Sếp có thể hiệu chỉnh văn bản ở khung bên phải.", "success");
          } else {
              nanobot.ui.showToast(res?.error || "Không thể bóc tách nội dung từ nguồn này. Vui lòng kiểm tra lại.", "error");
          }
      } catch (e) {
          console.error("[Extraction] Error:", e);
          nanobot.ui.showToast("Lỗi kết nối hoặc xử lý bóc tách tri thức!", "error");
      } finally {
          isExtracting = false;
      }
  }

  async function handleUpload(file: File) {
      if (!file) return;
      
      const ext = file.name.split('.').pop()?.toLowerCase();
      
      // VÁ LỖI TẢI FILE HTML: Đọc trực tiếp trên trình duyệt bằng FileReader.
      // Giải quyết triệt để lỗi "Mismatched Magic Bytes" và XSS Security của API media.
      if (ext === 'html' || ext === 'htm' || ext === 'txt' || ext === 'md') {
          const reader = new FileReader();
          reader.onload = (e) => {
              const content = e.target?.result as string;
              if (content) {
                  let text = '';
                  if (ext === 'html' || ext === 'htm') {
                      text = parseHtmlToText(content);
                  } else {
                      text = content.split('\n').map(l => l.trim()).filter(l => l.length > 0).join('\n');
                  }
                  
                  if (kb.editingItem) {
                      kb.editingItem = {
                          ...kb.editingItem,
                          answer: text,
                          source_url: file.name,
                          source_type: 'HTML'
                      };
                  }
                  console.log("[FileReader] HTML file loaded directly, text length:", text.length);
                  nanobot.ui.showToast("Bóc tách file HTML trực tiếp thành công! ⚡ Đã điền text trần vào ô soạn thảo.", "success");
              }
          };
          reader.readAsText(file);
          return;
      }
      
      // Với các định dạng được server cho phép upload như PDF/DOCX
      isUploadingPDF = true;
      try {
          const formData = new FormData();
          formData.append('data', file);
          const res = await apiClient.upload<{data: {file_path: string}}>('/api/v1/media', formData);
          
          let uploadedUrl = '';
          if (res && res.data) {
              uploadedUrl = res.data.file_path || (res.data as any).url || '';
          }
          if (!uploadedUrl && (res as any).file_path) {
              uploadedUrl = (res as any).file_path;
          }
          
          if (uploadedUrl) {
              kb.editingItem!.source_url = uploadedUrl;
              nanobot.ui.showToast("Đã tải file lên máy chủ thành công. Hãy bấm nút Bóc Tách để trích xuất!", "success");
          } else {
              throw new Error("Không lấy được đường dẫn URL từ server");
          }
      } catch (e) {
          console.error(e);
          nanobot.ui.showToast("Lỗi tải file lên! Máy chủ chỉ cho phép upload PDF/DOCX vì lý do an toàn.", "error");
      } finally {
          isUploadingPDF = false;
      }
  }

  let filteredProducts = $derived.by(() => {
      if (!productSearchQuery) return products;
      const searchLower = productSearchQuery.toLowerCase().trim();
      
      return products.filter(p => {
          const nameLower = p.name.toLowerCase();
          if (nameLower.includes(searchLower)) return true;
          if (searchLower.includes(nameLower)) return true;
          
          const searchWords = searchLower.split(/\s+/).filter(w => w.length > 0);
          if (searchWords.length > 0 && searchWords.every(w => nameLower.includes(w))) return true;
          
          return false;
      });
  });

  let selectedProductName = $derived.by(() => {
      if (!kb.editingItem?.product_id) return "-- Áp dụng cho toàn bộ cửa hàng (Tri thức chung) --";
      return products.find(p => p.id === kb.editingItem.product_id)?.name || kb.editingItem.product_id;
  });

  let isOptimizing = $state(false);

  async function triggerXohiOptimize() {
      console.log("[XohiOptimize] triggerXohiOptimize called");
      if (!kb.editingItem?.answer) {
          console.warn("[XohiOptimize] Aborted: kb.editingItem?.answer is empty");
          nanobot.ui.showToast("Không có nội dung văn bản nào để tối ưu!", "warning");
          return;
      }
      
      console.log("[XohiOptimize] Setting isOptimizing = true");
      isOptimizing = true;
      try {
          console.log("[XohiOptimize] Sending POST /api/v1/admin/support/knowledge/optimize, text length:", kb.editingItem.answer.length);
          const res = await apiClient.post<{ok: boolean, text?: string, error?: string}>('/api/v1/admin/support/knowledge/optimize', {
              text: kb.editingItem.answer
          });
          
          console.log("[XohiOptimize] Received response raw:", res);
          if (res && res.ok && res.text) {
              console.log("[XohiOptimize] Optimization success, updating answer");
              kb.editingItem = { ...kb.editingItem, answer: res.text };
              nanobot.ui.showToast("Đã làm sạch và tối ưu tri thức XOHI thành công! 🟢", "success");
          } else {
              console.error("[XohiOptimize] Server returned error status:", res);
              nanobot.ui.showToast(res?.error || "Không thể tối ưu hóa nội dung. Vui lòng kiểm tra lại.", "error");
          }
      } catch (e) {
          console.error("[XohiOptimize] Exception during API call:", e);
          nanobot.ui.showToast("Lỗi hệ thống khi tối ưu hóa tri thức!", "error");
      } finally {
          console.log("[XohiOptimize] Optimization completed, setting isOptimizing = false");
          isOptimizing = false;
      }
  }

  let isCheckingDuplicate = $state(false);
  let isFullscreen = $state(false);

  async function handleSave() {
      if (!kb.editingItem) return;
      
      const answer = kb.editingItem.answer?.trim() || "";
      if (!answer) {
          nanobot.ui.showToast("Vui lòng nhập nội dung tri thức trước khi lưu!", "warning");
          return;
      }
      
      isCheckingDuplicate = true;
      try {
          const checkRes = await apiClient.post<{
              ok: boolean, 
              has_duplicate?: boolean, 
              duplicates?: Array<{id: string, question: string, match_score: number, snippet: string}>,
              error?: string
          }>('/api/v1/admin/support/knowledge/check-duplicate', {
              text: answer,
              current_id: kb.editingItem.id || null,
              threshold: 0.82
          });
          
          if (checkRes && checkRes.ok && checkRes.has_duplicate && checkRes.duplicates && checkRes.duplicates.length > 0) {
              const topDup = checkRes.duplicates[0];
              const similarityPercent = Math.round(topDup.match_score * 100);
              
              const confirm = await nanobot.ui.showConfirm({
                  title: "⚠️ [TRÙNG LẶP TRI THỨC TOÀN CỤC]",
                  message: `Phát hiện tri thức tương tự đã tồn tại trong Brain!\n\n` +
                           `👉 Tri thức trùng khớp: "${topDup.question}"\n` +
                           `🎯 Độ tương đồng: ${similarityPercent}%\n\n` +
                           `Để đảm bảo nguồn tri thức "Tinh Không" (không trùng lặp loãng dữ liệu), Sếp có chắc chắn muốn lưu đè (lưu mới) tri thức này không?`,
                  confirmText: "EXECUTE SAVE",
                  cancelText: "ABORT"
              });
              
              if (!confirm) return;
          }
      } catch (e) {
          console.error("[CheckDuplicate] Failed:", e);
      } finally {
          isCheckingDuplicate = false;
      }
      
      try {
          await kb.saveItem(kb.editingItem);
          nanobot.ui.showToast("Đã lưu tri thức thành công! 🟢", "success");
          onClose();
      } catch (e) {
          console.error(e);
          nanobot.ui.showToast("Lỗi hệ thống khi lưu tri thức!", "error");
      }
  }
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

      <!-- Drawer Panel: Unified Knowledge Ingestion (Expanded 2-Column Professional UI) -->
      <div
          class="fixed top-0 right-0 h-full max-w-full bg-[#020202] border-l border-cyan-500/10 shadow-[-30px_0_60px_rgba(0,0,0,0.9)] flex flex-col overflow-hidden transition-all duration-300 ease-in-out {isFullscreen ? 'w-screen' : 'w-[1000px]'}"
          transition:fly={{ x: 1000, duration: 400, opacity: 1 }}
          style="z-index: {isFullscreen ? Z_INDEX_ADMIN.TIPTAP_FULLSCREEN : Z_INDEX_ADMIN.MODAL + 10};"
      >
          <!-- Header -->
          <div class="h-20 flex items-center justify-between px-8 border-b border-cyan-500/10 relative bg-black/40 flex-shrink-0">
              <div class="flex items-center gap-4">
                  <div class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                      <Activity size={18} class="text-cyan-400 animate-pulse" />
                  </div>
                  <div>
                      <h2 class="text-base font-black text-cyan-400 tracking-tighter">
                          Neural Knowledge Sync
                      </h2>
                      <p class="text-[9px] font-mono text-cyan-500/40 tracking-[0.2em]">Unified RAG Ingestion Pipeline</p>
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

          <!-- Main Layout: 2 Columns -->
          <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
              
              <!-- LEFT COLUMN: Configurations & Unified Input Ingestion (440px) -->
              <div class="w-full md:w-[440px] border-r border-cyan-500/10 overflow-y-auto custom-scrollbar p-6 space-y-6 flex-shrink-0 bg-black/25 {isFullscreen ? 'hidden' : ''}">
                  
                  <!-- Metadata group -->
                  <div class="grid grid-cols-2 gap-4">
                      <div class="space-y-2">
                          <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="category">Neural_Category</label>
                          <div class="relative group">
                              <select 
                                  id="category"
                                  bind:value={kb.editingItem.category}
                                  class="w-full bg-[#111]/80 border border-white/5 rounded-xl px-4 py-3 text-[10px] font-mono font-black tracking-widest text-cyan-400 outline-none focus:border-cyan-500/30 transition-all cursor-pointer appearance-none group-hover:bg-[#111]"
                              >
                                  {#each categories as c}
                                      <option value={c}>{c}</option>
                                  {/each}
                              </select>
                              <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-cyan-500/30 group-hover:text-cyan-400 transition-colors">
                                  <HelpCircle size={10} />
                              </div>
                          </div>
                      </div>
                      <div class="space-y-2">
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
                              class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-xs font-mono font-bold text-cyan-400 outline-none focus:border-cyan-500/50 transition-all text-center" 
                          />
                      </div>
                  </div>

                  <div class="space-y-2">
                      <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="question">
                          Neural_Input (Câu hỏi / Prompt kích hoạt hoặc tên tài liệu)
                      </label>
                      <input 
                          id="question"
                          bind:value={kb.editingItem.question}
                          type="text" 
                          placeholder="Chính sách bảo hành / Placenta là gì?..."
                          class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-xs font-bold text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-500/50 transition-all"
                      />
                  </div>

                  <div class="space-y-2">
                      <div class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1">Target_Product_ID (Tùy chọn)</div>
                      <div class="relative">
                          <div 
                              class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-xs font-bold text-cyan-400 outline-none cursor-pointer hover:bg-[#222] flex justify-between items-center transition-all"
                              onclick={() => isProductDropdownOpen = !isProductDropdownOpen}
                              aria-hidden="true"
                          >
                              <span class="truncate pr-4">{selectedProductName}</span>
                              <ChevronDown size={12} class="text-cyan-500/50 flex-shrink-0" />
                          </div>

                          {#if isProductDropdownOpen}
                              <!-- svelte-ignore a11y_click_events_have_key_events -->
                              <!-- svelte-ignore a11y_no_static_element_interactions -->
                              <div class="fixed inset-0 z-40" onclick={() => isProductDropdownOpen = false}></div>

                              <div class="absolute z-50 mt-1 w-full bg-[#0a0a0a] border border-white/20 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-48 shadow-cyan-900/20">
                                  <div class="p-2 border-b border-white/10 sticky top-0 bg-[#0a0a0a] z-10">
                                      <input 
                                          type="text" 
                                          bind:value={productSearchQuery}
                                          placeholder="🔍 Tìm sản phẩm..."
                                          class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-[11px] text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-500/50 font-medium"
                                          onclick={(e) => e.stopPropagation()}
                                          onkeydown={(e) => e.stopPropagation()}
                                      />
                                  </div>
                                  
                                  <div class="overflow-y-auto custom-scrollbar">
                                      <button 
                                          class="w-full text-left px-4 py-2.5 text-[11px] font-bold text-cyan-400/80 hover:bg-cyan-500/10 hover:text-cyan-400 transition-colors border-b border-white/5"
                                          onclick={() => { kb.editingItem.product_id = null; isProductDropdownOpen = false; productSearchQuery = ""; }}
                                      >
                                          -- Áp dụng cho toàn bộ cửa hàng (Tri thức chung) --
                                      </button>
                                      {#each filteredProducts as p}
                                          <button 
                                              class="w-full text-left px-4 py-2 text-[11px] text-gray-300 hover:bg-cyan-500/10 hover:text-cyan-400 transition-colors border-b border-white/5 truncate font-medium"
                                              onclick={() => { kb.editingItem!.product_id = p.id; isProductDropdownOpen = false; productSearchQuery = ""; }}
                                          >
                                              {p.name}
                                          </button>
                                      {/each}
                                      {#if filteredProducts.length === 0}
                                          <div class="p-3 text-center text-[10px] text-gray-500">Không tìm thấy sản phẩm</div>
                                      {/if}
                                  </div>
                              </div>
                          {/if}
                      </div>
                  </div>

                  <!-- UNIFIED INGESTION SOURCE (Nguồn nhập liệu hợp nhất đưa về text) -->
                  <div class="space-y-4 p-4 rounded-2xl bg-cyan-500/[0.02] border border-cyan-500/10">
                      <div class="text-[9px] font-mono font-black text-cyan-400 tracking-widest">
                          Unified_Ingestion_Source (Nguồn nạp Tri thức)
                      </div>

                      <div class="space-y-2">
                          <label class="block text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1" for="source_type">Loại nguồn dữ liệu</label>
                          <select 
                              id="source_type"
                              value={kb.editingItem.source_type || 'TEXT'}
                              onchange={(e) => kb.editingItem!.source_type = e.currentTarget.value as any}
                              class="w-full bg-[#111] border border-white/10 rounded-xl px-4 py-3 text-[10px] font-mono font-black tracking-widest text-cyan-400 outline-none focus:border-cyan-500/30 transition-all cursor-pointer"
                          >
                              <option value="TEXT">RAW_TEXT (Gõ trực tiếp / Nhập bằng tay)</option>
                              <option value="URL">WEB_URL (Trích xuất từ Link bài viết)</option>
                              <option value="PDF">DOCUMENT (Trích xuất từ file PDF, DOCX)</option>
                              <option value="HTML">HTML_FILE (Trích xuất từ file HTML, TXT, MD)</option>
                          </select>
                      </div>

                      <!-- Sub inputs depending on source type -->
                      {#if kb.editingItem.source_type === 'TEXT'}
                          <div class="text-[10px] text-gray-400 font-mono leading-relaxed bg-[#0a0a0a] p-3 rounded-xl border border-white/5">
                              [Chế độ nhập tay]: Sếp chỉ cần trực tiếp gõ và chỉnh sửa nội dung văn bản ở khung ĐỌC & HIỆU CHỈNH bên phải.
                          </div>
                      {:else if kb.editingItem.source_type === 'URL'}
                          <div class="space-y-2">
                              <textarea 
                                  bind:value={kb.editingItem.source_url}
                                  rows="2"
                                  placeholder="Nhập đường dẫn URL cần trích xuất (Mỗi dòng 1 link)..."
                                  class="w-full bg-[#111] border border-white/10 rounded-xl px-4 py-3 text-xs font-medium text-cyan-300 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30 transition-all font-mono resize-none"
                              ></textarea>
                              
                              <button 
                                  onclick={triggerExtraction}
                                  disabled={isExtracting}
                                  class="w-full py-3 rounded-xl bg-yellow-500/10 border border-yellow-500/30 text-[10px] font-black font-mono text-yellow-400 hover:bg-yellow-500/20 hover:text-yellow-300 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                              >
                                  {#if isExtracting}
                                      <Activity size={12} class="animate-spin text-yellow-400" />
                                      <span>ĐANG TRÍCH XUẤT LINK...</span>
                                  {:else}
                                      <Zap size={12} class="text-yellow-400 fill-yellow-400" />
                                      <span>⚡ BÓC TÁCH LINK ĐƯA VỀ TEXT</span>
                                  {/if}
                              </button>
                          </div>
                      {:else if kb.editingItem.source_type === 'PDF' || kb.editingItem.source_type === 'HTML'}
                          <div class="space-y-2">
                              <div 
                                  class="relative w-full border border-dashed border-white/15 rounded-xl p-4 hover:border-cyan-500/30 transition-colors bg-[#111] flex flex-col items-center justify-center cursor-pointer group"
                                  onclick={() => fileInput.click()}
                                  aria-hidden="true"
                              >
                                  <input 
                                      bind:this={fileInput}
                                      type="file" 
                                      accept={kb.editingItem.source_type === 'HTML' ? '.html,.htm,.txt,.md' : '.pdf,.doc,.docx'}
                                      class="hidden"
                                      onchange={(e) => {
                                          const file = e.currentTarget.files?.[0];
                                          if (file) handleUpload(file);
                                          e.currentTarget.value = '';
                                      }}
                                  />
                                  {#if isUploadingPDF}
                                      <div class="text-cyan-400 text-[10px] font-bold animate-pulse flex flex-col items-center gap-1.5">
                                          <Activity class="animate-spin text-cyan-400" size={20} />
                                          <span>Đang tải file...</span>
                                      </div>
                                  {:else if kb.editingItem.source_url}
                                      <div class="flex flex-col items-center gap-1">
                                          <FileText size={20} class="text-green-400" />
                                          <div class="text-green-400 text-[9px] font-bold truncate max-w-[200px]">{kb.editingItem.source_url.split('/').pop()}</div>
                                          <div class="text-[8px] text-gray-500 mt-1 hover:text-cyan-400">Chọn file khác</div>
                                      </div>
                                  {:else}
                                      <UploadCloud size={20} class="text-white/20 group-hover:text-cyan-400 transition-colors mb-1" />
                                      <div class="text-[10px] text-gray-400 group-hover:text-cyan-300 transition-colors">
                                          {kb.editingItem.source_type === 'HTML' ? 'Click chọn File HTML/TXT' : 'Click chọn File PDF/DOC'}
                                      </div>
                                  {/if}
                              </div>

                              {#if kb.editingItem.source_type === 'PDF'}
                                  <button 
                                      onclick={triggerExtraction}
                                      disabled={isExtracting || !kb.editingItem.source_url}
                                      class="w-full py-3 rounded-xl bg-yellow-500/10 border border-yellow-500/30 text-[10px] font-black font-mono text-yellow-400 hover:bg-yellow-500/20 hover:text-yellow-300 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                                  >
                                      {#if isExtracting}
                                          <Activity size={12} class="animate-spin text-yellow-400" />
                                          <span>ĐANG TRÍCH XUẤT FILE...</span>
                                      {:else}
                                          <Zap size={12} class="text-yellow-400 fill-yellow-400" />
                                          <span>⚡ BÓC TÁCH FILE ĐƯA VỀ TEXT</span>
                                      {/if}
                                  </button>
                              {/if}
                          </div>
                      {/if}
                  </div>

                  <!-- Activation toggler -->
                  <div class="space-y-2">
                      <div class="text-[9px] font-mono font-black text-cyan-500/40 tracking-widest ml-1">Activation_Protocol</div>
                      <button
                          onclick={() => kb.editingItem!.is_active = !kb.editingItem!.is_active}
                          class="w-full p-4 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between group/status transition-all hover:bg-cyan-500/[0.02] hover:border-cyan-500/20"
                      >
                          <div class="flex items-center gap-4">
                              <div class="w-10 h-5 rounded-full transition-colors duration-500 relative {kb.editingItem.is_active ? 'bg-cyan-500' : 'bg-red-500/20'}">
                                  <div class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-500 {kb.editingItem.is_active ? 'translate-x-5' : ''}"></div>
                              </div>
                              <span class="text-[10px] font-black tracking-[0.1em] {kb.editingItem.is_active ? 'text-cyan-400' : 'text-red-500'}">
                                  {kb.editingItem.is_active ? 'Neural_Active' : 'Neural_Offline'}
                              </span>
                          </div>
                          <Activity size={16} class={kb.editingItem.is_active ? 'text-cyan-500' : 'text-zinc-800'} />
                      </button>
                  </div>

                  <!-- Action Buttons inside Left Panel -->
                  <div class="pt-4 flex gap-3 border-t border-cyan-500/10">
                      <button 
                          onclick={handleSave}
                          disabled={kb.loading || isExtracting || isCheckingDuplicate}
                          class="flex-1 py-4 rounded-xl bg-cyan-500 text-black text-[10px] font-black tracking-widest hover:bg-cyan-400 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center relative overflow-hidden"
                      >
                          {#if kb.loading || isCheckingDuplicate}
                              <RefreshCw size={14} class="animate-spin mr-2" />
                              {#if isCheckingDuplicate}
                                  CHECKING DUP...
                              {:else}
                                  SAVING...
                              {/if}
                          {:else}
                              EXECUTE_SAVE
                          {/if}
                      </button>
                      <button 
                          onclick={onClose}
                          class="px-6 py-4 rounded-xl bg-white/5 border border-white/5 text-gray-500 hover:text-white hover:bg-white/10 hover:border-white/10 font-mono text-[9px] font-black tracking-widest transition-all"
                      >
                          ABORT
                      </button>
                  </div>
              </div>

              <!-- RIGHT COLUMN: Professional Text Reader & Editor (560px) -->
              <div class="flex-1 flex flex-col overflow-hidden p-6 bg-black/40 relative">
                  <!-- Strategic Header & Info -->
                  <div class="flex justify-between items-center mb-3">
                      <div>
                          <label class="block text-[10px] font-mono font-black text-cyan-400 tracking-widest" for="answer_area">
                              Neural_Output (Khung đọc nội dung & Hiệu chỉnh Tri thức)
                          </label>
                          <span class="text-[10px] text-gray-500 font-medium">Toàn bộ dữ liệu bóc tách được từ link/file được đưa về text thuần tại đây để Sếp đọc và hiệu chỉnh trực tiếp</span>
                      </div>
                      
                      <!-- Char & Word indicators -->
                      <div class="text-[10px] font-mono text-cyan-500/30 flex items-center gap-4">
                          <span>WORDS: <strong class="text-cyan-400/80">{wordCount}</strong></span>
                          <span>CHARS: <strong class="text-cyan-400/80">{charCount}</strong></span>
                      </div>
                  </div>

                  <!-- Professional Editor Box -->
                  <div class="flex-1 flex flex-col border border-white/10 rounded-2xl overflow-hidden bg-[#050505]/95 shadow-inner focus-within:border-cyan-500/30 transition-colors">
                      
                      <!-- Toolbar: Minimalist (Only Copy Action) -->
                      <div class="h-10 flex items-center justify-between px-4 border-b border-white/5 bg-[#0f0f0f]/90 select-none">
                          <div class="flex items-center gap-1.5">
                              <span class="text-[9px] font-mono font-black text-cyan-500/50 tracking-wider">TEXT_EDITOR // WYSIWYG DISABLED</span>
                          </div>

                          <div class="flex items-center gap-2">
                              <!-- Nút Tối ưu tri thức Xohi -->
                              <button 
                                  onclick={triggerXohiOptimize}
                                  disabled={isOptimizing || !kb.editingItem?.answer}
                                  class="h-7 px-3 rounded-lg bg-pink-500/10 border border-pink-500/30 text-[10px] font-mono text-pink-400 hover:bg-pink-500/20 hover:text-pink-300 transition-all flex items-center gap-1.5 disabled:opacity-50 relative overflow-hidden group/xohi active:scale-[0.98]"
                              >
                                  {#if isOptimizing}
                                      <Activity size={11} class="animate-spin text-pink-400" />
                                      <span class="tracking-widest">XOHI OPTIMIZING...</span>
                                  {:else}
                                      <Zap size={11} class="text-pink-400 fill-pink-400 group-hover/xohi:animate-bounce" />
                                      <span class="tracking-widest">✨ XOHI NEURAL OPTIMIZE</span>
                                  {/if}
                              </button>

                              <!-- Copy Action -->
                              <button 
                                  onclick={copyToClipboard}
                                  class="h-7 px-3 rounded-lg hover:bg-white/5 text-[10px] font-mono text-gray-400 hover:text-cyan-400 transition-all flex items-center gap-1.5 border border-transparent hover:border-white/5"
                              >
                                  {#if isCopied}
                                      <Check size={11} class="text-green-400" />
                                      <span class="text-green-400">COPIED!</span>
                                  {:else}
                                      <Copy size={11} />
                                      <span>COPY</span>
                                  {/if}
                              </button>

                              <!-- Fullscreen Action -->
                              <button 
                                  onclick={() => isFullscreen = !isFullscreen}
                                  class="h-7 px-3 rounded-lg hover:bg-white/5 text-[10px] font-mono text-gray-400 hover:text-cyan-400 transition-all flex items-center gap-1.5 border border-transparent hover:border-white/5 active:scale-95"
                                  title={isFullscreen ? "Exit Fullscreen" : "Full Screen View"}
                              >
                                  {#if isFullscreen}
                                      <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-cyan-400"><path d="M4 14h6v6M20 10h-6V4M14 10l7-7M10 14l-7 7"/></svg>
                                      <span>EXIT_FULLSCREEN</span>
                                  {:else}
                                      <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
                                      <span>FULLSCREEN</span>
                                  {/if}
                              </button>
                          </div>
                      </div>

                      <!-- Editor Workspace (Line Numbers + Textarea) -->
                      <div class="flex-1 flex overflow-hidden relative">
                          
                          <!-- Hiệu ứng quét tia sáng laser khi đang tối ưu hóa -->
                          {#if isOptimizing}
                              <div class="laser-scanner"></div>
                          {/if}
                          
                          <!-- 1. Code Editor Line Numbers Column (Pro touch) -->
                          <div 
                              bind:this={lineNumContainer}
                              class="w-12 border-r border-white/5 bg-[#0a0a0a]/50 text-right pr-3 pl-1 py-4 font-mono text-[11px] leading-relaxed text-zinc-700/80 select-none overflow-hidden"
                          >
                              {#each lineNumbers as num}
                                  <div class="h-5">{num}</div>
                                  {/each}
                          </div>

                          <!-- 2. Textarea Editor (Unified Text Output) -->
                          <textarea 
                              id="answer_area"
                              bind:this={answerTextarea}
                              bind:value={kb.editingItem.answer}
                              onscroll={syncScroll}
                              placeholder="NỘI DUNG VĂN BẢN TRẦN (RAW TEXT):
- Nhập/soạn thảo nội dung tri thức trực tiếp tại đây...
- Hoặc nếu nạp từ Link/File bên cột trái, hãy bấm nút 'BÓC TÁCH' để văn bản bóc tách được đổ thẳng vào đây.
- Hãy đọc nội dung text thuần trên và hiệu chỉnh thoải mái trước khi bấm Lưu."
                              class="flex-1 bg-transparent px-4 py-4 text-xs font-mono font-medium leading-relaxed text-cyan-50/90 placeholder:text-white/20 focus:outline-none transition-all resize-none overflow-y-auto custom-scrollbar whitespace-pre-wrap select-text h-full"
                          ></textarea>

                      </div>

                      <!-- Editor Statusbar -->
                      <div class="h-7 border-t border-white/5 bg-[#0a0a0a]/80 px-4 flex items-center justify-between text-[9px] font-mono text-cyan-500/30">
                          <div>STATUS: <strong class="text-green-500/80">READY_FOR_SYNC</strong></div>
                          <div>RAW TEXT ONLY</div>
                      </div>
                  </div>
                  
                  <!-- Tip indicator for External Sources -->
                  {#if kb.editingItem.source_type && kb.editingItem.source_type !== 'TEXT'}
                      <div class="mt-2.5 p-3 rounded-xl bg-cyan-500/5 border border-cyan-500/10 text-[10px] text-cyan-400/80 leading-relaxed font-mono flex items-start gap-2">
                          <Zap size={12} class="flex-shrink-0 text-yellow-400 mt-0.5 fill-yellow-400 animate-pulse" />
                          <div>
                              <strong>⚡ LUỒNG XỬ LÝ HỢP NHẤT:</strong> Hãy bấm nút <strong class="text-cyan-300 font-black">BÓC TÁC NGUỒN</strong> bên cột trái để tự động đưa toàn bộ dữ liệu (link/file) về dạng text trần hiển thị ở ô soạn thảo trên. Sếp chỉ việc đọc, rà soát lại và hiệu chỉnh trực tiếp trên văn bản rồi bấm lưu!
                          </div>
                      </div>
                  {/if}
              </div>

          </div>

          <!-- Bottom Decorative Blur -->
          <div class="absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t from-[#020202] to-transparent pointer-events-none z-10"></div>
      </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(34, 211, 238, 0.1); border-radius: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(34, 211, 238, 0.3); }

  @keyframes scan {
      0% { transform: translateY(-100%); }
      100% { transform: translateY(100%); }
  }
  .laser-scanner {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      pointer-events: none;
      background: linear-gradient(to bottom, transparent, rgba(236, 72, 153, 0.05) 40%, rgba(236, 72, 153, 0.35) 50%, rgba(236, 72, 153, 0.05) 60%, transparent);
      background-size: 100% 100px;
      animation: scan 2s linear infinite;
      z-index: 10;
      box-shadow: inset 0 0 20px rgba(236, 72, 153, 0.1);
  }
</style>
