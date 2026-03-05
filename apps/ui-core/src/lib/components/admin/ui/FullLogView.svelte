<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade, fly, scale } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Terminal from "lucide-svelte/icons/terminal";
  import Cpu from "lucide-svelte/icons/cpu";
  import Activity from "lucide-svelte/icons/activity";

  import MissionControlShell from "./MissionControlShell.svelte";

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
