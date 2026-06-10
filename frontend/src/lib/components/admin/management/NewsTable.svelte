<script lang="ts">
  import FileText from "@lucide/svelte/icons/file-text";
  import Pencil from "@lucide/svelte/icons/pencil";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import CheckSquare from "@lucide/svelte/icons/check-square";
  import Square from "@lucide/svelte/icons/square";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Eye from "@lucide/svelte/icons/eye";
  import Calendar from "@lucide/svelte/icons/calendar";
  import StarIcon from "@lucide/svelte/icons/star";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import type { Article } from "$lib/types";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

  let {
    articles,
    selectedIds,
    onToggleSelect,
    onToggleSelectAll,
    onEdit,
    onDelete,
    onOpenReviewLab,
    onSchedule,
  } = $props<{
    articles: Article[];
    selectedIds: Set<string>;
    onToggleSelect: (id: string) => void;
    onToggleSelectAll: () => void;
    onEdit: (a: Article) => void;
    onDelete: (id: string | string[]) => void;
    onOpenReviewLab: (article: { id: string; name: string }) => void;
    onSchedule: (a: Article) => void;
  }>();

  const isAllSelected = $derived(articles.length > 0 && articles.every(a => selectedIds.has(a.id)));

  $effect(() => {
    const action = nanobot.commandAction;
    if (action?.entity === "news" || action?.entity === "article") {
      if (action.verb === "edit" && action.args) {
        const target = articles.find(
          (a) =>
            a.id === action.args ||
            a.title.toLowerCase().includes(action.args.toLowerCase())
        );
        if (target && nanobot.consumeCommand("edit", action.entity)) {
          onEdit(target);
        }
      }
      if (action.verb === "delete" && action.args) {
        const target = articles.find(
          (a) =>
            a.id === action.args ||
            a.title.toLowerCase().includes(action.args.toLowerCase())
        );
        if (target && nanobot.consumeCommand("delete", action.entity)) {
          onDelete(target.id);
        }
      }
    }
  });
</script>

<!-- News Table Header -->
<div class="hidden md:grid grid-cols-[40px_minmax(300px,2fr)_1fr_1fr_1fr_100px] gap-4 px-4 py-4 sticky top-0 bg-black/80 border-b border-cyan-500/20 tracking-widest text-[9px] font-extrabold font-mono text-cyan-400 shadow-2xl"
     style="z-index: {Z_INDEX_ADMIN.STICKY_HEADER}; backdrop-filter: blur(16px);">
  <div class="text-center flex justify-center items-center">
    <button
      onclick={(e) => { e.stopPropagation(); onToggleSelectAll(); }}
      class="text-gray-600 hover:text-cyan-400 transition-colors"
      title={isAllSelected ? "Bỏ chọn tất cả" : "Chọn tất cả trang này"}
    >
      {#if isAllSelected}<CheckSquare size={16} />{:else}<Square size={16} />{/if}
    </button>
  </div>
  <div>Tiêu đề bài viết</div>
  <div>Chuyên mục</div>
  <div>Tác giả</div>
  <div>Trạng thái</div>
  <div class="text-right">Hành động</div>
</div>

<div class="flex flex-col flex-1 pb-10">
  <div class="flex flex-col gap-2 md:gap-0 px-2 sm:px-4 md:px-0">
    {#each articles as article (article.id)}
      <div
        class="group relative flex flex-col md:grid md:grid-cols-[40px_minmax(300px,2fr)_1fr_1fr_1fr_100px] md:gap-4 md:items-center bg-[#0a0a0a] md:bg-transparent border border-white/5 md:border-none p-3 sm:p-4 rounded-xl md:rounded-none hover:bg-white/[0.03] transition-colors duration-300"
      >
        <!-- Selection -->
        <div class="absolute top-2 left-2 md:relative md:top-auto md:left-auto md:flex md:justify-center"
             style="z-index: var(--z-surface);">
          <button
            onclick={(e: MouseEvent) => { e.stopPropagation(); onToggleSelect(article.id); }}
            class="text-gray-600 hover:text-cyan-400 transition-colors"
          >
            {#if selectedIds.has(article.id)}<CheckSquare size={16} />{:else}<Square size={16} />{/if}
          </button>
        </div>

        <!-- Thumbnail & Title -->
        <div class="flex items-start md:items-center gap-4 md:pl-0 pl-6 w-full">
          <div
            class="w-14 h-11 md:w-16 md:h-10 rounded-lg bg-zinc-900 border border-white/5 flex items-center justify-center shrink-0 overflow-hidden relative group-hover:border-cyan-500/30 transition-all duration-300"
          >
            {#if article.featuredImage && article.featuredImage.includes('/')}
              <img 
                src={article.featuredImage} 
                alt={article.title}
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 opacity-80 group-hover:opacity-100"
              />
            {:else}
              <div class="w-full h-full bg-gradient-to-br from-cyan-500/10 to-transparent flex items-center justify-center">
                <FileText size={18} class="text-cyan-500/40" />
              </div>
            {/if}
          </div>
          <div class="min-w-0 flex flex-col justify-center flex-1">
            <div class="text-[14px] md:text-[13px] font-bold text-gray-100 truncate group-hover:text-cyan-400 transition-colors tracking-wide">
              {article.title}
            </div>
            <div class="text-[10px] font-mono text-gray-500 mt-1 tracking-[0.2em] flex items-center flex-wrap gap-2">
              {#if article.metadata?.analysis_metrics}
                {@const metrics = article.metadata.analysis_metrics}
                {#if metrics.unique_score !== undefined}
                  <span class="px-1.5 py-0.5 rounded-md bg-orange-500/10 border border-orange-500/30 text-[8px] text-orange-400 font-black shadow-[0_0_10px_rgba(249,115,22,0.1)]" title="Tiêu chí vàng: Copyright Certificate">
                    © {Math.round(metrics.unique_score * 100)}%
                  </span>
                {/if}
                {#if metrics.seo_score !== undefined}
                  <span class="px-1.5 py-0.5 rounded-md bg-blue-500/10 border border-blue-500/30 text-[8px] text-blue-400 font-black shadow-[0_0_10px_rgba(59,130,246,0.1)]" title="Tiêu chí vàng: SEO Certificate">
                    📊 {metrics.seo_score}
                  </span>
                {/if}
                {#if metrics.ai_ready_score !== undefined}
                  <span class="px-1.5 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/30 text-[8px] text-purple-400 font-black shadow-[0_0_10px_rgba(168,85,247,0.1)]" title="Tiêu chí vàng: AI Mod Ready">
                    🤖 {metrics.ai_ready_score}
                  </span>
                {/if}
              {/if}

              <span class="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] text-gray-400 font-black" title="Lượt xem (Views)">
                👁️ {article.views || 0}
              </span>
              <span class="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 text-[8px] text-gray-400 font-black" title="Đánh giá (Reviews)">
                ⭐ {article.review_count || 0}
              </span>

              <span class="md:hidden text-gray-800 ml-1">/</span>
              <span class="md:hidden text-gray-600 font-bold ml-1">{article.category || "Chung"}</span>
            </div>
          </div>
        </div>

        <!-- Category -->
        <div class="hidden md:block text-[10px] font-mono text-gray-500 tracking-widest group-hover:text-gray-300 transition-colors">
          {article.category || "Chung"}
        </div>

        <!-- Author / Views -->
        <div class="hidden md:flex flex-col">
          <div class="text-[10px] font-mono text-gray-400 tracking-widest">
            {article.authorName || article.author || "SYSTEM_CORE"}
          </div>
          <div class="flex items-center gap-1.5 text-[9px] font-mono text-gray-600 mt-0.5">
            <Eye size={10} /> {(article.views || 0).toLocaleString()}
          </div>
        </div>

        <!-- Status -->
        <div class="pl-[72px] md:pl-0 mt-2 md:mt-0">
          <span
            class="px-2.5 py-1 rounded-lg text-[9px] font-bold font-mono tracking-widest inline-flex border {article.status.toLowerCase() === 'published' ? 'text-[#39FF14] border-[#39FF14]/30 bg-[#39FF14]/10' : 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10'}"
          >
            {article.status.toLowerCase() === 'published' ? 'ĐÃ ĐĂNG' : 'BẢN NHÁP'}
          </span>
        </div>

        <!-- Operations -->
        <div class="absolute bottom-3 right-3 md:relative md:bottom-auto md:right-auto md:flex">
          <div class="flex items-center gap-1.5 justify-end md:translate-x-2 md:group-hover:translate-x-0 w-full bg-[#0a0a0a] md:bg-transparent pl-2">
            <a
              href="/{article.slug}.html"
              target="_blank"
              class="p-2 text-cyan-400 hover:text-white transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-cyan-500/20 hover:border-cyan-500/40"
              title="Xem bài viết"
              onclick={(e: MouseEvent) => e.stopPropagation()}
            >
              <ExternalLink size={14} />
            </a>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onOpenReviewLab({ id: article.id, name: article.title }); }}
              class="p-2 text-[#FFD700]/50 md:text-gray-500 hover:text-[#FFD700] transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-[#FFD700]/20"
              title="Review Lab"
              id="news-review-lab-btn-{article.id}"
            >
              <StarIcon size={14} />
            </button>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onSchedule(article); }}
              class="p-2 text-gray-500 hover:text-cyan-400 transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-cyan-500/20"
              title="Đặt lịch đăng bài"
            >
              <Calendar size={14} />
            </button>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onEdit(article); }}
              class="p-2 text-gray-500 hover:text-cyan-400 transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-cyan-500/20"
              title="Sửa bài viết"
            >
              <Pencil size={14} />
            </button>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onDelete(article.id); }}
              class="p-2 text-red-500 md:text-gray-500 hover:text-red-400 transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-red-500/20"
              title="Xóa bài viết"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      </div>
    {/each}
  </div>
</div>
