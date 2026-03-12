import { safeRandomUUID } from "./utils";
import { type SystemLog } from "./types";

export function createLogState() {
  const state = $state({
    activityLogs: [] as SystemLog[],
    expandedLog: null as SystemLog | null,
  });

  function sortLogs(arr: SystemLog[]) {
    return arr.sort((a, b) => {
      const timeDiff = a.timestamp.getTime() - b.timestamp.getTime();
      const p = (source: string) => {
         const src = String(source || "").toUpperCase();
         if (src.includes('ADMIN') || src.includes('ADM') || src.includes('SẾP')) return 0;
         if (src.includes('XOHI') || src.includes('XÔ-HỈ')) return 1;
         return 2;
      };
      if (Math.abs(timeDiff) < 60000) {
        const pA = p(a.source);
        const pB = p(b.source);
        if (pA !== pB) return pA - pB;
      }
      return timeDiff;
    });
  }

  function upsertLogs(incoming: SystemLog[]) {
    const current = [...state.activityLogs];
    let changed = false;

    incoming.forEach((newL) => {
      // 1. Find exact match by ID
      let idx = current.findIndex(ex => ex.id === newL.id);
      
      // 2. Fallback: Find by Campaign ID + Step (Hardening for Content Factory updates)
      if (idx === -1 && newL.data?.campaign_id) {
        idx = current.findIndex(ex => 
          ex.data?.campaign_id === newL.data?.campaign_id && 
          String(ex.data?.step ?? "") === String(newL.data?.step ?? "")
        );
      }

      if (idx === -1) {
        current.push(newL);
        changed = true;
      } else {
        const currentDataStr = JSON.stringify(current[idx].data || "{}");
        const newDataStr = JSON.stringify(newL.data || "{}");
        
        if (newDataStr.length > currentDataStr.length || current[idx].id !== newL.id || current[idx].type !== newL.type) {
          current[idx] = { ...current[idx], ...newL };
          changed = true;
        }
      }
    });

    if (changed || incoming.length === 0) {
      const unique = Array.from(new Map(current.map(l => [l.id, l])).values());
      state.activityLogs = sortLogs(unique).slice(-150);
    }
  }

  function addLog(
    message: string,
    source: string = "Nanobot-Core",
    type: string = "info",
    routerTier?: number,
    data?: Record<string, any>
  ) {
    const newLog: SystemLog = {
      id: safeRandomUUID(),
      timestamp: new Date(),
      message,
      source,
      type,
      routerTier,
      data
    };
    upsertLogs([newLog]);
  }

  return {
    get activityLogs() { return state.activityLogs; },
    get expandedLog() { return state.expandedLog; },
    
    setActivityLogs: (logs: SystemLog[]) => { state.activityLogs = sortLogs(logs).slice(-150); },
    upsertLogs,
    addLog,
    showFullLog(log: SystemLog) { state.expandedLog = log; },
    closeFullLog() { state.expandedLog = null; },
  };
}
