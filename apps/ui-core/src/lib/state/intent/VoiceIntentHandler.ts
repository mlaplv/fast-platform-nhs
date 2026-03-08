import type { HandlerDeps } from "./FastActionHandler";

/**
 * VoiceIntentHandler
 * Responsibility: Full VUI Interaction.
 * Constraints: ACTIVE & PROACTIVE. Triggers orb, modal, and speech.
 */
export async function handleVoiceIntent(
  command: string,
  deps: HandlerDeps
): Promise<boolean> {
  const { state, voice } = deps;
  
  // Phase 55: Ensure VUI visuals are explicitly ON for voice source
  voice.setVuiActive(true);
  
  const { vuiController } = await import("$lib/vui");
  
  // Explicitly trigger AI Ghost with "voice" source
  const hasAiHandled = await vuiController.processGhost(command, "voice");
  
  if (hasAiHandled) {
    state.nanoBotStatus = "SUCCESS";
    state.isBusy = false;
    return true;
  }

  return false;
}
