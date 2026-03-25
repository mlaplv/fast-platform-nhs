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
