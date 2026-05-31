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
    
    // Elite V2.2 Bulk Operations thưa sếp
    onPurgeTrash: () => Promise<void>;
    onBulkTrash: (ids: string[]) => Promise<void>;
    onBulkRestore: (ids: string[]) => Promise<void>;
    onBulkHardDelete: (ids: string[]) => Promise<void>;
    onBulkToggleRead: (ids: string[], isUnread: boolean) => Promise<void>;
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
    onHardDelete,
    onPurgeTrash,
    onBulkTrash,
    onBulkRestore,
    onBulkHardDelete,
    onBulkToggleRead
  }: Props = $props();

  let unreadCount = $derived(sessions.filter(s => s.is_unread).length);

  // Local Reactive State for Bulk Selection thưa sếp
  let selectedIds = $state<string[]>([]);

  $effect(() => {
    // Clear selection when sessions list or filter tab changes to protect states
    const _ = sessions;
    const __ = activeFilter;
    selectedIds = [];
  });

  let isAllSelected = $derived(sessions.length > 0 && selectedIds.length === sessions.length);
  let isSomeSelected = $derived(selectedIds.length > 0 && selectedIds.length < sessions.length);

  function toggleSelectAll() {
    if (isAllSelected) {
      selectedIds = [];
    } else {
      selectedIds = sessions.map(s => s.session_id);
    }
  }

  function toggleSelectSession(id: string) {
    if (selectedIds.includes(id)) {
      selectedIds = selectedIds.filter(x => x !== id);
    } else {
      selectedIds = [...selectedIds, id];
    }
  }

  async function handlePurgeTrash() {
    await onPurgeTrash();
    selectedIds = [];
  }

  async function handleBulkRestore() {
    await onBulkRestore([...selectedIds]);
    selectedIds = [];
  }

  async function handleBulkHardDelete() {
    await onBulkHardDelete([...selectedIds]);
    selectedIds = [];
  }

  async function handleBulkToggleRead(isUnread: boolean) {
    await onBulkToggleRead([...selectedIds], isUnread);
    selectedIds = [];
  }

  async function handleBulkTrash() {
    await onBulkTrash([...selectedIds]);
    selectedIds = [];
  }

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

<aside class="w-full h-full overflow-hidden flex flex-col shrink-0 border-r border-white/5 bg-white/[0.01]">
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

  <!-- Bulk Actions & Select All Control Panel thưa sếp -->
  <div class="p-3 border-b border-white/5 bg-white/[0.01] flex items-center justify-between shrink-0 text-[10px] text-white/50">
    <div class="flex items-center gap-2">
      <label class="flex items-center cursor-pointer select-none">
        <input 
          type="checkbox" 
          checked={isAllSelected} 
          indeterminate={isSomeSelected}
          onchange={toggleSelectAll}
          class="sr-only" 
        />
        <div class="w-4 h-4 rounded border flex items-center justify-center transition-all {isAllSelected ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400' : isSomeSelected ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-400' : 'border-white/20 bg-white/5 hover:border-white/40'}">
          {#if isAllSelected}
            <svg class="w-2.5 h-2.5 fill-current" viewBox="0 0 20 20"><path d="M0 11l2-2 5 5L18 3l2 2L7 18z"/></svg>
          {:else if isSomeSelected}
            <!-- Indeterminate line -->
            <div class="w-1.5 h-0.5 bg-cyan-400 rounded-full"></div>
          {/if}
        </div>
        <span class="ml-2 font-bold uppercase tracking-wider hover:text-white/80 transition-colors">Chọn tất cả</span>
      </label>
    </div>
    
    <div class="flex items-center gap-1.5">
      <!-- If in trash, show Purge Trash button thưa sếp -->
      {#if activeFilter === 'trash' && sessions.length > 0}
        <button 
          onclick={handlePurgeTrash}
          class="flex items-center gap-1 py-1 px-2.5 rounded bg-red-500/15 hover:bg-red-500/30 text-red-400 border border-red-500/30 font-bold uppercase tracking-wider text-[8px] transition-all hover:scale-105 active:scale-95 shadow-[0_0_12px_rgba(239,68,68,0.15)]"
        >
          <Trash class="w-2.5 h-2.5" />
          Làm sạch Thùng rác
        </button>
      {/if}
    </div>
  </div>


  <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
    {#if isLoading && sessions.length === 0}
    <div class="p-8 text-center text-white/20 text-xs">Đang tải phiên...</div>
  {:else if sessions.length === 0}
    <div class="p-8 text-center text-white/20 text-xs">Không tìm thấy hội thoại nào</div>
  {:else}
    {#each sessions as session (session.session_id)}
      <div class="group/item relative flex items-center border-b border-white/5 hover:bg-white/5 transition-all {selectedSessionId === session.session_id ? 'bg-cyan-500/10 border-l-2 border-l-cyan-500' : ''} {session.is_high_intent ? 'high-intent-glow' : ''} {session.is_unread ? 'bg-white/[0.02]' : ''}">
        <!-- Custom Checkbox thưa sếp -->
        <label class="flex items-center cursor-pointer shrink-0 pl-3.5 py-4 select-none">
          <input 
            type="checkbox" 
            checked={selectedIds.includes(session.session_id)} 
            onchange={() => toggleSelectSession(session.session_id)}
            class="sr-only" 
          />
          <div class="w-4 h-4 rounded border flex items-center justify-center transition-all {selectedIds.includes(session.session_id) ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400' : 'border-white/20 bg-white/5 hover:border-white/40'}">
            {#if selectedIds.includes(session.session_id)}
              <svg class="w-2.5 h-2.5 fill-current" viewBox="0 0 20 20"><path d="M0 11l2-2 5 5L18 3l2 2L7 18z"/></svg>
            {/if}
          </div>
        </label>

        <button 
          onclick={() => onSelect(session.session_id)}
          class="flex-1 text-left p-4 pl-2.5 relative min-w-0"
        >
          <!-- Unread indicator dot -->
          {#if session.is_unread}
            <div class="absolute left-1 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)] z-10"></div>
          {/if}

          <div class="flex justify-between items-center mb-1 pl-1 gap-2 min-w-0">
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
  </div>

  <!-- Floating Bulk Action Bar thưa sếp -->
  {#if selectedIds.length > 0}
    <div class="p-3 bg-zinc-950/95 border-t border-white/10 shrink-0 backdrop-blur-md shadow-[0_-4px_12px_rgba(0,0,0,0.5)] z-30 flex flex-col gap-2 transition-all duration-300">
      <div class="flex justify-between items-center text-[10px] text-white/60 font-bold px-1">
        <span>ĐÃ CHỌN: <span class="text-cyan-400 font-extrabold text-xs">{selectedIds.length}</span> SESSIONS</span>
        <button onclick={() => selectedIds = []} class="hover:text-white text-[9px] uppercase tracking-widest font-black transition-colors">HỦY BỎ</button>
      </div>
      
      <div class="flex gap-1.5">
        {#if activeFilter === 'trash'}
          <button 
            onclick={handleBulkRestore} 
            class="flex-1 py-1.5 rounded bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 text-[9px] font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 active:scale-95 hover:scale-[1.02]"
          >
            <RotateCcw class="w-3 h-3" />
            Khôi phục
          </button>
          <button 
            onclick={handleBulkHardDelete} 
            class="flex-1 py-1.5 rounded bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 text-[9px] font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 active:scale-95 hover:scale-[1.02]"
          >
            <Trash class="w-3 h-3" />
            Xóa vĩnh viễn
          </button>
        {:else}
          <button 
            onclick={() => handleBulkToggleRead(false)} 
            class="flex-1 py-1.5 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 border border-cyan-500/30 text-[9px] font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 active:scale-95 hover:scale-[1.02]"
          >
            <Mail class="w-3 h-3" />
            Đã đọc
          </button>
          <button 
            onclick={() => handleBulkToggleRead(true)} 
            class="flex-1 py-1.5 rounded bg-white/5 hover:bg-white/10 text-white/70 border border-white/10 text-[9px] font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 active:scale-95 hover:scale-[1.02]"
          >
            <Mail class="w-3 h-3" />
            Chưa đọc
          </button>
          <button 
            onclick={handleBulkTrash} 
            class="flex-1 py-1.5 rounded bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 text-[9px] font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 active:scale-95 hover:scale-[1.02]"
          >
            <Trash class="w-3 h-3" />
            Xóa
          </button>
        {/if}
      </div>
    </div>
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
