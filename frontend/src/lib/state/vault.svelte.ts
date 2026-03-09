import type { PendingAction } from "./types";

export function createVaultState(
  addLogFn: (msg: string, src?: string) => void,
) {
  const state = $state({
    pendingApprovals: [] as PendingAction[],
  });

  function addPendingAction(action: PendingAction) {
    state.pendingApprovals.push(action);
  }

  function approveAction(id: string) {
    state.pendingApprovals = state.pendingApprovals.filter((p) => p.id !== id);
    addLogFn(`Vault Action APPROVED by Admin. Executing...`, "Nanobot-Vault");
  }

  function denyAction(id: string) {
    state.pendingApprovals = state.pendingApprovals.filter((p) => p.id !== id);
    addLogFn(`Vault Action DENIED by Admin. Aborted.`, "Nanobot-Vault");
  }

  return {
    get pendingApprovals() {
      return state.pendingApprovals;
    },
    addPendingAction,
    approveAction,
    denyAction,
  };
}
