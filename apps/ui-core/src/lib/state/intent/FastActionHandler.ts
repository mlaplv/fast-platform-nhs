import { COMMAND_WIDGET_MAP, WIDGET_VI_LABEL } from "../constants";
import { persistMessage } from "../chat.svelte";

export interface HandlerDeps {
  state: any;
  voice: any;
  log: any;
  ui: any;
  resetVui: () => void;
}

/**
 * FastActionHandler
 * Responsibility: Instant UI navigation (Widgets, Skills, Header Phím tắt).
 * Constraints: Strictly local, ABSOLUTELY NO AI FALLBACK.
 */
export async function handleFastAction(
  command: string,
  deps: HandlerDeps,
  source: "text" | "voice" = "text"
): Promise<boolean> {
  const { state, voice, log, ui, resetVui } = deps;
  const cmd = command.toLowerCase().trim();

  // 1. Strict Mapping Lookup
  const matchedWidget =
    COMMAND_WIDGET_MAP[cmd] ||
    Object.entries(COMMAND_WIDGET_MAP).find(([k]) => {
      const isExplicitOpen =
        cmd.includes("mở") ||
        cmd.includes("xem") ||
        cmd.includes("show") ||
        cmd.includes("manage");
      
      // Generic words require explicit intent
      if (k.length < 10 && !isExplicitOpen) return false;
      
      // Fuzzy match for joined words (e.g. voicesetting -> voice settings)
      const kNoSpace = k.replace(/\s/g, "");
      return cmd === k || cmd.includes(k) || cmd.includes(kNoSpace);
    })?.[1];

  if (matchedWidget) {
    const viLabel = WIDGET_VI_LABEL[matchedWidget] || matchedWidget.replace(/_/g, " ");
    const xohiReply = `Dạ, em mở ${viLabel} cho sếp ạ.`;

    log.addLog(xohiReply, "XOHI");
    state.activeWidget = matchedWidget;
    ui.setUniversalModalOpen(true);
    
    persistMessage("account", "user", command, source);
    persistMessage("account", "assistant", xohiReply, source, {
      ui_action: `show_${matchedWidget.toLowerCase()}`,
    });

    if (source === "voice") {
       const { vuiController } = await import("$lib/vui");
       vuiController.setStopAfterSpeech(true);
       await vuiController.speak(xohiReply);
    } else {
       // Phase 55 Enforcement: Clean up VUI state for fast actions triggered by text
       resetVui();
    }

    state.nanoBotStatus = "SUCCESS";
    state.isBusy = false;
    return true; // Handled locally
  }

  // 2. Fragment Match for "mở"
  if (cmd === "mở" && state.lastSuggestedWidget !== "NONE") {
    state.activeWidget = state.lastSuggestedWidget;
    ui.setUniversalModalOpen(true);
    state.lastSuggestedWidget = "NONE";
    state.nanoBotStatus = "SUCCESS";
    state.isBusy = false;
    resetVui();
    return true;
  }

  return false; // Not a fast action
}
