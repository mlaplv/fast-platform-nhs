<script lang="ts">
  import {
    Check,
    RotateCcw,
    Edit2,
    Save,
    X,
    Sparkles,
    MessageSquare,
    Image as ImageIcon,
    FileText,
    ShieldCheck,
    CheckCircle,
    Maximize2,
    Minimize2,
  } from "lucide-svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { vuiState, vuiController } from "$lib/vui";
  import { fade, slide, scale } from "svelte/transition";
  import { untrack } from "svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";

  let {
    campaign_id,
    step: incomingStep = 1,
    status: incomingStatus = "WAITING_FOR_REVIEW",
    progress_msg: incomingProgressMsg = "",
    title: incomingTitle = "",
    keywords: incomingKeywords = {},
    assets: incomingAssets = [],
    outline: incomingOutline = []
  } = $props();

  // Unified Local Reactive States (Editable by UI or synced from Props)
  // Matching template expectations: 'keywords', 'assets', 'outline'
  let step = $state(untrack(() => incomingStep));
  let status = $state(untrack(() => incomingStatus));
  let progress_msg = $state(untrack(() => incomingProgressMsg));
  
  // keywords is an object like { title: "...", primary_keyword: "...", secondary_keywords: [...] }
  let keywords = $state(untrack(() => incomingKeywords || {}));
  let assets = $state(untrack(() => incomingAssets || []));
  let outline = $state(untrack(() => incomingOutline || []));
  
  // Secondary State for Editing (Deep Copy)
  let editedKeywords = $state(untrack(() => ({ ...incomingKeywords })));
  let isLoading = $state(false);
  let resultMsg = $state("");
  let selectedAssetIndex = $state(0);

  // UI Derived States
  let isEditing = $derived(status === "EDITING");
  let isProcessing = $derived(status === "PROCESSING");
  let isReviewing = $derived(status === "WAITING_FOR_REVIEW");

  // Rule R82.22: Smart Sync Effect — Bridging Props and Local State
  $effect(() => {
    // 1. Step Sync (Anti-Regression Logic)
    // Only accept incoming steps if they are ahead or if we are not in a PROCESSING state
    if (incomingStep > step) {
      if (import.meta.env.DEV) console.log(`[ContentReviewCard] Prop Step Advance: ${step} -> ${incomingStep}`);
      step = incomingStep;
      selectedAssetIndex = 0; // Reset focus on step change
    }

    // 2. Status Sync (Elite Transition Logic)
    if (incomingStatus !== status) {
      // Don't let a stale "WAITING_FOR_REVIEW" from an old step pull us back
      if (incomingStep === step || (incomingStep > step)) {
        if (import.meta.env.DEV) console.log(`[ContentReviewCard] Prop Status Sync: ${status} -> ${incomingStatus}`);
        status = incomingStatus;
        
        if (status === "WAITING_FOR_REVIEW") {
           vuiController.resetToIdle();
           resultMsg = ""; 
        }
      }
    }

    // 3. Metadata & Asset Sync
    // Only refresh local state if we aren't editing, AND if data is actually present.
    if (!isEditing) {
      if (incomingKeywords && Object.keys(incomingKeywords).length > 0) {
        keywords = { ...incomingKeywords };
        // Update editing copy too if it's a fresh step
        if (incomingStep > step || !editedKeywords.title) {
          editedKeywords = { ...incomingKeywords };
        }
      }

      if (incomingAssets && incomingAssets.length > 0) {
        assets = [...incomingAssets];
      }

      if (incomingOutline && incomingOutline.sections?.length > 0) {
        outline = { ...incomingOutline };
      }
    }

    // 4. Progress Message & VUI Phasing
    progress_msg = incomingProgressMsg;
    if (status === "PROCESSING" && vuiState.phase === "executing") {
      vuiState.setLiveText(progress_msg || "AI đang xử lý...");
    }
  });

  async function handleApprove() {
    if (isLoading || status === "PROCESSING") return;
    
    // Rule R81/R82.20: Immediate UI/VUI Lock & Escape from Logs
    isLoading = true;
    status = "PROCESSING";
    vuiController.interruptSpeech();
    vuiState.setIsWaitingForAction(false);
    // If we're inside the log drawer, close it to "escape" to the Orb
    nanobot.closeFullLog();
    
    // Rule R81/R82.20: Capture VUI focus and PREEMPTIVELY show next step processing
    const nextStep = step + 1;
    nanobot.voice.setVoiceResult(
        "Chuyển bước nội dung",
        "Dạ sếp, em đã ghi nhận bản thảo bước " + step + ". Đang khởi tạo bước " + nextStep + " ạ.",
        "CONTENT_CREATE",
        { 
          category: "CONTENT_CREATE",
          campaign_id, 
          step: nextStep, 
          status: "PROCESSING", 
          keywords, // Keep keywords for context
          assets: [], // Clear assets for new hunt
          outline: { title: "", sections: [] }, 
          progress_msg: "Đang yêu cầu duyệt..."
        },
        "voice"
    );

    vuiState.setActive(true);
    vuiState.setPhase("executing");
    vuiState.setLiveText("Đang gửi yêu cầu duyệt...");
    nanobot.startPolling(); 

    try {
      const resp = (await apiClient.post(
        `/api/v1/content/campaigns/${campaign_id}/approve`,
        {
          approved: true,
          step: step,
          edited_data: isEditing ? editedKeywords : null,
        },
      )) as any;
      resultMsg = resp.message || "Sếp đã duyệt. Đang chuyển pha...";

      // 2. Local State Advance
      if (resp.next_step) {
        step = resp.next_step;
      } else {
        step += 1;
      }
      
      // 3. Sync back to nanobot
      if (nanobot.vuiResponse?.data) {
          nanobot.vuiResponse.data.step = step;
          nanobot.vuiResponse.data.progress_msg = resultMsg;
          nanobot.vuiResponse.data.status = "PROCESSING";
          
          nanobot.vuiResponse.data.assets = [];
          nanobot.vuiResponse.data.outline = { title: "", sections: [] };
          
          assets = []; 
          selectedAssetIndex = 0;
          outline = { title: "", sections: [] };
      }
      
    } catch (e) {
      console.error("[ContentReviewCard] Approve failed:", e);
      resultMsg = "Lỗi kết nối hệ thống...";
      status = "WAITING_FOR_REVIEW";
      if (nanobot.vuiResponse?.data) {
          nanobot.vuiResponse.data.status = "WAITING_FOR_REVIEW";
          nanobot.vuiResponse.data.progress_msg = "Lỗi kết nối. Thử lại nhé sếp!";
      }
    } finally {
      isLoading = false;
      vuiState.setIsWaitingForAction(false);
    }
  }

  async function handleRetry() {
    if (isLoading || status === "PROCESSING") return;
    
    isLoading = true;
    status = "PROCESSING";
    vuiController.interruptSpeech();
    nanobot.closeFullLog();

    // Capture VUI focus for CURRENT step (Rule R81/R82.20)
    nanobot.voice.setVoiceResult(
      "Chạy lại bước",
      "Dạ sếp, em đang chạy lại bước " + step + " cho sếp đây.",
      "CONTENT_CREATE",
      { 
        campaign_id, 
        step, 
        status: "PROCESSING", 
        keywords, 
        assets: [], // Clear old assets to show it's retrying
        outline: { title: "", sections: [] },
        progress_msg: "Đang yêu cầu AI thực hiện lại..." 
      },
      "voice"
    );

    vuiState.setActive(true);
    vuiState.setPhase("executing");
    vuiState.setLiveText("Đang yêu cầu AI thực hiện lại...");

    try {
      const resp = (await apiClient.post(
        `/api/v1/content/campaigns/${campaign_id}/retry`,
        {},
      )) as any;
      resultMsg = resp.message || "AI đang thực hiện lại...";
      vuiState.setLiveText(resultMsg);
      
      if (nanobot.vuiResponse?.data) {
          nanobot.vuiResponse.data.status = "PROCESSING";
          nanobot.vuiResponse.data.progress_msg = resultMsg;
      }
      nanobot.startPolling();
    } catch (e) {
      console.error("[ContentReviewCard] Retry failed:", e);
      resultMsg = "Lỗi kết nối hệ thống...";
      status = "WAITING_FOR_REVIEW";
    } finally {
      isLoading = false;
      vuiState.setIsWaitingForAction(false);
    }
  }

  function toggleEdit() {
    if (isEditing) {
      editedKeywords = { ...keywords };
    }
    isEditing = !isEditing;
  }

  function toggleExpand() {
    nanobot.toggleExpand();
  }

  // Handle Escape key to close expanded view
  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape" && nanobot.isExpanded) {
      nanobot.toggleExpand(false);
    }
  }

  // Design 2026: Mouse-tracking Glow (Rule R82.42)
  function handleMouseMove(e: MouseEvent) {
    const target = e.currentTarget as HTMLElement;
    const rect = target.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    target.style.setProperty("--mouse-x", `${x}%`);
    target.style.setProperty("--mouse-y", `${y}%`);
  }
</script>

<svelte:window onkeydown={handleKeyDown} />

<div
  class="content-review-card relative mt-4 rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.3)] overflow-hidden transition-all duration-700 hover:border-blue-500/30 group {nanobot.isExpanded ? 'fixed inset-0 w-screen h-screen z-[100] m-0 rounded-none flex flex-col p-6 md:p-12 backdrop-blur-3xl' : 'p-5'}"
  in:fade={{ duration: 400 }}
>
  <!-- Background Glow -->
  <div
    class="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/10 blur-[80px] rounded-full pointer-events-none group-hover:bg-blue-500/20 transition-all duration-700 {nanobot.isExpanded ? 'w-96 h-96' : ''}"
  ></div>

  <div class="flex items-center justify-between mb-5 relative z-10 {nanobot.isExpanded ? 'mb-8' : ''}">
    <div class="flex items-center gap-3">
      <div
        class="p-2 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/20 shadow-inner"
      >
        {#if step === 1} <Sparkles size={16} />
        {:else if step === 2} <ImageIcon size={16} />
        {:else if step === 3} <FileText size={16} />
        {:else if step === 5} <ShieldCheck size={16} />
        {:else} <CheckCircle size={16} />
        {/if}
      </div>
      <div class="flex flex-col">
        <span class="text-[10px] uppercase font-black tracking-[0.2em] text-blue-400/80">
          Phase {step}
        </span>
        <span class="text-xs font-bold text-white/90">
          {#if step === 1}Keyword Analysis
          {:else if step === 2}Asset Hunting
          {:else if step === 3}Content Outline
          {:else if step === 4}Drafting
          {:else if step === 5}Plagiarism Audit
          {:else}Finalization
          {/if}
        </span>
      </div>

      {#if status === "PROCESSING"}
        <div
          class="ml-2 flex items-center gap-1.5 px-2 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-400 animate-pulse"
        >
          <RotateCcw size={10} class="animate-spin" />
          <span class="font-medium">{progress_msg || "AI is working..."}</span>
        </div>
      {/if}
    </div>

    <div class="flex items-center gap-2">
      <button
        onclick={toggleExpand}
        class="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/40 hover:text-white border border-white/5 transition-all duration-300"
        title={nanobot.isExpanded ? "Collapse View" : "Expand to Neural Fullview"}
      >
        {#if nanobot.isExpanded}
          <Minimize2 size={16} />
        {:else}
          <Maximize2 size={16} />
        {/if}
      </button>

    {#if status === "WAITING_FOR_REVIEW" && step === 1}
      <button
        onclick={toggleEdit}
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white border border-white/5 transition-all duration-300"
      >
        {#if isEditing}
          <X size={14} />
          <span class="text-xs font-semibold">Hủy</span>
        {:else}
          <Edit2 size={14} />
          <span class="text-xs font-semibold">Chỉnh sửa</span>
        {/if}
      </button>
      {/if}
    </div>
  </div>

  <div class="space-y-5 relative z-10 min-h-0 {nanobot.isExpanded ? 'flex-1 overflow-hidden flex flex-col' : ''}">
    <!-- STEP 1: KEYWORDS -->
    {#if step === 1}
      {#if isEditing}
        <div class="space-y-4">
          <div class="group/input">
            <label for="title-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Tiêu đề bài viết</label>
            <div class="relative">
              <MessageSquare size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
              <input
                id="title-{campaign_id}"
                bind:value={editedKeywords.title}
                class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>
          <div class="group/input">
            <label for="primary-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Từ khóa chính</label>
            <div class="relative">
              <Sparkles size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
              <input
                id="primary-{campaign_id}"
                bind:value={editedKeywords.primary_keyword}
                class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>
        </div>
      {:else}
        <div class="space-y-2">
          <h4 class="text-lg font-bold text-white leading-snug tracking-tight">
            {keywords.title || 'Đang phân tích tiêu đề...'}
          </h4>
          <p class="text-[11px] text-white/40 font-medium uppercase tracking-wider">Style: 
            <span class="text-white/70 italic">{keywords.persona || 'Chuyên gia phân tích'}</span>
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          {#if keywords.primary_keyword}
            <span class="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-[11px] font-bold border border-blue-500/30">
              {keywords.primary_keyword}
            </span>
          {:else}
            <span class="px-3 py-1 rounded-full bg-white/5 text-white/20 text-[11px] font-medium border border-white/5 animate-pulse">
              Đang chờ từ khóa...
            </span>
          {/if}
          
          {#each (keywords.secondary_keywords || []) as kw}
            <span class="px-3 py-1 rounded-full bg-white/5 text-white/40 text-[11px] font-medium border border-white/5">{kw}</span>
          {/each}
        </div>
      {/if}

    <!-- STEP 2: ASSET GALLERY (DESIGN 2026 - NEURAL MATRIX) -->
    {:else if step === 2}
      <div class="space-y-4 {nanobot.isExpanded ? 'flex-1 overflow-hidden flex flex-col' : 'min-h-[400px]'}">
        <div class="flex items-center justify-between mb-1">
          <div class="flex items-center gap-3">
             <div class="relative w-4 h-4">
                <div class="absolute inset-0 bg-blue-500/40 blur-[4px] rounded-full animate-pulse"></div>
                <div class="absolute inset-1 bg-blue-400 rounded-full shadow-[0_0_8px_rgba(59,130,246,1)]"></div>
             </div>
             <div class="flex flex-col">
                <span class="text-[9px] text-blue-400/60 font-black tracking-[0.4em] leading-none mb-1 uppercase">Neural Asset Repository</span>
                <span class="text-[11px] text-white font-bold opacity-90 tracking-tight leading-none uppercase">SELECT_MODE://ACTIVE</span>
             </div>
          </div>
          <div class="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/10 backdrop-blur-xl">
             <span class="text-[11px] text-white/50 font-mono">ASSETS: <span class="text-blue-400">{assets.length}</span></span>
          </div>
        </div>

        <!-- Design 2026: Premium Bento Matrix Grid -->
        <div class="relative group/matrix {nanobot.isExpanded ? 'flex-1 overflow-hidden flex flex-col' : ''}">
          <!-- Neural Scanline Overlay -->
          <div class="absolute inset-0 pointer-events-none z-10 opacity-[0.02] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%]"></div>
          
          <div class="{nanobot.isExpanded ? 'flex-1' : 'max-h-[500px]'} overflow-y-auto pr-2 custom-scrollbar space-y-4 min-h-0">
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {#each (assets || []) as url, i}
                <button 
                  onclick={() => {
                    selectedAssetIndex = i;
                    // Rule R82.20: Immediate reaction - speak selection
                    vuiController.speak(`Đã chọn ảnh số ${i+1} ạ.`);
                  }}
                  onmousemove={handleMouseMove}
                  class="group/item relative aspect-[4/3] rounded-2xl overflow-hidden border transition-all duration-500 
                    {selectedAssetIndex === i ? 'border-blue-500 ring-2 ring-blue-500/30 base-shadow-blue' : 'border-white/5 bg-white/[0.02] hover:border-white/20 hover:scale-[1.02]'}
                    {i % 5 === 0 ? 'lg:col-span-2 lg:row-span-2 aspect-square' : ''}"
                  in:scale={{ duration: 500, delay: i * 40, start: 0.95 }}
                >
                  <!-- Asset Image -->
                  <img 
                    src={url} 
                    alt="Asset {i}" 
                    class="w-full h-full object-cover transition-all duration-1000 group-hover/item:scale-110 {selectedAssetIndex === i ? 'brightness-110' : 'brightness-75 group-hover/item:brightness-100'}"
                    onerror={(e) => (e.currentTarget.src = 'https://picsum.photos/seed/' + i + '/800/600')}
                  />
                  
                  <!-- Smart Selection Glow -->
                  <div class="absolute inset-0 transition-opacity duration-500 {selectedAssetIndex === i ? 'opacity-100' : 'opacity-0 group-hover/item:opacity-100'} bg-gradient-to-t from-black/80 via-transparent to-transparent">
                    <div class="absolute bottom-3 left-3 flex items-center gap-2">
                       <div class="p-1.5 rounded-full {selectedAssetIndex === i ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]' : 'bg-black/40 backdrop-blur-md'} border border-white/20 transition-all duration-500">
                          <Check size={12} class="text-white" />
                       </div>
                       <span class="text-[9px] font-black text-white uppercase tracking-widest">{selectedAssetIndex === i ? 'Selected' : 'Click to select'}</span>
                    </div>
                  </div>

                  {#if selectedAssetIndex === i}
                    <!-- Reactive Ripple Frame -->
                    <div class="absolute inset-0 border-2 border-blue-400/50 rounded-2xl animate-pulse pointer-events-none"></div>
                  {/if}
                  
                  <!-- Dynamic Mouse Trace -->
                  <div class="absolute inset-0 opacity-0 group-hover/item:opacity-100 transition-opacity duration-300 pointer-events-none bg-[radial-gradient(circle_at_var(--mouse-x,50%)_var(--mouse-y,50%),rgba(59,130,246,0.15)_0%,transparent_50%)]"></div>
                </button>
              {/each}
            </div>
          </div>
        </div>
      </div>

    <!-- STEP 3: OUTLINE (DESIGN 2026) -->
    {:else if step === 3}
      <div class="space-y-4 {nanobot.isExpanded ? 'flex-1 overflow-hidden flex flex-col' : ''}">
        <div class="flex items-center gap-3">
           <div class="w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
           <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-blue-400">{outline?.title || "Neural Script Outline"}</h5>
        </div>
        <div class="grid grid-cols-1 gap-2.5 {nanobot.isExpanded ? 'flex-1 overflow-y-auto pr-2 custom-scrollbar' : ''}">
          {#each (outline?.sections || []) as section, i}
            <div 
              class="flex items-center gap-4 p-3 rounded-2xl bg-white/[0.02] border border-white/5 transition-all hover:bg-white/5 hover:translate-x-1"
              in:fade={{ duration: 400, delay: i * 50 }}
            >
              <span class="text-[10px] font-mono text-blue-500/40">{i+1 < 10 ? '0' : ''}{i+1}</span>
              <span class="text-xs text-white/80 leading-relaxed font-semibold tracking-tight">{section}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>

  {#if resultMsg}
    <div
      class="mt-6 flex items-start gap-3 p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-300 transition-all backdrop-blur-md"
      transition:scale={{ start: 0.95, duration: 300 }}
    >
      <div class="mt-0.5 p-1.5 rounded-full bg-blue-500/20 shadow-lg"><Check size={14} strokeWidth={3} /></div>
      <p class="text-[13px] font-bold leading-relaxed">{resultMsg}</p>
    </div>
  {/if}

  {#if status === "WAITING_FOR_REVIEW"}
    <div class="flex gap-4 mt-auto pt-6 relative z-10 border-t border-white/5">
      <button
        onclick={handleApprove}
        disabled={isLoading}
        class="group/btn-primary flex-[2] relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-black text-xs uppercase tracking-widest transition-all shadow-[0_15px_30px_-10px_rgba(37,99,235,0.4)] disabled:opacity-50 active:scale-95"
      >
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn-primary:animate-shimmer pointer-events-none"></div>
        {#if isLoading} <RotateCcw size={18} class="animate-spin" />
        {:else} <Check size={18} strokeWidth={3} />
          <span>{isEditing ? "Finalize & Transmit" : "Approve & Execute"}</span>
        {/if}
      </button>

      <button
        onclick={handleRetry}
        disabled={isLoading}
        class="flex items-center justify-center px-6 rounded-2xl bg-white/5 hover:bg-white/10 text-white/40 border border-white/10 transition-all hover:text-white/80 disabled:opacity-50 active:scale-90"
        title="Neural Signal Regen"
      >
        <RotateCcw size={20} class={isLoading ? "animate-spin" : ""} />
      </button>
    </div>
  {/if}
</div>

<style>
  .content-review-card {
    position: relative;
    isolation: isolate;
  }

  /* 2026 Nano-Scrollbar */
  .custom-scrollbar::-webkit-scrollbar {
    width: 3px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.1);
    border-radius: 20px;
    transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(59, 130, 246, 0.6);
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
  }

  /* Shimmer Animation 2026 */
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  :global(.animate-shimmer) {
    position: relative;
    overflow: hidden;
  }
  :global(.animate-shimmer::after) {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    animation: shimmer 1.5s infinite linear;
  }

  /* Matrix Layout Flow */
  :global(.grid-flow-dense) {
    grid-auto-flow: dense;
  }

  .base-shadow-blue {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.4), 0 0 40px rgba(59, 130, 246, 0.2);
  }
</style>
