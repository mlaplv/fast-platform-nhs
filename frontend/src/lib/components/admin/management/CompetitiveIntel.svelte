<script lang="ts">
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import type { VideoScript } from "$lib/types";

  interface Props {
    activeScript: VideoScript;
  }

  let { activeScript }: Props = $props();
</script>

<!-- Competitive Intelligence Panel -->
<div class="border border-yellow-500/20 bg-yellow-950/5 rounded-xl p-5 relative overflow-hidden group">
  <div class="absolute -right-10 -bottom-10 w-32 h-32 bg-yellow-500/5 rounded-full blur-2xl group-hover:bg-yellow-500/10 transition-all duration-500"></div>
  
  <div class="flex items-center gap-2 border-b border-gray-900/60 pb-3 mb-4">
    <Sparkles class="w-4 h-4 text-yellow-400" />
    <span class="text-[10px] font-mono font-bold tracking-widest text-yellow-400 uppercase">COMPETITIVE RESEARCH & INTEL</span>
  </div>
  
  <div class="space-y-4">
    <div class="bg-[#0b0c10]/40 border border-gray-900 p-4 rounded-lg">
      <span class="text-[9px] font-mono text-cyan-400/80 uppercase tracking-wider font-bold block mb-1">🎯 Core Message / Angle:</span>
      <p class="text-xs text-cyan-100 font-medium leading-relaxed font-sans">
        {activeScript.structured_script?.competitor_analysis?.core_message || "(Chưa phân tích)"}
      </p>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Competitor Weaknesses -->
      <div class="bg-red-950/10 border border-red-500/10 p-4 rounded-lg space-y-2">
        <span class="text-[9px] font-mono text-red-400/80 uppercase tracking-wider font-bold block">▼ Điểm yếu lớn của đối thủ:</span>
        {#if activeScript.structured_script?.competitor_analysis?.competitor_weaknesses}
          {#if Array.isArray(activeScript.structured_script.competitor_analysis.competitor_weaknesses)}
            <ul class="list-disc list-inside space-y-1 text-[11px] text-red-200/90 leading-relaxed font-sans">
              {#each activeScript.structured_script.competitor_analysis.competitor_weaknesses as weakness}
                <li>{weakness}</li>
              {/each}
            </ul>
          {:else}
            <p class="text-[11px] text-red-200/90 leading-relaxed font-sans">
              {activeScript.structured_script.competitor_analysis.competitor_weaknesses}
            </p>
          {/if}
        {:else}
          <p class="text-[11px] text-red-200/90 leading-relaxed font-sans">(Không phát hiện)</p>
        {/if}
      </div>
      
      <!-- Our Strengths / USP -->
      <div class="bg-emerald-950/10 border border-emerald-500/10 p-4 rounded-lg space-y-2">
        <span class="text-[9px] font-mono text-emerald-400/80 uppercase tracking-wider font-bold block">▲ Điểm mạnh/USP của chúng ta:</span>
        {#if activeScript.structured_script?.competitor_analysis?.our_strengths}
          {#if Array.isArray(activeScript.structured_script.competitor_analysis.our_strengths)}
            <ul class="list-disc list-inside space-y-1 text-[11px] text-emerald-200/90 leading-relaxed font-sans">
              {#each activeScript.structured_script.competitor_analysis.our_strengths as strength}
                <li>{strength}</li>
              {/each}
            </ul>
          {:else}
            <p class="text-[11px] text-emerald-200/90 leading-relaxed font-sans">
              {activeScript.structured_script.competitor_analysis.our_strengths}
            </p>
          {/if}
        {:else}
          <p class="text-[11px] text-emerald-200/90 leading-relaxed font-sans">(Chưa có USP)</p>
        {/if}
      </div>
    </div>
  </div>
</div>
