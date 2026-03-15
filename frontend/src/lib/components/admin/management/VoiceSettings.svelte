<script lang="ts">
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiController } from "$lib/vui";

  import Save from "lucide-svelte/icons/save";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";

  import TriggersGrid from "./voice/TriggersGrid.svelte";
  import LexiconControl from "./voice/LexiconControl.svelte";
  import NeuralIdentity from "./voice/NeuralIdentity.svelte";
  import CapabilitiesGrid from "./voice/CapabilitiesGrid.svelte";
  import ChatPersistence from "./voice/ChatPersistence.svelte";
  import SecurityFooter from "./voice/SecurityFooter.svelte";
  import GeminiControl from "./voice/GeminiControl.svelte";
  import GeminiDiagnosticsModal from "./voice/GeminiDiagnosticsModal.svelte";

  interface Capability {
    id: string;
    label: string;
    active: boolean;
    description?: string;
  }

  interface ChatSettings {
    selective_persistence: boolean;
    save_ai_responses: boolean;
    auto_purge_days: number;
    cache_limit: number;
  }

  interface VoiceSettingsResponse {
    wake_words: string[];
    sleep_words: string[];
    greeting_template: string;
    farewell_template: string;
    capabilities: Capability[];
    chat_settings: ChatSettings;
    stt_anchors: string[];
    mic_sensitivity: number;
    status?: string;
    data?: VoiceSettingsResponse;
  }

  let wakeTriggers = $state<string[]>([]);
  let sleepTriggers = $state<string[]>([]);
  let greetingTemplate = $state("");
  let farewellTemplate = $state("");
  let capabilities = $state<Capability[]>([]);
  let sttOverrides = $state<Record<string, string>>({});
  let sttStopwords = $state<string[]>([]);
  let sttAnchors = $state<string[]>([]);
  let micSensitivity = $state(0.6);
  let chatSettings = $state<ChatSettings>({
    selective_persistence: true,
    save_ai_responses: false,
    auto_purge_days: 30,
    cache_limit: 10,
  });
  let showGeminiDiagnostics = $state(false);

  let isLoading = $state(true);
  let isSaving = $state(false);

  function startTraining(type: "wake" | "sleep") {
    nanobot.voice.clearVuiResponse();
    nanobot.setTraining(true, type);
    nanobot.setModality("voice");
    vuiController.startRecording();
    nanobot.addLog(`Initializing Neural Capture: ${type.toUpperCase()}`, "SYS");
  }

  // Hydration
  onMount(async () => {
    try {
      const [voice, over, stop] = await Promise.all([
        apiClient.get<VoiceSettingsResponse>("/api/v1/settings/voice").catch(() => null),
        apiClient
          .get<{ overrides: Record<string, string> }>("/api/v1/settings/lexicon/overrides")
          .catch(() => null),
        apiClient
          .get<{ stopwords: string[] }>("/api/v1/settings/lexicon/stopwords")
          .catch(() => null),
      ]);

      if (voice) {
        wakeTriggers = voice.wake_words || ["xohi"];
        sleepTriggers = voice.sleep_words || ["ngủ đi"];
        greetingTemplate = voice.greeting_template || "";
        farewellTemplate = voice.farewell_template || "";
        capabilities = voice.capabilities || [];
        if (voice.chat_settings)
          chatSettings = { ...chatSettings, ...voice.chat_settings };
        if (voice.stt_anchors) sttAnchors = voice.stt_anchors;
        if (voice.mic_sensitivity !== undefined) micSensitivity = voice.mic_sensitivity;
      }
      if (over?.overrides) sttOverrides = over.overrides;
      if (stop?.stopwords)
        sttStopwords = stop.stopwords.filter((w: string) => w?.trim());
    } finally {
      isLoading = false;
    }
  });

  async function saveSettings() {
    isSaving = true;
    try {
      const capMap = capabilities.reduce(
        (acc, c) => ({ ...acc, [c.id]: c.active }),
        {} as Record<string, boolean>,
      );
      const res = await apiClient.post<VoiceSettingsResponse>("/api/v1/settings/voice", {
        wake_words: wakeTriggers,
        sleep_words: sleepTriggers,
        greeting_template: greetingTemplate,
        farewell_template: farewellTemplate,
        capabilities: capMap,
        is_campaign_mode: nanobot.isCampaignMode,
        chat_settings: chatSettings,
        stt_anchors: sttAnchors,
        mic_sensitivity: micSensitivity,
      });

      if (res?.status === "success" && res.data) {
        const d = res.data;
        nanobot.updateVoiceSettings(
          d.wake_words,
          d.sleep_words,
          d.greeting_template,
          d.farewell_template,
          d.is_campaign_mode,
          d.chat_settings as unknown as Record<string, unknown>,
          d.stt_anchors,
          d.mic_sensitivity
        );
        nanobot.addLog(
          "Agent Capabilities Synchronized",
          "Nanobot-Core",
          "success",
        );
        nanobot.showToast(
          "Cognitive Matrix committed successfully.",
          "success",
        );
      }
    } catch (e: unknown) {
      nanobot.showToast("Failed to synchronize. See Neural Logs.", "error");
    } finally {
      isSaving = false;
    }
  }
</script>

<div
  class="w-full h-full flex flex-col bg-[#020202] text-zinc-100 selection:bg-cyan-500/30 font-sans"
>
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center gap-8">
      <div class="relative">
        <div
          class="w-24 h-24 border-2 border-cyan-500/5 border-t-cyan-400 rounded-full animate-spin"
        ></div>
      </div>
      <h2
        class="text-xs font-mono text-cyan-400 uppercase tracking-[0.6em] animate-pulse"
      >
        Initializing Neuro-Link
      </h2>
    </div>
  {:else}
    <header
      class="h-auto min-h-[3.5rem] lg:h-16 px-4 sm:px-6 lg:px-8 border-b border-white/5 flex flex-col lg:flex-row items-center justify-between bg-zinc-950/40 backdrop-blur-xl gap-4 py-2 lg:py-0 z-50 sticky top-0"
    >
      <div class="flex items-center gap-4">
        <div class="flex flex-col lg:flex-row lg:items-center gap-2 lg:gap-4">
          <h1
            class="text-lg lg:text-xl font-black italic tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 to-zinc-500"
          >
            AGENT COCKPIT
          </h1>
          <div
            class="flex items-center gap-2 px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded-md"
          >
            <div
              class="w-1 h-1 rounded-full bg-emerald-500 animate-pulse"
            ></div>
            <span
              class="text-[8px] font-mono text-emerald-500 uppercase tracking-widest"
              >Neural Link Active</span
            >
          </div>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          onclick={saveSettings}
          disabled={isSaving}
          class="group relative h-9 lg:h-10 px-6 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-lg shadow-[0_0_15px_rgba(8,145,178,0.3)] transition-all disabled:opacity-50 flex items-center gap-2"
        >
          {#if isSaving}
            <RefreshCw size={14} class="animate-spin" />
          {:else}
            <Save
              size={14}
              class="group-hover:scale-110 transition-transform"
            />
          {/if}
          <span class="text-[10px] uppercase tracking-[0.15em] font-black"
            >{isSaving ? "Syncing..." : "Commit Matrix"}</span
          >
        </button>
      </div>
    </header>

    <main class="flex-1 flex flex-col lg:flex-row min-h-0">
      <aside
        class="w-full lg:w-80 border-b lg:border-b-0 lg:border-r border-white/5 bg-zinc-950/20 overflow-y-auto custom-scrollbar flex flex-col p-4 sm:p-6 gap-8"
      >
        <CapabilitiesGrid bind:capabilities />
        <SecurityFooter />
      </aside>

      <section
        class="flex-1 overflow-y-auto custom-scrollbar bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.03),transparent_70%)] p-4 sm:p-6 lg:p-8"
      >
        <div class="max-w-7xl mx-auto space-y-6">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <TriggersGrid
              bind:wakeTriggers
              bind:sleepTriggers
              onStartTraining={startTraining}
            />
            <LexiconControl
              bind:sttOverrides
              bind:sttStopwords
              onStartTraining={startTraining}
            />
            <!-- STT Engine Tuning Block -->
            <div class="bg-zinc-950/40 border border-white/5 rounded-xl p-5 space-y-4 lg:col-span-2">
              <h3 class="text-sm font-black text-cyan-400 uppercase tracking-widest flex items-center gap-2">
                STT Engine Tuning
              </h3>
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label class="block text-xs text-zinc-400 mb-1 font-bold">Context Anchors (Max 30)</label>
                  <p class="text-[10px] text-zinc-500 mb-2">Inject exact domain keywords to help Whisper detect accents perfectly. Press Enter to add.</p>
                  <div class="flex flex-wrap gap-2 p-2 bg-black/50 border border-white/5 rounded-lg min-h-[2.5rem]">
                    {#each sttAnchors as anchor, i}
                      <span class="px-2 py-1 bg-cyan-950/30 text-cyan-300 text-xs rounded border border-cyan-500/20 flex items-center gap-1 group">
                        {anchor}
                        <button onclick={() => sttAnchors = sttAnchors.filter((_, idx) => idx !== i)} class="text-cyan-500/50 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">×</button>
                      </span>
                    {/each}
                    <input 
                      type="text" 
                      placeholder="Type & press Enter..." 
                      class="bg-transparent border-none text-xs text-white focus:outline-none flex-1 min-w-[120px]"
                      onkeydown={(e) => {
                        if (e.key === 'Enter' && e.currentTarget.value.trim() && sttAnchors.length < 30) {
                          sttAnchors = [...sttAnchors, e.currentTarget.value.trim()];
                          e.currentTarget.value = '';
                        }
                      }}
                    />
                  </div>
                </div>
                <div>
                  <div class="flex justify-between items-center mb-1">
                    <label class="text-xs text-zinc-400 font-bold">Mic Sensitivity (Kill-Switch)</label>
                    <span class="text-xs font-mono text-cyan-400">{Number(micSensitivity).toFixed(2)}</span>
                  </div>
                  <p class="text-[10px] text-zinc-500 mb-2">Strictness of noise rejection. 0.1 is paranoid. 0.9 allows noise. Sweet spot: 0.6</p>
                  <input type="range" min="0.1" max="1.0" step="0.05" bind:value={micSensitivity} class="w-full accent-cyan-500 mt-2 cursor-pointer" />
                </div>
              </div>
            </div>
          </div>
          <ChatPersistence bind:chatSettings />
          <GeminiControl onOpenDiagnostics={() => showGeminiDiagnostics = true} />
          <NeuralIdentity bind:greetingTemplate bind:farewellTemplate />
        </div>
      </section>
    </main>
  {/if}
</div>

<GeminiDiagnosticsModal 
  show={showGeminiDiagnostics} 
  onClose={() => showGeminiDiagnostics = false} 
/>

<style>
  @keyframes fadeScaleIn {
    from {
      opacity: 0;
      transform: scale(0.95);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }
</style>
