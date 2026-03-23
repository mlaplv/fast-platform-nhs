import { ACTION_WIDGET_MAP } from "./constants";
import { handleFastAction, type HandlerDeps } from "./intent/FastActionHandler";
import { handleChatIntent } from "./intent/ChatIntentHandler";
import { handleVoiceIntent } from "./intent/VoiceIntentHandler";
import type { WidgetType, ToastType, CommandAction, Suggestion, ChatSettings } from "./types";

interface IntentDeps {
  state: {
    activeWidget: WidgetType;
    commandAction: CommandAction | null;
    nanoBotStatus: string;
    currentData: Record<string, unknown> | null;
    isBusy: boolean;
    lastProcessedCommand: string;
    lastProcessedTime: number;
    lastSpokenText: string;
    lastSpokenTime: number;
    commandEpoch: number;
    lastSuggestedWidget?: WidgetType;
  };
  voice: {
    setVoiceResult: (
      transcript: string,
      responseText: string,
      uiAction: string,
      data?: Record<string, unknown>,
      source?: "text" | "voice",
      routerTier?: number
    ) => void;
    status: string;
    setVuiActive: (val: boolean) => void;
    resetVui: () => void;
    softReset: () => void;
  };
  log: {
    addLog: (msg: string, source?: string, type?: string, tier?: number, data?: Record<string, unknown>) => void;
  };
  ui: {
    setUniversalModalOpen: (val: boolean) => void;
    showToast: (msg: string, type: ToastType) => void;
  };
  chat: {
    history: import("./chat.svelte").ChatMessage[];
    pagination: { cursor: string | null; hasMore: boolean; isLoading: boolean };
    hydrateHistory: (sessionId: string, callback?: (logs: import("./types").SystemLog[]) => void, userId?: string, sinceId?: string, force?: boolean) => Promise<void>;
    loadMoreMessages: (callback?: (logs: import("./types").SystemLog[]) => void, sessionId?: string, userId?: string) => Promise<void>;
    clearHistory: (sessionId: string) => Promise<boolean | undefined>;
  };
}

export function createIntentManager(
  state: IntentDeps["state"],
  voice: IntentDeps["voice"],
  log: IntentDeps["log"],
  ui: IntentDeps["ui"],
  chat: IntentDeps["chat"],
  resetVui: () => void,
  softReset: () => void,
  setThinking: (val: boolean, source?: "text" | "voice") => void
) {
  const deps: HandlerDeps = { state, voice, log, ui, resetVui, softReset };

  function isNavAction(uiAction: string, intentType: string) {
    return intentType === "UI_NAV";
  }

  function setVoiceResult(
    transcript: string,
    responseText: string,
    uiAction: string,
    data: Record<string, unknown>,
    source: "text" | "voice" = "text",
    routerTier?: number
  ) {
    state.lastSpokenText = responseText.toLowerCase();
    state.lastSpokenTime = Date.now();

    if (responseText && responseText !== "NONE" && responseText.trim().length > 0) {
      log.addLog(responseText, "XOHI", "info", routerTier, data);
    }

    voice.setVoiceResult(transcript, responseText, uiAction, data, source, routerTier);
    state.nanoBotStatus = voice.status === "VOICE" ? "IDLE" : "SUCCESS";

    // Phase 82: Robust data isolation (Sếp's Request)
    if (data) {
      const newCid = data.campaign_id || data.id || (data.data as any)?.campaign_id || (data.data as any)?.id;
      const oldCid = (state.currentData as any)?.campaign_id || (state.currentData as any)?.id;

      // Logic: If it's a NEW campaign ID, we MUST replace the entire data object to avoid leakage (e.g. Hôi nách nam -> Hôi nách nữ)
      if (newCid && oldCid && newCid !== oldCid) {
        console.log("[DEBUG] New Campaign Context. Replacing stale data.");
        state.currentData = { ...data };
      } else {
        // Same campaign: merge normally for incremental updates (like Step 1 -> 2)
        state.currentData = { ...state.currentData, ...data };
      }

      // Flatten data.data if it exists (Smart Flattening Phase 60)
      if (data.data && typeof data.data === 'object') {
        state.currentData = { ...state.currentData, ...data.data };
      }
    }

    // ═══ SESSION CONTROL OVERRIDES (Wake/Sleep) ═══
    if (data?.action === "HARDWARE_SLEEP") {
      log.addLog("Deactivating Neural Link", "SYS", "info");
      if (source === "voice") {
        voice.setVuiActive(false);
        import("$lib/vui").then(({ vuiController }) => {
          vuiController.setStopAfterSpeech(true);
        });
      }
    }

    if (uiAction || data?.ui_action) {
      const actualUiAction = (uiAction || data?.ui_action) as string;
      const targetWidget = ACTION_WIDGET_MAP[actualUiAction];

      if (targetWidget) {
        const mergedData = { ...state.currentData, ...data };
        if (data.data && typeof data.data === 'object') {
          Object.assign(mergedData, data.data);
        }
        state.currentData = mergedData;
        const intentType = (data?.intent_type as string) || "";
        console.log("[DEBUG TRACE] processAction -> action:", actualUiAction, "intentType:", intentType, "target:", targetWidget);

        const requiresConfirmationForVoice = (d: Record<string, unknown>) => {
          return (
            source === "voice" &&
            (d?.action === "MUTATE" || d?.requires_confirmation === true || d?.intent_type === "MUTATE")
          );
        };

        if (
          isNavAction(actualUiAction, intentType) ||
          actualUiAction.startsWith("show_") ||
          actualUiAction.includes("revenue") ||
          actualUiAction.includes("edit") ||
          actualUiAction.includes("content_factory") ||
          actualUiAction.includes("campaigns") ||
          actualUiAction === "CONTENT_CREATE" ||
          intentType === "CONTENT_CREATE" ||
          data?.restricted === false ||
          requiresConfirmationForVoice(data)
        ) {
          // Phase 82.5: Anti-Hijacking Guard
          // If a background update arrives from SSE/pulse (Neural Update), 
          // we ONLY open the modal if the user is already IN the CONTENT_REVIEW widget.
          // This prevents automated updates from stealing focus while the user is elsewhere.
          if (actualUiAction === "CONTENT_CREATE" && transcript === "Neural Update" && state.activeWidget !== "CONTENT_REVIEW") {
            console.log("[IntentManager] Deflecting background Content Factory hijack.");
            return;
          }

          state.activeWidget = targetWidget;
          ui.setUniversalModalOpen(true);
          console.log("[DEBUG TRACE] Bật UniversalModal với widget:", targetWidget, "Dữ liệu:", state.currentData);
          log.addLog(actualUiAction.replace("show_", "").replace(/_/g, " "), "[ACTION]");

          if (
            source === "voice" && 
            (isNavAction(actualUiAction, intentType) || 
             actualUiAction.startsWith("show_") || 
             actualUiAction.includes("revenue") ||
             actualUiAction === "CONTENT_CREATE" ||
             intentType === "CONTENT_CREATE")
          ) {
            voice.setVuiActive(false);
          }
        } else {
          state.lastSuggestedWidget = targetWidget;
          if (source !== "voice") {
            log.addLog("Sếp gõ 'mở' nếu muốn xem chi tiết.", "SYS");
          }
        }
      }
    }
  }

  async function processCommand(command: string, source: "text" | "voice" = "text", intentData?: Record<string, unknown>) {
    const now = Date.now();
    let cmd = command.toLowerCase().trim();
    if (!cmd) {
      resetVui();
      return;
    }

    // Anti-Spam Gate
    const isFragment =
      state.lastProcessedCommand &&
      (cmd.includes(state.lastProcessedCommand) || state.lastProcessedCommand.includes(cmd));
    if (
      state.lastProcessedCommand &&
      now - state.lastProcessedTime < 3000 &&
      (isFragment || (cmd.length < 5 && cmd !== "mở"))
    )
      return;
    if (
      now - state.lastSpokenTime < 3000 &&
      (state.lastSpokenText.includes(cmd) || cmd.includes(state.lastSpokenText))
    )
      return;

    state.isBusy = true;
    state.lastProcessedCommand = cmd;
    state.lastProcessedTime = now;
    log.addLog(command, "[ADMIN]");
    setThinking(true, source);
    const myEpoch = ++state.commandEpoch;

    try {
      if (cmd === "clear" || cmd === "reset") {
        state.activeWidget = "NONE";
        resetVui();
        return;
      }

      // ═══ TRI-FLUX ROUTING ═══

      // 1. LUỒNG FAST ACTION (UI Click / Direct Match)
      // Check local system commands BEFORE AI Ghost to ensure instant UI response.
      const isFastActionHandled = await handleFastAction(cmd, deps, source);
      if (isFastActionHandled) return;

      // 2. LUỒNG CHAT AI (Bàn phím)
      if (source === "text") {
        await handleChatIntent(cmd, deps, intentData);
        return;
      }

      // 3. LUỒNG VOICE (Giọng nói)
      if (source === "voice") {
        await handleVoiceIntent(cmd, deps);
        return;
      }

    } catch (e: unknown) {
      state.nanoBotStatus = "ERROR";
      log.addLog(`Command failed: ${(e as Error).message}`, "Nanobot-Core");
      setTimeout(() => resetVui(), 4000);
    } finally {
      if (state.commandEpoch === myEpoch) state.isBusy = false;
    }
  }

  return { setVoiceResult, processCommand };
}
