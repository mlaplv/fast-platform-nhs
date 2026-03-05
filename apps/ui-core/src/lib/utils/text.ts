/**
 * Normalize Vietnamese text for comparison (remove diacritics, lowercase, trim)
 * Sync with backend's normalize_vn() logic.
 */
export function normalizeVn(text: string): string {
  if (!text) return "";
  let res = text.toLowerCase().trim();

  // Remove diacritics (Standard web approach for Vietnamese)
  res = res.normalize("NFD").replace(/[\u0300-\u036f]/g, "");

  // Specific Vietnamese characters not covered by NFD
  res = res.replace(/đ/g, "d");

  // Remove special characters, keeping only alphanumeric and spaces
  res = res.replace(/[^a-z0-9\s]/g, "");

  // Collapse multiple spaces
  res = res.replace(/\s+/g, " ");

  return res.trim();
}
