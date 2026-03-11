<script lang="ts">
  import { onMount } from "svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { fade, fly } from "svelte/transition";
  import Megaphone from "lucide-svelte/icons/megaphone";
  import PlusCircle from "lucide-svelte/icons/plus-circle";
  import Loader2 from "lucide-svelte/icons/loader-2";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import RotateCcw from "lucide-svelte/icons/rotate-ccw";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Image from "lucide-svelte/icons/image";
  import FileText from "lucide-svelte/icons/file-text";
  import ShieldCheck from "lucide-svelte/icons/shield-check";

  let campaigns: any[] = $state([]);
  let isLoading = $state(true);
  let deletingId = $state<string | null>(null);

  // Step labels for display
  const STEP_LABELS: Record<number, { label: string; icon: any }> = {
    1: { label: "Phân tích từ khóa", icon: Sparkles },
    2: { label: "Săn ảnh", icon: Image },
    3: { label: "Lập dàn ý", icon: FileText },
    4: { label: "Soạn bản thảo", icon: FileText },
    5: { label: "Kiểm tra đạo văn", icon: ShieldCheck },
    6: { label: "Hoàn thiện & Xuất bản", icon: CheckCircle }
  };

  const STATUS_STYLE: Record<string, string> = {
    PROCESSING: "text-amber-400 bg-amber-500/10 border-amber-500/30 animate-pulse",
    WAITING_FOR_REVIEW: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    COMPLETED: "text-green-400 bg-green-500/10 border-green-500/30",
    ERROR: "text-red-400 bg-red-500/10 border-red-500/30",
    REJECTED: "text-gray-500 bg-gray-500/10 border-gray-500/20"
  };

  const STATUS_LABEL: Record<string, string> = {
    PROCESSING: "Đang xử lý",
    WAITING_FOR_REVIEW: "Chờ duyệt",
    COMPLETED: "Hoàn thành",
    ERROR: "Lỗi",
    REJECTED: "Đã huỷ"
  };

  onMount(async () => {
    await loadCampaigns();
  });

  async function loadCampaigns() {
    isLoading = true;
    try {
      const raw = await apiClient.get<any>("/api/v1/content/campaigns");
      // API might return wrapped or direct array
      campaigns = Array.isArray(raw) ? raw : raw?.data || raw?.items || [];
    } catch (e) {
      console.error("[ContentFactory] Failed to load campaigns:", e);
      campaigns = [];
    } finally {
      isLoading = false;
    }
  }

  async function deleteCampaign(id: string) {
    deletingId = id;
    try {
      await apiClient.delete(`/api/v1/content/campaigns/${id}`);
      campaigns = campaigns.filter(c => c.id !== id);
      nanobot.showToast("Đã xóa chiến dịch thành công", "success");
    } catch (e) {
      nanobot.showToast("Không thể xóa chiến dịch", "error");
    } finally {
      deletingId = null;
    }
  }

  function resumeCampaign(campaign: any) {
    // Resume via VUI voice command — triggers orchestrator resume logic
    nanobot.closeUniversalModal();
    nanobot.processCommand(`tiếp tục chiến dịch ${campaign.topic_data?.title || ""}`, "text");
  }

  function handleCreateCampaign() {
    nanobot.processCommand("tạo tin tức", "text");
    nanobot.closeUniversalModal();
  }
</script>

<div class="w-full h-full flex flex-col pt-2 gap-4" in:fade={{ duration: 200 }}>
  <!-- Header -->
  <div class="flex items-center justify-between px-1">
    <h3 class="text-[11px] font-black uppercase tracking-[0.2em] text-white/40">Chiến Dịch Nội Dung</h3>
    <div class="flex items-center gap-2">
      <button
        onclick={loadCampaigns}
        class="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/30 hover:text-white border border-white/5 transition-all"
        title="Làm mới"
      >
        <RotateCcw size={12} class={isLoading ? "animate-spin" : ""} />
      </button>
      <button
        onclick={handleCreateCampaign}
        class="flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-xs font-bold rounded-lg border border-blue-500/30 transition-all"
      >
        <PlusCircle size={12} />
        Tạo mới
      </button>
    </div>
  </div>

  <!-- Content Area -->
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center text-white/20 gap-3">
      <Loader2 class="w-6 h-6 animate-spin" />
      <p class="text-xs font-mono tracking-wider">Đang tải...</p>
    </div>

  {:else if campaigns.length === 0}
    <!-- Empty State -->
    <div
      class="flex-1 flex flex-col items-center justify-center p-8 text-center border border-dashed border-white/10 rounded-2xl bg-black/20"
      in:fade={{ duration: 300 }}
    >
      <div class="w-14 h-14 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-5 border border-blue-500/20">
        <Megaphone class="w-7 h-7 text-blue-400" />
      </div>
      <h3 class="text-base font-bold text-white/80 mb-1">Chưa có Chiến dịch nào</h3>
      <p class="text-white/30 text-xs max-w-xs mx-auto mb-6 leading-relaxed">
        Tạo chiến dịch mới để AI Xohi bắt đầu lên ý tưởng, viết bài và phân phối nội dung.
      </p>
      <button
        onclick={handleCreateCampaign}
        class="group relative px-5 py-2.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-bold text-xs rounded-xl border border-blue-500/30 transition-all flex items-center gap-2"
      >
        <PlusCircle size={14} />
        Tạo Chiến Dịch Đầu Tiên
      </button>
    </div>

  {:else}
    <!-- Campaign List -->
    <div class="flex-1 flex flex-col gap-3 overflow-y-auto pr-1">
      {#each campaigns as campaign, i (campaign.id)}
        {@const step = campaign.current_step || 1}
        {@const stepInfo = STEP_LABELS[step]}
        {@const statusStyle = STATUS_STYLE[campaign.status] || "text-gray-400 bg-gray-500/10 border-gray-500/20"}
        {@const statusLabel = STATUS_LABEL[campaign.status] || campaign.status}
        {@const isAction = campaign.status === "WAITING_FOR_REVIEW" || campaign.status === "PROCESSING"}
        <div
          class="group relative p-4 rounded-2xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 hover:border-white/10 transition-all duration-300"
          in:fly={{ y: 10, duration: 250, delay: i * 40 }}
        >
          <div class="flex items-start justify-between gap-3">
            <!-- Left: info -->
            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold text-white/90 truncate">
                {campaign.topic_data?.title || campaign.source_input || "Chiến dịch không tên"}
              </p>
              <div class="flex items-center gap-2 mt-1.5 flex-wrap">
                <!-- Step badge -->
                <span class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-[10px] font-semibold text-white/50">
                  <svelte:component this={stepInfo?.icon} size={9} />
                  Bước {step} — {stepInfo?.label || "Đang xử lý"}
                </span>
                <!-- Status badge -->
                <span class="px-2 py-0.5 rounded-full border text-[10px] font-bold {statusStyle}">
                  {statusLabel}
                </span>
              </div>
            </div>

            <!-- Right: actions -->
            <div class="flex items-center gap-1 shrink-0">
              {#if isAction}
                <button
                  onclick={() => resumeCampaign(campaign)}
                  class="px-3 py-1.5 rounded-lg bg-blue-500/15 hover:bg-blue-500/25 text-blue-400 border border-blue-500/30 text-[11px] font-bold transition-all"
                >
                  Tiếp tục
                </button>
              {/if}
              <button
                onclick={() => deleteCampaign(campaign.id)}
                disabled={deletingId === campaign.id}
                class="p-1.5 rounded-lg bg-white/5 hover:bg-red-500/15 text-white/20 hover:text-red-400 border border-white/5 hover:border-red-500/30 transition-all opacity-0 group-hover:opacity-100"
                title="Xóa chiến dịch"
              >
                {#if deletingId === campaign.id}
                  <Loader2 size={12} class="animate-spin" />
                {:else}
                  <Trash2 size={12} />
                {/if}
              </button>
            </div>
          </div>

          <!-- Progress bar for PROCESSING -->
          {#if campaign.status === "PROCESSING"}
            <div class="mt-3 h-0.5 bg-white/5 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full"
                style="width: {Math.round((step / 6) * 100)}%; transition: width 1s ease"
              ></div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
