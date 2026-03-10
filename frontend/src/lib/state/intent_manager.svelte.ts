import { ACTION_WIDGET_MAP } from "./constants";
import { handleFastAction, type HandlerDeps } from "./intent/FastActionHandler";
import { handleChatIntent } from "./intent/ChatIntentHandler";
import { handleVoiceIntent } from "./intent/VoiceIntentHandler";

interface IntentDeps {
  state: any;
  voice: {
    setVoiceResult: (
      transcript: string,
      responseText: string,
      uiAction: string,
      data?: Record<string, any>,
      source?: "text" | "voice",
      routerTier?: number
    ) => void;
    status: string;
    setVuiActive: (val: boolean) => void;
    resetVui: () => void;
    softReset: () => void;
  };
  log: {
    addLog: (msg: string, source?: string, type?: string, tier?: number, data?: Record<string, any>) => void;
  };
  ui: {
    setUniversalModalOpen: (val: boolean) => void;
    showToast: (msg: string, type: "success" | "error" | "warning" | "info") => void;
  };
  chat: any;
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

    // Phase 60: Always persist session context for multi-turn conversation
    if (data?.session_id) {
      state.currentData = { ...state.currentData, ...data };
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

    if (uiAction) {
      const targetWidget = ACTION_WIDGET_MAP[uiAction];
      if (targetWidget) {
        state.currentData = { ...state.currentData, ...data };
        const intentType = (data?.intent_type as string) || "";

        const requiresConfirmationForVoice = (d: any) => {
          return (
            source === "voice" &&
            (d?.action === "MUTATE" || d?.requires_confirmation === true || d?.intent_type === "MUTATE")
          );
        };

        if (
          isNavAction(uiAction, intentType) ||
          uiAction.includes("edit") ||
          data?.restricted === false ||
          requiresConfirmationForVoice(data)
        ) {
          state.activeWidget = targetWidget;
          ui.setUniversalModalOpen(true);
          log.addLog(uiAction.replace("show_", "").replace(/_/g, " "), "[ACTION]");
          
          if (source === "voice" && isNavAction(uiAction, intentType)) {
            voice.setVuiActive(false);
            import("$lib/vui").then(({ vuiController }) => {
              vuiController.setStopAfterSpeech(true);
            });
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

  async function processCommand(command: string, source: "text" | "voice" = "text") {
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
        await handleChatIntent(cmd, deps);
        return;
      }

      // 3. LUỒNG VOICE (Giọng nói)
      if (source === "voice") {
        await handleVoiceIntent(cmd, deps);
        return;
      }

    } catch (e: any) {
      state.nanoBotStatus = "ERROR";
      log.addLog(`Command failed: ${e.message}`, "Nanobot-Core");
      setTimeout(() => resetVui(), 4000);
    } finally {
      if (state.commandEpoch === myEpoch) state.isBusy = false;
    }
  }

  return { setVoiceResult, processCommand };
}
