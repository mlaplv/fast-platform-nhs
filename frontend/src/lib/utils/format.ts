export function formatCurrency(n: number): string {
  return new Intl.NumberFormat("vi-VN").format(n) + "đ";
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("vi-VN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m trước`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h trước`;
  return `${Math.floor(hrs / 24)}d trước`;
}

export function slugify(str: string): string {
  if (!str) return '';
  return str
    .toLowerCase()
    .normalize('NFD') // Phân rã chữ có dấu thành ký tự cơ bản và dấu
    .replace(/[\u0300-\u036f]/g, '') // Loại bỏ các dấu
    .replace(/đ/g, 'd')
    .replace(/[^a-z0-9\s-]/g, '') // Loại bỏ ký tự đặc biệt
    .trim()
    .replace(/\s+/g, '-') // Thay khoảng trắng bằng gạch ngang
    .replace(/-+/g, '-'); // Gộp các gạch ngang liên tiếp
}

/**
 * Elite V2.2: Universal Product Name Sanitizer
 * Removes messy internal separators and trailing punctuation/noise.
 * Essential for clean UI truncation.
 */
export function trimProductName(name: string): string {
  if (!name) return '';
  return name
    .replace(/\s+[\-\.\|\/]+\s+/g, ' ') // Replace " - ", " | ", etc with space
    .replace(/[^a-zA-Z0-9\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]+$/, '') // Multi-language alphanumeric strip
    .replace(/\s+/g, ' ')
    .trim();
}
