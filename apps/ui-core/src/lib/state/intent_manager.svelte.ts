import { apiClient } from "$lib/utils/apiClient";
import { persistMessage } from "./chat.svelte";
import { COMMAND_WIDGET_MAP, ACTION_WIDGET_MAP, WIDGET_VI_LABEL } from "./constants";
import type { WidgetType } from "./types";

interface IntentDeps {
  state: any;
  voice: {
    setVoiceResult: (
      transcript: string,
      responseText: string,
      uiAction: string,
      source: "text" | "voice",
      routerTier?: number
    ) => void;
    status: string;
    setVuiActive: (val: boolean) => void;
    resetVui: () => void;
  };
  log: {
    addLog: (msg: string, source?: string, type?: string, tier?: number) => void;
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
  setThinking: (val: boolean, source?: "text" | "voice") => void
) {
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
      log.addLog(responseText, "XOHI", "info", routerTier);
    }

    voice.setVoiceResult(transcript, responseText, uiAction, source, routerTier);
    state.nanoBotStatus = voice.status === "VOICE" ? "IDLE" : "SUCCESS";

    if (uiAction) {
      const targetWidget = ACTION_WIDGET_MAP[uiAction];
      if (targetWidget) {
        state.currentData = data;
        const intentType = (data?.intent_type as string) || "";

        const requiresConfirmationForVoice = (d: any) => {
          return (
            source === "voice" &&
            (d?.action === "MUTATE" || d?.requires_confirmation === true || d?.intent_type === "MUTATE")
          );
        };

        if (
          intentType === "UI_NAV" ||
          uiAction.includes("edit") ||
          uiAction === "show_news_management" ||
          data?.restricted === false ||
          requiresConfirmationForVoice(data)
        ) {
          state.activeWidget = targetWidget;
          ui.setUniversalModalOpen(true);
          log.addLog(uiAction.replace("show_", "").replace(/_/g, " "), "[ACTION]");
        } else if (source === "voice") {
          // Speak only
        } else {
          state.lastSuggestedWidget = targetWidget;
          log.addLog("Sếp gõ 'mở' nếu muốn xem chi tiết.", "SYS");
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

    if (source === "voice") voice.setVuiActive(true);

    try {
      if (cmd === "clear" || cmd === "reset") {
        state.activeWidget = "NONE";
        resetVui();
        return;
      }

      if (cmd === "mở" && state.lastSuggestedWidget !== "NONE") {
        state.activeWidget = state.lastSuggestedWidget;
        ui.setUniversalModalOpen(true);
        state.lastSuggestedWidget = "NONE";
        state.nanoBotStatus = "SUCCESS";
        state.isBusy = false;
        return;
      }

      const matchedWidget =
        COMMAND_WIDGET_MAP[cmd] ||
        Object.entries(COMMAND_WIDGET_MAP).find(([k]) => {
          const words = cmd.split(" ");
          return cmd === k || (words.length <= 4 && cmd.includes(k));
        })?.[1];

      if (matchedWidget) {
        const viLabel = WIDGET_VI_LABEL[matchedWidget] || matchedWidget.replace(/_/g, " ");
        const xohiReply = `Dạ, em mở ${viLabel} cho sếp ạ.`;
        log.addLog(xohiReply, "XOHI");

        if (source === "voice") {
          persistMessage("account", "user", command, source);
          persistMessage("account", "assistant", xohiReply, source, {
            ui_action: `show_${matchedWidget.toLowerCase()}`,
          });
          const { omni } = await import("./omni.svelte");
          await omni.speak(xohiReply);
        } else {
          state.activeWidget = matchedWidget;
          ui.setUniversalModalOpen(true);
          persistMessage("account", "user", command, source);
          persistMessage("account", "assistant", xohiReply, source, {
            ui_action: `show_${matchedWidget.toLowerCase()}`,
          });
        }
        state.nanoBotStatus = "SUCCESS";
        state.isBusy = false;
        return;
      }

      const { omni } = await import("./omni.svelte");
      await omni.processGhost(cmd, source);
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
