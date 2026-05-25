<script lang="ts">
  import Phone from "@lucide/svelte/icons/phone";
  import MessageCircle from "@lucide/svelte/icons/message-circle";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Trash from "@lucide/svelte/icons/trash";
  import Mail from "@lucide/svelte/icons/mail";
  
  export interface SessionSummary {
    session_id: string;
    customer_name: string | null;
    customer_phone: string | null;
    product_slug: string | null;
    message_count: number;
    last_intent: string | null;
    last_message_at: string | null;
    is_takeover?: boolean;
    is_high_intent?: boolean;
    is_online?: boolean;
    is_unread?: boolean;
    is_trash?: boolean;
  }

  interface Props {
    sessions: SessionSummary[];
    selectedSessionId: string | null;
    isLoading: boolean;
    activeFilter: "all" | "unread" | "read" | "trash";
    onSelect: (id: string) => void;
    onFilterChange: (filter: "all" | "unread" | "read" | "trash") => void;
    onToggleRead: (id: string, currentlyUnread: boolean) => void;
    onMoveToTrash: (id: string) => void;
    onRestore: (id: string) => void;
    onHardDelete: (id: string) => void;
  }

  let { 
    sessions, 
    selectedSessionId, 
    isLoading, 
    activeFilter, 
    onSelect, 
    onFilterChange, 
    onToggleRead, 
    onMoveToTrash, 
    onRestore, 
    onHardDelete 
  }: Props = $props();

  let unreadCount = $derived(sessions.filter(s => s.is_unread).length);

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    const now = new Date();
    
    const dDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    const diffTime = nowDate.getTime() - dDate.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
    } else if (diffDays === 1) {
      return "Hôm qua";
    } else if (diffDays > 1 && diffDays <= 7) {
      return `${diffDays} ngày trước`;
    } else {
      return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
    }
  }
</script>

<aside class="w-full h-full overflow-y-auto custom-scrollbar flex flex-col shrink-0 border-r border-white/5 bg-white/[0.01]">
  <!-- Zalo-style Filter Tabs thưa sếp -->
  <div class="p-3 border-b border-white/5 flex gap-1.5 shrink-0 bg-white/[0.02]">
    <button 
      onclick={() => onFilterChange("all")} 
      class="flex-1 py-1.5 rounded-lg text-[10px] font-bold tracking-wider uppercase transition-all {activeFilter === 'all' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.1)]' : 'text-white/40 hover:text-white border border-transparent'}"
    >
      Tất cả
    </button>
    <button 
      onclick={() => onFilterChange("unread")} 
      class="flex-1 py-1.5 rounded-lg text-[10px] font-bold tracking-wider uppercase transition-all relative {activeFilter === 'unread' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.1)]' : 'text-white/40 hover:text-white border border-transparent'}"
    >
      Chưa đọc
      {#if unreadCount > 0}
        <span class="absolute top-1 right-1 flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-cyan-400"></span>
        </span>
      {/if}
    </button>
    <button 
      onclick={() => onFilterChange("read")} 
      class="flex-1 py-1.5 rounded-lg text-[10px] font-bold tracking-wider uppercase transition-all {activeFilter === 'read' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.1)]' : 'text-white/40 hover:text-white border border-transparent'}"
    >
      Đã đọc
    </button>
    <button 
      onclick={() => onFilterChange("trash")} 
      class="flex-1 py-1.5 rounded-lg text-[10px] font-bold tracking-wider uppercase transition-all {activeFilter === 'trash' ? 'bg-red-500/20 text-red-400 border border-red-500/30 shadow-[0_0_10px_rgba(239,68,68,0.1)]' : 'text-white/40 hover:text-white border border-transparent'}"
    >
      Rác
    </button>
  </div>

  {#if isLoading && sessions.length === 0}
    <div class="p-8 text-center text-white/20 text-xs">Đang tải phiên...</div>
  {:else if sessions.length === 0}
    <div class="p-8 text-center text-white/20 text-xs">Không tìm thấy hội thoại nào</div>
  {:else}
    {#each sessions as session (session.session_id)}
      <div class="group/item relative">
        <button 
          onclick={() => onSelect(session.session_id)}
          class="w-full text-left p-4 border-b border-white/5 hover:bg-white/5 transition-all relative {selectedSessionId === session.session_id ? 'bg-cyan-500/10 border-l-2 border-l-cyan-500' : ''} {session.is_high_intent ? 'high-intent-glow' : ''} {session.is_unread ? 'bg-white/[0.02]' : ''}"
        >
          <!-- Unread indicator dot -->
          {#if session.is_unread}
            <div class="absolute left-1.5 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)] z-10"></div>
          {/if}

          <div class="flex justify-between items-center mb-1 pl-1 gap-2">
            <!-- Left: Online Status + Name -->
            <span class="truncate transition-all duration-300 {session.is_high_intent ? 'text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.4)]' : 'text-white/90'} {session.is_unread ? 'font-black text-white' : 'font-medium'} flex items-center gap-1.5 min-w-0">
              <span class="shrink-0 inline-block w-1.5 h-1.5 rounded-full {session.is_online ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.6)]' : 'bg-white/20'}"></span>
              <span class="truncate">{session.customer_name || "Khách ẩn danh"}</span>
            </span>

            <!-- Right: Mute/High Badges + Time inline -->
            <div class="flex items-center gap-1.5 shrink-0 select-none">
              {#if session.is_takeover}
                <span class="text-[7px] font-bold px-1.5 py-0.5 bg-yellow-500/20 text-yellow-500 rounded border border-yellow-500/30 tracking-wider whitespace-nowrap font-mono">MUTE</span>
              {/if}
              {#if session.is_high_intent}
                <div class="flex items-center gap-1 p-1 rounded border border-cyan-500/20 bg-cyan-500/10 anim-pulse-cyan shrink-0">
                   <span class="flex h-1.5 w-1.5 relative">
                     <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                     <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-500"></span>
                   </span>
                   <span class="text-[7px] font-black text-cyan-400 uppercase tracking-wider leading-none">High</span>
                </div>
              {/if}
              <span class="text-[9px] text-white/30 whitespace-nowrap">{formatDate(session.last_message_at)}</span>
            </div>
          </div>
          
          <div class="flex items-center gap-3 text-[10px] text-white/40 pl-1">
            {#if session.customer_phone}
              <span class="flex items-center gap-1"><Phone class="w-2.5 h-2.5" /> {session.customer_phone}</span>
            {/if}
            <span class="flex items-center gap-1"><MessageCircle class="w-2.5 h-2.5" /> {session.message_count}</span>
          </div>
          
          {#if session.last_intent}
            <div class="mt-1.5 flex gap-1 pl-1">
              <span class="text-[8px] px-1.5 py-0.5 bg-white/5 rounded border border-white/10 text-white/50 uppercase tracking-wider font-mono font-bold">{session.last_intent}</span>
            </div>
          {/if}
        </button>

        <!-- Zalo-style Hover Action Buttons thưa sếp -->
        <div class="absolute right-2 bottom-2.5 hidden group-hover/item:flex items-center gap-1 bg-zinc-950/90 border border-white/10 rounded-lg p-1 z-20 backdrop-blur-md shadow-[0_4px_12px_rgba(0,0,0,0.5)]">
          {#if activeFilter === 'trash'}
            <button 
              onclick={(e) => { e.stopPropagation(); onRestore(session.session_id); }} 
              title="Khôi phục cuộc trò chuyện" 
              class="p-1 hover:bg-white/10 rounded text-green-400 transition-colors"
            >
              <RotateCcw class="w-3.5 h-3.5" />
            </button>
            <button 
              onclick={(e) => { e.stopPropagation(); onHardDelete(session.session_id); }} 
              title="Xóa vĩnh viễn" 
              class="p-1 hover:bg-white/10 rounded text-red-500 transition-colors"
            >
              <Trash class="w-3.5 h-3.5" />
            </button>
          {:else}
            <button 
              onclick={(e) => { e.stopPropagation(); onToggleRead(session.session_id, !!session.is_unread); }} 
              title={session.is_unread ? "Đánh dấu đã đọc" : "Đánh dấu chưa đọc"} 
              class="p-1 hover:bg-white/10 rounded text-cyan-400 transition-colors"
            >
              <Mail class="w-3.5 h-3.5" />
            </button>
            <button 
              onclick={(e) => { e.stopPropagation(); onMoveToTrash(session.session_id); }} 
              title="Đưa vào thùng rác" 
              class="p-1 hover:bg-white/10 rounded text-red-400 transition-colors"
            >
              <Trash class="w-3.5 h-3.5" />
            </button>
          {/if}
        </div>
      </div>
    {/each}
  {/if}
</aside>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.15); }
  .high-intent-glow {
    background: linear-gradient(90deg, rgba(6, 182, 212, 0.08) 0%, transparent 100%);
    box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.1), 0 0 15px rgba(6, 182, 212, 0.05);
    border-right: 3px solid rgba(6, 182, 212, 0.4);
  }
  @keyframes pulse-cyan {
    0% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.3); }
    70% { box-shadow: 0 0 0 5px rgba(6, 182, 212, 0); }
    100% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0); }
  }
  .anim-pulse-cyan { animation: pulse-cyan 2.5s infinite; }
</style>
