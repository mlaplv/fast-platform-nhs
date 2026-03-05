<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { fade, scale } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { omni } from "$lib/state/omni.svelte";

  import Mic from "lucide-svelte/icons/mic";
  import Moon from "lucide-svelte/icons/moon";
  import MessageSquare from "lucide-svelte/icons/message-square";
  import Save from "lucide-svelte/icons/save";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Brain from "lucide-svelte/icons/brain";

  let wakeTriggers = $state<string[]>([]);
  let sleepTriggers = $state<string[]>([]);
  let greetingTemplate = $state("");
  let isLoading = $state(true);
  let isSaving = $state(false);
  let editingWake = $state<number | null>(null);
  let editingSleep = $state<number | null>(null);



  // V44.0 Voice Onboarding State
  let capturedText = $derived(
    (nanobot.voice.vuiUserQuery || omni.liveTrans || "").toLowerCase(),
  );

  // V44.2 Training Handshake
  $effect(() => {
    const result = nanobot.trainingResult;
    const type = nanobot.trainingType;
    if (!result) return;

    untrack(() => {
      const results = (Array.isArray(result) ? result : [result]).map((r) =>
        r.toLowerCase(),
      );
      if (type === "wake") {
        wakeTriggers = [...new Set([...wakeTriggers, ...results])];
      } else if (type === "sleep") {
        sleepTriggers = [...new Set([...sleepTriggers, ...results])];
      }
      nanobot.addLog(
        `Neural Link Established: ${results.length} phrase(s)`,
        "SYS",
        "success",
      );
      nanobot.cancelTraining();
    });
  });

  // V40.0 Cognitive State (Dynamic from Backend)
  let capabilities = $state<any[]>([]);

  function startTraining(type: "wake" | "sleep") {
    nanobot.voice.clearVuiResponse();
    nanobot.setTraining(true, type);
    nanobot.setModality("voice");
    omni.startTrainingRec();
    nanobot.addLog(`Initializing Neural Capture: ${type.toUpperCase()}`, "SYS");
  }

  function cancelTraining() {
    nanobot.setTraining(false, null);
    nanobot.voice.clearVuiResponse();
  }

  function confirmTraining() {
    if (!capturedText) return;
    const lowerText = capturedText.toLowerCase();
    if (nanobot.trainingType === "wake") {
      wakeTriggers = [...new Set([...wakeTriggers, lowerText])];
    } else {
      sleepTriggers = [...new Set([...sleepTriggers, lowerText])];
    }
    cancelTraining();
    nanobot.addLog(`Neural Link Established: ${lowerText}`, "SYS", "success");
  }

  // Fetch current settings
  onMount(async () => {
    try {
      const res = await apiClient
        .get<any>("/api/v1/settings/voice")
        .catch(() => null);
      if (res) {
        wakeTriggers = res.wake_words || ["xohi", "oi xohi"];
        sleepTriggers = res.sleep_words || ["tam biet", "ngu di"];
        greetingTemplate = res.greeting_template || "Dạ, em nghe đây sếp.";
        capabilities = res.capabilities || [];
      } else {
        wakeTriggers = ["xohi", "hey xohi"];
        sleepTriggers = ["tạm biệt", "ngủ đi"];
        greetingTemplate = "Dạ, em nghe đây sếp.";
      }

    } finally {
      isLoading = false;
    }
  });

  async function saveSettings() {
    isSaving = true;
    try {
      const capMap = capabilities.reduce(
        (acc, c) => ({ ...acc, [c.id]: c.active }),
        {},
      );

      const res = await apiClient.post<{
        wake_words?: string[];
        sleep_words?: string[];
      }>("/api/v1/settings/voice", {
        wake_words: wakeTriggers,
        sleep_words: sleepTriggers,
        greeting_template: greetingTemplate,
        capabilities: capMap,
      });

      if (res && res.status === "success" && res.data) {
        if (res.data.wake_words) wakeTriggers = res.data.wake_words;
        if (res.data.sleep_words) sleepTriggers = res.data.sleep_words;
        nanobot.updateVoiceSettings(
          wakeTriggers,
          sleepTriggers,
          greetingTemplate,
        );
      }


      nanobot.addLog("Agent Capabilities Synchronized", "Nanobot-Core", "success");
      nanobot.showToast("Cognitive Matrix committed successfully.", "success");
    } catch (e: any) {
      nanobot.addLog(`Sync Failed: ${e.message}`, "Nanobot-Core", "error");
      nanobot.showToast("Failed to synchronize. See Neural Logs.", "error");
    } finally {
      isSaving = false;
    }
  }

  function addWakeWord() {
    wakeTriggers = [...wakeTriggers, ""];
  }
  function addSleepWord() {
    sleepTriggers = [...sleepTriggers, ""];
  }
  function removeWakeWord(index: number) {
    wakeTriggers = wakeTriggers.filter((_, i) => i !== index);
  }
  function removeSleepWord(index: number) {
    sleepTriggers = sleepTriggers.filter((_, i) => i !== index);
  }
  function toggleCapability(id: string) {
    const cap = capabilities.find((c) => c.id === id);
    if (cap) cap.active = !cap.active;
  }
</script>

<div
  class="w-full h-full flex flex-col overflow-y-auto bg-black/40 backdrop-blur-xl relative"
>
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center gap-4">
      <div
        class="w-16 h-16 border-2 border-cyan-500/10 border-t-cyan-500 rounded-full animate-spin shadow-[0_0_20px_rgba(0,255,255,0.1)]"
      ></div>
      <p
        class="text-[10px] font-mono text-cyan-500/50 uppercase tracking-[0.3em] animate-pulse"
      >
        Initializing Cognitive Core...
      </p>
    </div>
  {:else}
    <div class="flex-1 p-8 pb-24">
      <div
        class="grid grid-cols-1 lg:grid-cols-12 gap-8"
        in:fade={{ duration: 800 }}
      >
        <!-- LEFT COLUMN: VOICE & PERSONALITY (6 Cols) -->
        <div class="lg:col-span-6 space-y-8">
          <!-- Wake Sector -->
          <div
            class="bg-white/[0.02] border border-white/5 rounded-3xl p-6 hover:bg-white/[0.04] transition-all group"
          >
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-3 text-cyan-400">
                <Mic size={18} />
                <h2 class="text-xs font-mono font-bold uppercase tracking-widest">
                  Neural Wake Triggers
                </h2>
              </div>
            </div>
            <div class="flex flex-wrap gap-2">
              {#each wakeTriggers as word, i}
                <div
                  class="inline-flex items-center gap-1.5 bg-cyan-500/10 border border-cyan-500/20 rounded-lg px-3 py-1.5 group hover:border-cyan-500/40 transition-all"
                  transition:scale={{ start: 0.8, duration: 150 }}
                >
                  {#if editingWake === i}
                    <input
                      bind:value={wakeTriggers[i]}
                      onblur={() => { wakeTriggers[i] = wakeTriggers[i].toLowerCase(); editingWake = null; }}
                      onkeydown={(e) => { if (e.key === "Enter") { wakeTriggers[i] = wakeTriggers[i].toLowerCase(); editingWake = null; } }}
                      class="bg-transparent outline-none text-[11px] font-mono text-white w-20 min-w-0"
                      autofocus
                    />
                  {:else}
                    <button
                      onclick={() => { editingWake = i; }}
                      class="text-[11px] font-mono text-white/90 cursor-text hover:text-cyan-300 transition-colors"
                      >{word}</button
                    >
                  {/if}
                  <button
                    onclick={() => removeWakeWord(i)}
                    class="w-4 h-4 flex items-center justify-center rounded-full text-white/20 hover:bg-red-500/30 hover:text-red-400 transition-all"
                    >&times;</button
                  >
                </div>
              {/each}
              <button
                onclick={() => startTraining("wake")}
                class="inline-flex items-center gap-1.5 px-3 py-1.5 border border-dashed border-cyan-500/30 rounded-lg text-[9px] font-mono text-cyan-400/60 hover:bg-cyan-500/5 hover:text-cyan-400 transition-all uppercase"
              >
                <Mic size={10} /> Train
              </button>
              <button
                onclick={addWakeWord}
                class="inline-flex items-center px-2.5 py-1.5 border border-dashed border-white/10 rounded-lg text-[10px] font-mono text-gray-500 hover:text-white transition-all"
                >+</button
              >
            </div>
          </div>

          <!-- Sleep Sector -->
          <div
            class="bg-white/[0.02] border border-white/5 rounded-3xl p-6 hover:bg-white/[0.04] transition-all"
          >
            <div class="flex items-center gap-3 text-red-400/80 mb-6">
              <Moon size={18} />
              <h2 class="text-xs font-mono font-bold uppercase tracking-widest">
                Termination Protocols
              </h2>
            </div>
            <div class="flex flex-wrap gap-2">
              {#each sleepTriggers as word, i}
                <div
                  class="inline-flex items-center gap-1.5 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-1.5 group hover:border-red-500/40 transition-all"
                  transition:scale={{ start: 0.8, duration: 150 }}
                >
                  {#if editingSleep === i}
                    <input
                      bind:value={sleepTriggers[i]}
                      onblur={() => { sleepTriggers[i] = sleepTriggers[i].toLowerCase(); editingSleep = null; }}
                      onkeydown={(e) => { if (e.key === "Enter") { sleepTriggers[i] = sleepTriggers[i].toLowerCase(); editingSleep = null; } }}
                      class="bg-transparent outline-none text-[11px] font-mono text-white w-20 min-w-0"
                      autofocus
                    />
                  {:else}
                    <button
                      onclick={() => { editingSleep = i; }}
                      class="text-[11px] font-mono text-white/90 cursor-text hover:text-red-300 transition-colors"
                      >{word}</button
                    >
                  {/if}
                  <button
                    onclick={() => removeSleepWord(i)}
                    class="w-4 h-4 flex items-center justify-center rounded-full text-white/20 hover:bg-red-500/30 hover:text-red-400 transition-all"
                    >&times;</button
                  >
                </div>
              {/each}
              <button
                onclick={() => startTraining("sleep")}
                class="inline-flex items-center gap-1.5 px-3 py-1.5 border border-dashed border-red-500/30 rounded-lg text-[9px] font-mono text-red-400/60 hover:bg-red-500/5 hover:text-red-400 transition-all uppercase"
              >
                <Moon size={10} /> Train
              </button>
              <button
                onclick={addSleepWord}
                class="inline-flex items-center px-2.5 py-1.5 border border-dashed border-white/10 rounded-lg text-[10px] font-mono text-gray-500 hover:text-white transition-all"
                >+</button
              >
            </div>
          </div>

          <!-- Personality -->
          <div
            class="bg-white/[0.02] border border-white/5 rounded-3xl p-6 hover:bg-white/[0.04] transition-all"
          >
            <div class="flex items-center gap-3 text-purple-400 mb-4">
              <MessageSquare size={18} />
              <h2 class="text-xs font-mono font-bold uppercase tracking-widest">
                Greeting Identity
              </h2>
            </div>
            <textarea
              bind:value={greetingTemplate}
              rows="3"
              class="w-full bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-xs font-mono text-white focus:border-purple-500/40 outline-none transition-all resize-none"
            ></textarea>
          </div>


        </div>

        <!-- RIGHT COLUMN: CAPABILITIES & INTEGRATIONS (6 Cols) -->
        <div class="lg:col-span-6 flex flex-col gap-8">


          <!-- Cognitive Matrix -->
          <div
            class="bg-gradient-to-br from-white/[0.03] to-transparent border border-white/5 rounded-3xl p-8 relative overflow-hidden group"
          >
            <div
              class="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity"
            >
              <Brain size={120} />
            </div>

            <div class="flex items-center gap-3 text-amber-400 mb-2">
              <Sparkles size={18} />
              <h2 class="text-xs font-mono font-bold uppercase tracking-widest">
                Cognitive Capability Matrix
              </h2>
            </div>
            <p class="text-[9px] font-mono text-gray-600 mb-8 leading-relaxed">
              Kiểm soát theo loại hành động (IntentAction), độc lập với Tier
              routing. Tắt toggle ⇒ chặn toàn bộ đường đi của action đó ở mọi
              tier (1/2/3).
            </p>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              {#each capabilities as cap}
                <button
                  onclick={() => toggleCapability(cap.id)}
                  class="flex flex-col p-5 bg-black/40 border {cap.active
                    ? 'border-amber-500/30 shadow-[0_0_20px_rgba(245,158,11,0.05)]'
                    : 'border-white/5'} rounded-2xl text-left transition-all hover:translate-y-[-2px]"
                >
                  <div class="flex items-center justify-between mb-3 w-full">
                    <div class="flex flex-col gap-0.5">
                      <span
                        class="text-[10px] font-mono font-bold tracking-widest {cap.color}"
                        >{cap.id}</span
                      >
                      <span
                        class="text-[8px] font-mono text-gray-700 uppercase tracking-wider"
                      >
                        {cap.id === "READ"
                          ? "Truy xuất (READ / COUNT)"
                          : cap.id === "MUTATE"
                            ? "Thay đổi (MUTATE)"
                            : "Phân tích (ANALYZE)"}
                      </span>
                    </div>
                    <div
                      class="w-10 h-5 bg-black/60 rounded-full border border-white/10 relative p-1 shrink-0"
                    >
                      <div
                        class="w-3 h-3 rounded-full transition-all duration-300 {cap.active
                          ? 'bg-amber-400 translate-x-5 shadow-[0_0_10px_rgba(251,191,36,0.5)]'
                          : 'bg-gray-700 translate-x-0'}"
                      ></div>
                    </div>
                  </div>
                  <h3
                    class="text-sm font-bold text-white mb-1 uppercase tracking-tighter"
                  >
                    {cap.name}
                  </h3>
                  <p
                    class="text-[9px] font-mono text-gray-500 leading-relaxed mb-3"
                  >
                    {cap.desc}
                  </p>

                  <div class="mt-auto pt-3 border-t border-white/5">
                    <p
                      class="text-[8px] font-mono text-amber-500/50 leading-tight"
                    >
                      {#if cap.id === "READ"}
                        Cho phép AI đọc và đếm dữ liệu (VD: tìm đơn hàng, doanh
                        thu). Hoạt động độc lập trên cả 3 Tier.
                      {:else if cap.id === "MUTATE"}
                        Cho phép AI thực hiện thay đổi hệ thống (R11). Nếu tắt,
                        mọi nỗ lực Sửa/Xóa của AI đều bị chặn.
                      {:else if cap.id === "ANALYZE"}
                        Kích hoạt luồng suy luận sâu của mô hình Cloud (Tier 3).
                        Dành cho báo cáo phức tạp.
                      {/if}
                    </p>
                  </div>
                </button>
              {/each}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sticky Bottom Save Bar -->
    <div
      class="sticky bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 via-black/70 to-transparent pointer-events-none z-10"
    >
      <div class="flex justify-end pointer-events-auto">
        <button
          onclick={saveSettings}
          disabled={isSaving}
          class="relative group overflow-hidden px-6 py-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl transition-all hover:border-cyan-400/50 hover:bg-cyan-500/15 active:scale-95 disabled:opacity-50 shadow-[0_0_30px_rgba(0,255,255,0.08)]"
        >
          <div
            class="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/5 to-cyan-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"
          ></div>
          <div class="flex items-center gap-2.5 relative z-10">
            {#if isSaving}
              <RefreshCw size={13} class="animate-spin text-cyan-400" />
              <span
                class="text-[10px] font-mono font-bold text-cyan-400 tracking-widest uppercase"
                >Synchronizing...</span
              >
            {:else}
              <Save size={13} class="text-cyan-400" />
              <span
                class="text-[10px] font-mono font-bold text-cyan-400 tracking-widest uppercase"
                >Commit Matrix</span
              >
            {/if}
          </div>
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Custom Scrollbar for Sci-Fi HUD feel */
  div::-webkit-scrollbar {
    width: 4px;
  }
  div::-webkit-scrollbar-track {
    background: transparent;
  }
  div::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 255, 0.05);
    border-radius: 10px;
  }
  div::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 255, 0.2);
  }
</style>
