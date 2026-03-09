import { nanobot } from "./nanobot.svelte";

/**
 * OmniController Utilities
 * Extracted to comply with Rule 1.3 (300 LOC limit).
 */
export function getVisibleDataIds(): string[] {
  const ids: string[] = [];
  const pathParts = window.location.pathname.split("/");
  const lastPart = pathParts[pathParts.length - 1];
  if (lastPart && /^\d+$/.test(lastPart)) ids.push(lastPart);
  
  const data = nanobot.currentData;
  if (data) {
    if (data.id) ids.push(String(data.id));
    if (data.items && Array.isArray(data.items)) {
      for (const item of data.items) {
        if (item && typeof item === "object" && "id" in item)
          ids.push(String(item.id));
      }
    }
  }
  return [...new Set(ids)];
}

export const ACTION_VI: Record<string, string> = {
  READ: "Phân tích Dữ liệu",
  MUTATE: "Thay đổi Hệ thống",
  ANALYZE: "Suy luận Chuyên sâu",
};
