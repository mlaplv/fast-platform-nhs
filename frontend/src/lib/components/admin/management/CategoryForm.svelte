<script lang="ts">
  import { fly, fade, slide } from "svelte/transition";
  import { onMount } from "svelte";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import X from "@lucide/svelte/icons/x";
  import Globe from "@lucide/svelte/icons/globe";
  import FileText from "@lucide/svelte/icons/file-text";
  import ImageIcon from "@lucide/svelte/icons/image";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import MessageCircleQuestion from "@lucide/svelte/icons/message-circle-question";
  import TiptapEditor from "../ui/tiptap/TiptapEditor.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();

  let {
    editingId,
    formParentId,
    formName = $bindable(),
    formSlug = $bindable(),
    formDescription = $bindable(),
    formSeoTitle = $bindable(),
    formSeoDescription = $bindable(),
    formImage = $bindable(),
    formIcon = $bindable(),
    formShowOnMobile = $bindable(),
    formShowOnDesktop = $bindable(),
    formFaqs = $bindable(),
    onSave,
    onClose,
    generateSlug,
  } = $props<{
    editingId: string | null;
    formParentId: string | null;
    formName: string;
    formSlug: string;
    formDescription: string;
    formSeoTitle: string;
    formSeoDescription: string;
    formImage: string;
    formIcon: string;
    formShowOnMobile: boolean;
    formShowOnDesktop: boolean;
    formFaqs: { question: string; answer: string }[];
    onSave: () => void;
    onClose: () => void;
    generateSlug: (name: string) => string;
  }>();

  onMount(() => {
    if (formName === undefined) formName = "";
    if (formSlug === undefined) formSlug = "";
    if (formDescription === undefined) formDescription = "";
    if (formSeoTitle === undefined) formSeoTitle = "";
    if (formSeoDescription === undefined) formSeoDescription = "";
    if (formImage === undefined) formImage = "";
    if (formIcon === undefined) formIcon = "";
    if (formShowOnMobile === undefined) formShowOnMobile = true;
    if (formShowOnDesktop === undefined) formShowOnDesktop = true;
    if (formFaqs === undefined) formFaqs = [];
  });

  let activeTab = $state("general");
  let isSuggestingSeo = $state(false);
  let isSuggestingFaqs = $state(false);

  async function suggestSeo() {
    if (!formName.trim()) {
      nanobot.showToast("Cần nhập tên danh mục để gợi ý SEO", "warning");
      return;
    }
    isSuggestingSeo = true;
    try {
      const res = await apiClient.post<Record<string, string>>("/api/v1/categories/seo-suggest", {
        name: formName,
        description: formDescription
      });
      if (res.title) formSeoTitle = res.title;
      if (res.description) formSeoDescription = res.description;
      nanobot.showToast("Đã gợi ý SEO thành công", "success");
    } catch (e) {
      console.error("SEO suggest failed:", e);
      nanobot.showToast("Gợi ý SEO thất bại", "error");
    } finally {
      isSuggestingSeo = false;
    }
  }

  async function suggestFaqs() {
    if (!formName.trim()) {
      nanobot.showToast("Cần nhập tên danh mục để gợi ý FAQ", "warning");
      return;
    }
    isSuggestingFaqs = true;
    try {
      const res = await apiClient.post<{ question: string; answer: string }[]>("/api/v1/categories/faq-suggest", {
        name: formName,
        description: formDescription
      });
      if (res && res.length > 0) {
        formFaqs = [...formFaqs, ...res];
        nanobot.showToast(`Đã gợi ý ${res.length} câu hỏi FAQ`, "success");
      }
    } catch (e) {
      console.error("FAQ suggest failed:", e);
      nanobot.showToast("Gợi ý FAQ thất bại", "error");
    } finally {
      isSuggestingFaqs = false;
    }
  }

  function addFaq() {
    formFaqs = [...formFaqs, { question: "", answer: "" }];
  }

  function removeFaq(index: number) {
    formFaqs = formFaqs.filter((_, i) => i !== index);
  }
</script>

<div use:portal>
  <!-- Master Backdrop -->
  <div
    class="fixed inset-0 bg-[#050505]/80 backdrop-blur-sm transition-all"
    style="z-index: {Z_INDEX_ADMIN.OVERLAY};"
    transition:fade={{ duration: 300 }}
    onclick={onClose}
    aria-label="Close panel"
    role="button"
    tabindex="0"
    onkeydown={(e) => e.key === "Escape" && onClose()}
  ></div>

  <!-- THE MASTER DRAWER -->
  <div
    class="fixed top-0 right-0 h-full w-full max-w-3xl bg-[#050505] border-l border-white/10 flex flex-col shadow-[-50px_0_100px_rgba(0,0,0,0.9)] overflow-hidden"
    style="z-index: {Z_INDEX_ADMIN.MODAL + 10};"
    transition:fly={{ x: 600, duration: 400, opacity: 1 }}
  >
    <!-- Ambient Background Effect -->
    <div class="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#00FFFF]/50 to-transparent opacity-30"></div>
    <div class="absolute -top-24 -right-24 w-48 h-48 bg-[#00FFFF]/5 blur-[100px] rounded-full"></div>

    <!-- Header -->
    <div class="flex items-center justify-between border-b border-white/10 px-8 py-5 bg-white/[0.02]">
      <div class="flex flex-col gap-1">
        <div class="text-[10px] font-bold text-[#00FFFF] tracking-[0.3em] flex items-center gap-2">
          <div class="w-1.5 h-1.5 rounded-full bg-[#00FFFF] animate-pulse"></div>
          {editingId ? "Modify Taxonomy Node" : "Initialize Taxonomy Node"}
        </div>
        {#if formParentId}
          <div class="text-gray-500 font-mono text-[9px] tracking-wider">
            Inheriting from parent scope: <span class="text-[#00FFFF]/60">{formParentId}</span>
          </div>
        {/if}
      </div>

      <div class="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/10">
        <button 
          onclick={() => activeTab = "general"}
          class="px-4 py-1.5 text-[10px] font-bold tracking-widest rounded-lg transition-all {activeTab === 'general' ? 'bg-[#00FFFF]/20 text-[#00FFFF]' : 'text-gray-500 hover:text-gray-300'}"
        >General</button>
        <button 
          onclick={() => activeTab = "seo"}
          class="px-4 py-1.5 text-[10px] font-bold tracking-widest rounded-lg transition-all {activeTab === 'seo' ? 'bg-[#00FFFF]/20 text-[#00FFFF]' : 'text-gray-500 hover:text-gray-300'}"
        >SEO_Engine</button>
        <button 
          onclick={() => activeTab = "faqs"}
          class="px-4 py-1.5 text-[10px] font-bold tracking-widest rounded-lg transition-all {activeTab === 'faqs' ? 'bg-orange-500/20 text-orange-400' : 'text-gray-500 hover:text-gray-300'}"
        >FAQs_Schema</button>
      </div>
    </div>

    <!-- Scrollable Body -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-8">
      <div class="flex flex-col gap-8">
        {#if activeTab === "general"}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-8" transition:fade>
            <!-- Name & Slug -->
            <div class="flex flex-col gap-6">
              <div class="flex flex-col gap-2">
                <label class="text-[9px] font-bold text-gray-500 tracking-widest ml-1">Name_Identifier</label>
                <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-2xl transition-all shadow-inner">
                  <input
                    bind:value={formName}
                    oninput={() => { if (!editingId) formSlug = generateSlug(formName); }}
                    placeholder="Enter category name..."
                    class="w-full bg-transparent py-3.5 px-5 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none"
                  />
                </div>
              </div>

              <div class="flex flex-col gap-2">
                <label class="text-[9px] font-bold text-gray-500 tracking-widest ml-1">Slug_Reference</label>
                <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-2xl transition-all shadow-inner">
                  <div class="absolute left-4 top-1/2 -translate-y-1/2 text-[10px] text-[#00FFFF]/40 font-mono">/</div>
                  <input
                    bind:value={formSlug}
                    placeholder="slug-path..."
                    class="w-full bg-transparent py-3.5 pl-8 pr-5 text-sm text-[#00FFFF] font-mono placeholder:text-gray-700 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <!-- Image & Icon -->
            <div class="flex flex-col gap-6">
              <div class="flex items-center gap-4">
                <div class="flex-1 flex flex-col gap-2">
                  <label class="text-[9px] font-bold text-gray-500 tracking-widest ml-1 flex items-center gap-2">
                    <ImageIcon size={10} /> Banner_Asset_URL
                  </label>
                  <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-2xl transition-all shadow-inner">
                    <input
                      bind:value={formImage}
                      placeholder="https://assets.xohi.io/banners/..."
                      class="w-full bg-transparent py-3.5 px-5 text-xs text-gray-400 font-mono placeholder:text-gray-700 focus:outline-none"
                    />
                  </div>
                </div>
                <div class="w-16 h-16 rounded-2xl bg-white/[0.02] border border-white/5 overflow-hidden flex items-center justify-center shrink-0 shadow-2xl">
                  {#if formImage}
                    <img src={formImage} alt="Preview" class="w-full h-full object-cover" />
                  {:else}
                    <ImageIcon size={20} class="text-gray-800" />
                  {/if}
                </div>
              </div>

              <div class="flex flex-col gap-2">
                <label class="text-[9px] font-bold text-gray-500 tracking-widest ml-1 flex items-center gap-2">
                  <span>🖼️</span> Icon_Emoji_SVG
                </label>
                <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-[#00FFFF]/40 rounded-2xl transition-all shadow-inner">
                  <input
                    bind:value={formIcon}
                    placeholder="💧 or /assets/icons/..."
                    class="w-full bg-transparent py-3.5 px-5 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <!-- Visual Gate Controls -->
            <div class="md:col-span-2">
              <div class="p-4 bg-white/5 border border-white/10 rounded-2xl">
                <label class="text-[9px] font-bold text-[#00FFFF] tracking-widest flex items-center gap-2 mb-4">
                  Display_Gate_Control
                </label>
                <div class="flex gap-4">
                  <label class="flex-1 flex items-center justify-between p-3 bg-black/20 border border-white/5 rounded-xl cursor-pointer group hover:border-[#00FFFF]/20 transition-all">
                    <span class="text-xs text-gray-400 group-hover:text-white transition-colors tracking-tighter">Show on Mobile</span>
                    <input type="checkbox" bind:checked={formShowOnMobile} class="hidden" />
                    <div class="w-10 h-5 rounded-full relative transition-colors {formShowOnMobile ? 'bg-[#00FFFF]/40' : 'bg-gray-800'}">
                        <div class="absolute top-1 left-1 w-3 h-3 rounded-full bg-white transition-all {formShowOnMobile ? 'translate-x-5' : ''}"></div>
                    </div>
                  </label>
                  <label class="flex-1 flex items-center justify-between p-3 bg-black/20 border border-white/5 rounded-xl cursor-pointer group hover:border-[#00FFFF]/20 transition-all">
                    <span class="text-xs text-gray-400 group-hover:text-white transition-colors tracking-tighter">Show on Desktop</span>
                    <input type="checkbox" bind:checked={formShowOnDesktop} class="hidden" />
                    <div class="w-10 h-5 rounded-full relative transition-colors {formShowOnDesktop ? 'bg-[#00FFFF]/40' : 'bg-gray-800'}">
                        <div class="absolute top-1 left-1 w-3 h-3 rounded-full bg-white transition-all {formShowOnDesktop ? 'translate-x-5' : ''}"></div>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <!-- Description -->
            <div class="md:col-span-2 flex flex-col gap-2">
              <label class="text-[9px] font-bold text-gray-500 tracking-widest ml-1 flex items-center gap-2">
                <FileText size={10} /> Rich_Description
              </label>
              <div class="min-h-[300px] rounded-2xl overflow-hidden border border-white/5 focus-within:border-[#00FFFF]/20 transition-all bg-black/40">
                <TiptapEditor 
                  bind:content={formDescription}
                  editable={true}
                  placeholder="Describe this category..."
                />
              </div>
            </div>
          </div>
        {/if}

        {#if activeTab === "seo"}
          <div class="flex flex-col gap-6" transition:fade>
            <div class="flex items-center justify-between">
              <label class="text-[9px] font-bold text-gray-500 tracking-widest ml-1 flex items-center gap-2 text-blue-400">
                <Globe size={10} /> Meta_Title_Override
              </label>
              <button 
                onclick={suggestSeo}
                disabled={isSuggestingSeo}
                class="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 rounded-lg text-[9px] font-bold text-blue-400 tracking-widest hover:bg-blue-500/20 disabled:opacity-50 transition-all"
              >
                <Sparkles size={10} class={isSuggestingSeo ? "animate-spin" : ""} />
                {isSuggestingSeo ? "Analysing..." : "AI_Suggest"}
              </button>
            </div>
            <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-blue-500/40 rounded-2xl transition-all shadow-inner">
              <input
                bind:value={formSeoTitle}
                placeholder={formName || "Meta title..."}
                class="w-full bg-transparent py-3.5 px-5 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none"
              />
              <div class="absolute right-4 top-1/2 -translate-y-1/2 text-[9px] font-mono text-gray-600">{(formSeoTitle || "").length}/60</div>
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-[9px] font-bold text-gray-500 tracking-widest ml-1 flex items-center gap-2 text-purple-400">
                Meta_Description_Snippet
              </label>
              <div class="relative group bg-black/40 border border-white/5 hover:border-white/10 focus-within:border-purple-500/40 rounded-2xl transition-all shadow-inner">
                <textarea
                  bind:value={formSeoDescription}
                  placeholder="Brief summary for Google results..."
                  rows="4"
                  class="w-full bg-transparent py-3.5 px-5 text-sm text-gray-100 placeholder:text-gray-700 focus:outline-none resize-none"
                ></textarea>
                <div class="absolute right-4 bottom-3 text-[9px] font-mono text-gray-600">{(formSeoDescription || "").length}/160</div>
              </div>
            </div>

            <div class="p-6 bg-blue-500/[0.02] border border-blue-500/10 rounded-3xl flex items-start gap-4">
              <div class="p-3 bg-blue-500/10 rounded-xl">
                <Globe size={18} class="text-blue-500" />
              </div>
              <div class="flex flex-col gap-1">
                <span class="text-[10px] font-bold text-blue-500 tracking-widest">SEO Optimization Engine</span>
                <p class="text-[9px] text-gray-600 leading-relaxed tracking-tighter">AI will analyze your category name and description to generate optimal meta tags for search engine visibility.</p>
              </div>
            </div>
          </div>
        {/if}

        {#if activeTab === "faqs"}
          <div class="flex flex-col gap-6" transition:fade>
            <div class="flex items-center justify-between bg-white/5 border border-white/10 p-5 rounded-2xl">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center border border-orange-500/30">
                  <MessageCircleQuestion size={20} class="text-orange-400" />
                </div>
                <div class="flex flex-col">
                  <span class="text-xs font-black text-white tracking-widest">FAQ_Schema_Core</span>
                  <span class="text-[9px] text-gray-500 tracking-wider">AI-Powered Structured Data Generation</span>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button 
                  onclick={suggestFaqs}
                  disabled={isSuggestingFaqs}
                  class="flex items-center gap-2 px-4 py-2 bg-orange-500/20 border border-orange-500/30 rounded-xl text-[10px] font-bold text-orange-400 tracking-widest hover:bg-orange-500/30 disabled:opacity-50 transition-all"
                >
                  <Sparkles size={12} class={isSuggestingFaqs ? "animate-spin" : ""} />
                  {isSuggestingFaqs ? "Synthesizing..." : "AI_Suggest"}
                </button>
                <button 
                  onclick={addFaq}
                  class="p-2 bg-white/5 border border-white/10 rounded-xl text-gray-400 hover:text-[#00FFFF] hover:border-[#00FFFF]/30 transition-all"
                >
                  <Plus size={18} />
                </button>
              </div>
            </div>

            <div class="flex flex-col gap-4">
              {#each formFaqs as faq, i}
                <div 
                  class="group relative bg-white/[0.02] border border-white/5 hover:border-white/10 rounded-2xl p-6 transition-all"
                  transition:slide
                >
                  <div class="flex flex-col gap-4">
                    <div class="relative">
                      <div class="absolute -left-2 top-0 bottom-0 w-1 bg-orange-500/30 rounded-full"></div>
                      <input 
                        bind:value={faq.question}
                        placeholder="Enter FAQ Question..."
                        class="w-full bg-transparent border-none text-sm font-bold text-white placeholder:text-gray-700 focus:outline-none"
                      />
                    </div>
                    <textarea 
                      bind:value={faq.answer}
                      placeholder="Enter FAQ Answer..."
                      rows="2"
                      class="w-full bg-black/20 border border-white/5 rounded-xl p-3 text-[11px] text-gray-400 placeholder:text-gray-700 focus:outline-none focus:border-[#00FFFF]/20 transition-all resize-none"
                    ></textarea>
                  </div>
                  <button 
                    onclick={() => removeFaq(i)}
                    class="absolute top-4 right-4 p-2 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              {/each}
              
              {#if formFaqs.length === 0}
                <div class="py-16 border-2 border-dashed border-white/5 rounded-3xl flex flex-col items-center justify-center gap-3">
                  <MessageCircleQuestion size={32} class="text-gray-800" />
                  <span class="text-[10px] font-bold text-gray-600 tracking-[0.2em]">No questions mapped to this node</span>
                  <button 
                    onclick={addFaq}
                    class="text-[9px] font-black text-orange-500/60 tracking-widest hover:text-white transition-colors"
                  >Initialize_FAQ_Store</button>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-end gap-3 px-8 py-6 border-t border-white/10 bg-black/40">
      <button
        onclick={onClose}
        class="px-6 py-3 text-gray-500 hover:text-white text-[10px] font-bold tracking-widest transition-all"
      >Abort_Changes</button>
      <button
        onclick={onSave}
        class="px-10 py-3 bg-[#00FFFF] text-black rounded-xl text-[10px] font-black tracking-[0.2em] hover:shadow-[0_0_30px_rgba(0,255,255,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-300"
      >
        {editingId ? "Sync_Node_State" : "Deploy_Taxonomy"}
      </button>
    </div>
  </div>
</div>

<style>
  :global(.tiptap-shell) {
    @apply border-none !bg-transparent;
  }
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
  }
</style>
