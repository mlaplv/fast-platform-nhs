<script lang="ts">
  import { AlertTriangle, X, Eye } from "lucide-svelte";

  let {
    blockers,
    onClose,
    onViewDetails
  }: {
    blockers: Array<{ label: string; current: string; required: string; tab: 'copyright' | 'seo' | 'ai' }>;
    onClose: () => void;
    onViewDetails: (tab: 'copyright' | 'seo' | 'ai') => void;
  } = $props();

  const tabColor: Record<string, string> = {
    copyright: 'text-orange-400 border-orange-400/30 bg-orange-400/10',
    seo: 'text-blue-400 border-blue-400/30 bg-blue-400/10',
    ai: 'text-purple-400 border-purple-400/30 bg-purple-400/10'
  };

  const stepGuide: Record<string, string[]> = {
    copyright: [
      'Xem đoạn được tô màu đỏ trong bài (annotations)',
      'Viết lại hoặc dùng nút ✦ Auto-Fix để sửa đoạn vi phạm',
      'Nhấn ↻ Chạy lại Check COPYRIGHT để cập nhật điểm'
    ],
    seo: [
      'Mở tab SEO → xem chi tiết signal nào bị điểm thấp',
      'Bổ sung từ khóa, heading H2/H3, hoặc tăng độ dài bài',
      'Nhấn ↻ Chạy lại SEO để cập nhật điểm'
    ],
    ai: [
      'Mở tab AI MOD → xem gợi ý GEO Readiness',
      'Thêm định nghĩa chuyên ngành, trích dẫn, cấu trúc rõ ràng',
      'Nhấn ↻ Chạy lại AI MOD để cập nhật điểm'
    ]
  };
</script>

<!-- Overlay backdrop -->
<div
  class="fixed inset-0 z-[200000] flex items-center justify-center p-4"
  style="background: rgba(0,0,0,0.8); backdrop-filter: blur(8px);"
  role="dialog"
  aria-modal="true"
  aria-label="Cảnh báo chưa đủ điều kiện duyệt"
>
  <div class="relative w-full max-w-md rounded-2xl border border-red-500/20 bg-[#0f0b14] shadow-2xl overflow-hidden">
    <!-- Top accent bar -->
    <div class="h-0.5 w-full bg-gradient-to-r from-red-500/60 via-orange-500/60 to-yellow-500/60"></div>

    <!-- Header -->
    <div class="flex items-start gap-3 p-5 pb-3">
      <div class="w-9 h-9 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center shrink-0 mt-0.5">
        <AlertTriangle size={18} class="text-red-400" />
      </div>
      <div class="flex-1">
        <h3 class="text-[13px] font-black text-white uppercase tracking-wider">Không thể Duyệt & Tiếp tục</h3>
        <p class="text-[10px] text-white/40 mt-0.5">Bài viết chưa đạt ngưỡng chất lượng bắt buộc.</p>
      </div>
      <button
        onclick={onClose}
        class="w-7 h-7 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors shrink-0"
        aria-label="Đóng"
      >
        <X size={14} class="text-white/40" />
      </button>
    </div>

    <!-- Blockers list -->
    <div class="px-5 flex flex-col gap-2">
      {#each blockers as blocker}
        <div class="flex items-start gap-3 p-3 rounded-xl border {tabColor[blocker.tab]} border-opacity-30">
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-2">
              <span class="text-[10px] font-black uppercase tracking-wider">{blocker.label}</span>
              <span class="text-[9px] font-bold opacity-70">{blocker.current} / cần {blocker.required}</span>
            </div>
            <div class="mt-2 flex flex-col gap-1">
              {#each stepGuide[blocker.tab] as step, i}
                <p class="text-[8px] text-white/40 flex gap-1.5">
                  <span class="font-black opacity-60 shrink-0">{i + 1}.</span>
                  {step}
                </p>
              {/each}
            </div>
          </div>
          <button
            onclick={() => onViewDetails(blocker.tab)}
            class="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 hover:bg-white/10 transition-colors shrink-0 mt-0.5"
            title="Xem chi tiết lỗi"
          >
            <Eye size={11} class="text-white/40" />
            <span class="text-[8px] text-white/40 font-bold">Chi tiết</span>
          </button>
        </div>
      {/each}
    </div>

    <!-- Footer -->
    <div class="p-5 pt-4">
      <button
        onclick={onClose}
        class="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-[10px] font-black uppercase tracking-widest transition-all border border-white/10"
      >
        Đã hiểu — Quay lại chỉnh sửa
      </button>
    </div>
  </div>
</div>
