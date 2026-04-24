import type { HandlerDeps } from "./FastActionHandler";

/**
 * ChatIntentHandler
 * Responsibility: AI-powered Text Q&A (OmniCommand input).
 * Constraints: SILENT & HIDDEN. Response appears only in logs.
 */
export async function handleChatIntent(
  command: string,
  deps: HandlerDeps,
  intentData?: Record<string, unknown>
): Promise<boolean> {
  const { state, voice, resetVui } = deps;
  
  // Unified Chat: KHÔNG set isVuiActive ở đây — để execTextCmd xử lý đồng bộ
  // cả isVuiActive + phase="thinking" cùng 1 tick, tránh Safety Unmount race condition
  
  const { vuiController } = await import("$lib/vui");
  
  // Explicitly trigger AI Ghost with "text" source for silent processing
  const hasAiHandled = await vuiController.processGhost(command, "text", intentData);
  
  if (hasAiHandled) {
    state.nanoBotStatus = "SUCCESS";
    state.isBusy = false;
    // We don't call resetVui here because processGhost -> execTextCmd -> streamLLM 
    // will eventually set phase to idle. But we ensure isVuiActive is false.
    return true;
  }

  return false;
}
