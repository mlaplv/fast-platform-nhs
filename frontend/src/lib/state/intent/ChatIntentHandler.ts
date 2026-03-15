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
  
  // Phase 55: Ensure VUI visuals are forced OFF for chat initially
  // Reverted blind VUI activation. VUI state is now managed by the VuiOrchestrator based on source.
  
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
