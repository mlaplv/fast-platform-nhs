<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade, fly, scale } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Terminal from "lucide-svelte/icons/terminal";
  import Cpu from "lucide-svelte/icons/cpu";
  import Activity from "lucide-svelte/icons/activity";
  import Play from "lucide-svelte/icons/play";

  import MissionControlShell from "./MissionControlShell.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

  let log = $derived(nanobot.expandedLog);
  let visible = $state(false);

  $effect(() => {
    if (log) {
      visible = true;
    } else {
      visible = false;
    }
  });

  function close() {
    visible = false;
    setTimeout(() => nanobot.closeFullLog(), 300);
  }

  function maskSensitiveData(message: string) {
    if (!message) return "";
    let masked = message;

    // API Keys (sk-...)
    masked = masked.replace(/(sk-[a-zA-Z0-9]{12,})/g, "sk-****[REDACTED]****");

    // Generic Sensitive Keys in JSON/KV
    const sensitivePattern =
      /(password|secret|api_key|token|salt|credential|private_key|auth_key)["\s:=]+["']?([^"'\s,}] {4,})["']?/gi;
    masked = masked.replace(sensitivePattern, (match, key) => {
      return `${key}: "****[REDACTED]****"`;
    });

    return masked;
  }

  // Advanced Mission Control Formatter
  function formatContent(text: string) {
    if (!text) return "";
    const maskedText = maskSensitiveData(text);
    return maskedText
      .replace(
        /### (.*)/g,
        '<h3 class="text-neon-cyan font-bold mt-8 mb-3 uppercase tracking-[0.3em] text-xs flex items-center gap-2"><div class="w-1.5 h-1.5 bg-neon-cyan rotate-45"></div> $1</h3>',
      )
      .replace(
        /## (.*)/g,
        '<h2 class="text-white font-bold mt-10 mb-5 border-b border-white/10 pb-3 text-xl uppercase tracking-[0.2em] flex items-center gap-3"><span class="text-neon-cyan/40 text-xs font-mono">/SEC/</span> $1</h2>',
      )
      .replace(
        /\*\*(.*?)\*\*/g,
        '<strong class="text-neon-cyan font-bold px-1 bg-neon-cyan/5 rounded">$1</strong>',
      )
      .replace(
        /^\* (.*)/gm,
        '<div class="flex gap-4 mb-2 group/item"><span class="text-neon-cyan/40 font-mono text-[10px] mt-1 group-hover/item:text-neon-cyan transition-colors">0x_ACK</span><span class="text-gray-300 leading-relaxed">$1</span></div>',
      )
      .replace(/\n\n/g, '<div class="h-6"></div>')
      .replace(/\n/g, " ");
  }
</script>

{#if log && visible}
  <MissionControlShell
    title="Integrated Intelligence Display"
    node="TRINITY_PRIMARY"
    protocol="GHOST_v8"
    isOpen={visible}
    onClose={close}
    maxWidth="max-w-5xl"
    zIndex={Z_INDEX_ADMIN.MODAL_CONFIRM}
  >
    <div class="p-12 md:p-20 relative">
      <div class="max-w-4xl mx-auto relative z-10">
        <!-- source Meta-data -->
        <div
          class="mb-12 flex items-center justify-between border-l-2 border-neon-cyan pl-6 py-2 bg-neon-cyan/5"
        >
          <div>
            <span
              class="text-[9px] text-neon-cyan/60 uppercase font-mono block mb-1"
              >Decrypted Source</span
            >
            <span class="text-lg font-bold text-white tracking-widest uppercase"
              >{log.source}</span
            >
          </div>
          <div class="text-right">
            <span
              class="text-[9px] text-neon-cyan/60 uppercase font-mono block mb-1"
              >Authentication</span
            >
            <span class="text-[11px] font-mono text-[#39FF14] uppercase"
              >Level 5 - Verified</span
            >
          </div>
        </div>

        <!-- Rule R81: Action Hub (Resume Capability) -->
        {#if log.data?.category === "CONTENT_CREATE" && (log.data?.status === "WAITING_FOR_REVIEW" || log.data?.status === "PROCESSING")}
          <div class="mb-12 p-8 rounded-[2.5rem] bg-neon-cyan/5 border border-neon-cyan/20 backdrop-blur-3xl relative overflow-hidden group/resume">
             <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,255,255,0.06)_0%,transparent_70%)] opacity-0 group-hover/resume:opacity-100 transition-opacity duration-700"></div>
             
             <div class="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                <div class="flex items-start gap-5">
                   <div class="w-14 h-14 rounded-2xl bg-neon-cyan/10 border border-neon-cyan/20 flex items-center justify-center text-neon-cyan shadow-[0_0_20px_rgba(0,255,255,0.1)]">
                      <Play size={28} fill="currentColor" class="translate-x-0.5" />
                   </div>
                   <div class="flex flex-col gap-1">
                      <h4 class="text-white font-bold text-lg tracking-tight uppercase">PHÁT HIỆN BẢN THẢO CHƯA XONG</h4>
                      <p class="text-neon-cyan/60 text-xs font-mono tracking-widest leading-relaxed">
                        CAMPAIGN_ID: {log.data.campaign_id.slice(0,18)}...<br/>
                        NEURAL_STATUS: {log.data.status} // STEP_{log.data.step}
                      </p>
                   </div>
                </div>
                
                <button 
                   onclick={() => nanobot.resumeCampaign(log)}
                   class="px-10 py-5 rounded-[2rem] bg-neon-cyan text-[#050505] font-black text-sm uppercase tracking-[0.2em] shadow-[0_20px_40px_-10px_rgba(0,255,255,0.4)] hover:scale-105 active:scale-95 transition-all duration-500 hover:shadow-[0_25px_50px_-5px_rgba(0,255,255,0.5)] flex items-center gap-3 group/btn"
                >
                   <span>Tiếp tục với XoHi</span>
                   <div class="w-1.5 h-1.5 bg-black rounded-full group-hover/btn:animate-ping"></div>
                </button>
             </div>
          </div>
        {/if}

        <!-- The Data Stream -->
        <article
          class="prose prose-invert max-w-none font-medium selection:bg-neon-cyan/40"
        >
          <div
            class="text-gray-300 text-lg leading-[1.8] tracking-wide mission-text"
          >
            {@html formatContent(log.message)}
          </div>
        </article>
      </div>
    </div>
  </MissionControlShell>
{/if}

<style>
  :global(.mission-text strong) {
    color: #00ffff !important;
    text-shadow: 0 0 8px rgba(0, 255, 255, 0.4);
    background: rgba(0, 255, 255, 0.05);
    padding: 0 4px;
    border-radius: 2px;
  }

  :global(.mission-text h2) {
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
  }
</style>
