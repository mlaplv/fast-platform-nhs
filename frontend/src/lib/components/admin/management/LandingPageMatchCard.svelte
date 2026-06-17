<script lang="ts">
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Copy from "@lucide/svelte/icons/copy";
  import Check from "@lucide/svelte/icons/check";
  import FileText from "@lucide/svelte/icons/file-text";
  import type { VideoScript } from "$lib/types";

  interface Props {
    activeScript: VideoScript | null;
  }

  let { activeScript }: Props = $props();

  let copiedIndex = $state<number | null>(null);

  // Derive headlines from the active script structure
  let headlines = $derived(
    activeScript?.structured_script?.landing_page_headlines || []
  );

  async function copyToClipboard(h1: string, h2: string, index: number) {
    try {
      const text = `H1: ${h1}\nH2: ${h2}`;
      await navigator.clipboard.writeText(text);
      copiedIndex = index;
      setTimeout(() => {
        copiedIndex = null;
      }, 2000);
    } catch (err) {
      console.error("Không thể sao chép tự động", err);
    }
  }

  function getBadgeColor(psychology: string) {
    const p = psychology.toLowerCase();
    if (p.includes("sợ") || p.includes("cảnh báo")) {
      return "bg-red-500/10 text-red-400 border-red-500/20";
    }
    if (p.includes("lợi ích") || p.includes("tức thì") || p.includes("nhanh")) {
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    }
    return "bg-purple-500/10 text-purple-400 border-purple-500/20";
  }
</script>

{#if headlines.length > 0}
  <div class="bg-[#08080c] border border-cyan-500/10 rounded-xl p-5 space-y-4 relative overflow-hidden group">
    <!-- Neon blur background -->
    <div class="absolute -left-10 -top-10 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-all duration-500"></div>

    <div class="flex items-center justify-between border-b border-gray-900 pb-3">
      <div class="flex items-center gap-2">
        <Sparkles class="w-4 h-4 text-cyan-400" />
        <span class="text-[10px] font-mono font-bold tracking-widest text-cyan-400 uppercase">LANDING PAGE MESSAGE-MATCH CENTER</span>
      </div>
      <span class="text-[9px] font-mono bg-cyan-950/30 text-cyan-400 px-2 py-0.5 rounded border border-cyan-500/20">CRO BOOSTER</span>
    </div>

    <p class="text-[11px] text-gray-400 leading-relaxed font-sans">
      Tối ưu hóa tỷ lệ chuyển đổi bằng cách đồng bộ tiêu đề trang đích với kịch bản video quảng cáo. Hãy chọn và dán 1 trong các cặp H1 & H2 dưới đây lên dòng đầu tiên của website:
    </p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      {#each headlines as hl, idx}
        <div class="bg-[#0b0c10]/40 border border-gray-850 rounded-lg p-3.5 space-y-3 flex flex-col justify-between hover:border-gray-800 transition-all relative">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-[8px] font-mono px-2 py-0.5 rounded-full border {getBadgeColor(hl.match_psychology)}">
                {hl.match_psychology}
              </span>
              <button
                onclick={() => copyToClipboard(hl.headline, hl.subheadline, idx)}
                class="p-1 text-gray-500 hover:text-white hover:bg-white/5 rounded transition-all"
                title="Sao chép cặp tiêu đề"
              >
                {#if copiedIndex === idx}
                  <Check class="w-3.5 h-3.5 text-emerald-400" />
                {:else}
                  <Copy class="w-3.5 h-3.5" />
                {/if}
              </button>
            </div>

            <div class="space-y-1.5 pt-1">
              <div>
                <span class="text-[9px] font-mono font-bold text-gray-500 block uppercase">Tiêu đề chính (H1)</span>
                <p class="text-xs font-semibold text-white leading-relaxed">{hl.headline}</p>
              </div>
              <div class="pt-1 border-t border-gray-900/50">
                <span class="text-[9px] font-mono font-bold text-gray-500 block uppercase">Tiêu đề phụ (H2)</span>
                <p class="text-[11px] text-gray-400 leading-relaxed">{hl.subheadline}</p>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}
