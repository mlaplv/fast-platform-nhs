<script lang="ts">
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { omni } from "$lib/state/omni.svelte";

  import Save from "lucide-svelte/icons/save";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";

  import TriggersGrid from "./voice/TriggersGrid.svelte";
  import LexiconControl from "./voice/LexiconControl.svelte";
  import NeuralIdentity from "./voice/NeuralIdentity.svelte";
  import CapabilitiesGrid from "./voice/CapabilitiesGrid.svelte";
  import ChatPersistence from "./voice/ChatPersistence.svelte";
  import SecurityFooter from "./voice/SecurityFooter.svelte";

  let wakeTriggers = $state<string[]>([]);
  let sleepTriggers = $state<string[]>([]);
  let greetingTemplate = $state("");
  let farewellTemplate = $state("");
  let capabilities = $state<any[]>([]);
  let sttOverrides = $state<Record<string, string>>({});
  let sttStopwords = $state<string[]>([]);
  let chatSettings = $state<Record<string, any>>({
    selective_persistence: true,
    save_ai_responses: false,
    auto_purge_days: 30,
    cache_limit: 10
  });

  let isLoading = $state(true);
  let isSaving = $state(false);

  function startTraining(type: any) {
    nanobot.voice.clearVuiResponse();
    nanobot.setTraining(true, type);
    nanobot.setModality("voice");
    omni.startTrainingRec();
    nanobot.addLog(`Initializing Neural Capture: ${type.toUpperCase()}`, "SYS");
  }

  // Hydration
  onMount(async () => {
    try {
      const [voice, over, stop] = await Promise.all([
        apiClient.get<any>("/api/v1/settings/voice").catch(() => null),
        apiClient.get<any>("/api/v1/settings/lexicon/overrides").catch(() => null),
        apiClient.get<any>("/api/v1/settings/lexicon/stopwords").catch(() => null)
      ]);

      if (voice) {
        wakeTriggers = voice.wake_words || ["xohi"];
        sleepTriggers = voice.sleep_words || ["ngủ đi"];
        greetingTemplate = voice.greeting_template || "";
        farewellTemplate = voice.farewell_template || "";
        capabilities = voice.capabilities || [];
        if (voice.chat_settings) chatSettings = { ...chatSettings, ...voice.chat_settings };
      }
      if (over?.overrides) sttOverrides = over.overrides;
      if (stop?.stopwords) sttStopwords = stop.stopwords.filter((w: string) => w?.trim());
    } finally {
      isLoading = false;
    }
  });

  async function saveSettings() {
    isSaving = true;
    try {
      const capMap = capabilities.reduce((acc, c) => ({ ...acc, [c.id]: c.active }), {});
      const res = await apiClient.post<any>("/api/v1/settings/voice", {
        wake_words: wakeTriggers,
        sleep_words: sleepTriggers,
        greeting_template: greetingTemplate,
        farewell_template: farewellTemplate,
        capabilities: capMap,
        is_campaign_mode: nanobot.isCampaignMode,
        chat_settings: chatSettings
      });

      if (res?.status === "success" && res.data) {
        const d = res.data;
        nanobot.updateVoiceSettings(
          d.wake_words,
          d.sleep_words,
          d.greeting_template,
          d.farewell_template,
          d.is_campaign_mode,
          d.chat_settings
        );
        nanobot.addLog("Agent Capabilities Synchronized", "Nanobot-Core", "success");
        nanobot.showToast("Cognitive Matrix committed successfully.", "success");
      }
    } catch (e: any) {
      nanobot.showToast("Failed to synchronize. See Neural Logs.", "error");
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="w-full h-full flex flex-col bg-[#020202] text-zinc-100 selection:bg-cyan-500/30 font-sans">
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center gap-8">
      <div class="relative">
        <div class="w-24 h-24 border-2 border-cyan-500/5 border-t-cyan-400 rounded-full animate-spin"></div>
      </div>
      <h2 class="text-xs font-mono text-cyan-400 uppercase tracking-[0.6em] animate-pulse">Initializing Neuro-Link</h2>
    </div>
  {:else}
    <header class="h-auto min-h-[5rem] lg:h-24 px-4 sm:px-8 lg:px-12 border-b border-white/5 flex flex-col lg:flex-row items-start lg:items-center justify-between bg-zinc-950/20 backdrop-blur-md gap-4 py-4 lg:py-0 z-50 sticky top-0">
      <div class="flex items-center gap-6">
        <div class="space-y-1">
          <h1 class="text-xl lg:text-2xl font-black italic tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 to-zinc-600">AGENT COCKPIT</h1>
          <div class="flex items-center gap-3">
             <div class="flex items-center gap-2 px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                <span class="text-[9px] font-mono text-emerald-500 uppercase tracking-widest text-nowrap">Neural Link Active</span>
             </div>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-4 w-full lg:w-auto justify-end">
        <button onclick={saveSettings} disabled={isSaving} class="group relative h-10 lg:h-12 px-8 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-xl shadow-[0_0_20px_rgba(8,145,178,0.4)] transition-all disabled:opacity-50 flex items-center gap-3">
          {#if isSaving} <RefreshCw size={16} class="animate-spin" />
          {:else} <Save size={16} class="group-hover:scale-110 transition-transform" /> {/if}
          <span class="text-xs uppercase tracking-[0.2em]">{isSaving ? 'Syncing...' : 'Commit Matrix'}</span>
        </button>
      </div>
    </header>

    <main class="flex-1 flex flex-col lg:flex-row min-h-0">
      <aside class="w-full lg:w-96 border-b lg:border-b-0 lg:border-r border-white/5 bg-zinc-950/20 overflow-y-auto custom-scrollbar flex flex-col p-6 sm:p-8 gap-12">
        <CapabilitiesGrid bind:capabilities />
        <SecurityFooter />
      </aside>

      <section class="flex-1 overflow-y-auto custom-scrollbar bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.03),transparent_70%)] p-4 sm:p-8 lg:p-10">
        <div class="max-w-7xl mx-auto space-y-10">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <TriggersGrid bind:wakeTriggers bind:sleepTriggers onStartTraining={startTraining} />
            <LexiconControl bind:sttOverrides bind:sttStopwords onStartTraining={startTraining} />
          </div>
          <ChatPersistence bind:chatSettings />
          <NeuralIdentity bind:greetingTemplate bind:farewellTemplate />
        </div>
      </section>
    </main>
  {/if}
</div>

<style>
  @keyframes fadeScaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
</style>
