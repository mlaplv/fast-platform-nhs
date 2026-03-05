import { safeRandomUUID } from "./utils";
import { type SystemLog } from "./types";

export function createLogState() {
  const state = $state({
    activityLogs: [] as SystemLog[],
    expandedLog: null as SystemLog | null,
  });

  function addLog(
    message: string,
    source: string = "Nanobot-Core",
    type: string = "info",
    routerTier?: number
  ) {
    const newLog: SystemLog = {
      id: safeRandomUUID(),
      timestamp: new Date(),
      message,
      source,
      type,
      routerTier
    };
    // Ensure uniqueness and limit size
    const updated = [...state.activityLogs, newLog];
    state.activityLogs = updated.slice(-150);
  }

  return {
    get activityLogs() { return state.activityLogs; },
    get expandedLog() { return state.expandedLog; },
    
    setActivityLogs(logs: SystemLog[]) { state.activityLogs = logs; },
    addLog,
    showFullLog(log: SystemLog) { state.expandedLog = log; },
    closeFullLog() { state.expandedLog = null; },
  };
}
