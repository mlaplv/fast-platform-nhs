<script lang="ts">
  import Phone from "lucide-svelte/icons/phone";
  import MessageCircle from "lucide-svelte/icons/message-circle";
  
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
  }

  interface Props {
    sessions: SessionSummary[];
    selectedSessionId: string | null;
    isLoading: boolean;
    onSelect: (id: string) => void;
  }

  let { sessions, selectedSessionId, isLoading, onSelect }: Props = $props();

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleString("vi-VN", {
      hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit",
    });
  }
</script>

<aside class="w-full h-full overflow-y-auto custom-scrollbar flex flex-col shrink-0">
  {#if isLoading && sessions.length === 0}
    <div class="p-8 text-center text-white/20">Đang tải phiên...</div>
  {:else if sessions.length === 0}
    <div class="p-8 text-center text-white/20">Không tìm thấy hội thoại nào</div>
  {:else}
    {#each sessions as session (session.session_id)}
      <button 
        onclick={() => onSelect(session.session_id)}
        class="w-full text-left p-4 border-b border-white/5 hover:bg-white/5 transition-all relative {selectedSessionId === session.session_id ? 'bg-cyan-500/10 border-l-2 border-l-cyan-500' : ''} {session.is_high_intent ? 'high-intent-glow' : ''}"
      >
        {#if session.is_high_intent}
          <div class="absolute top-2 right-2 flex items-center gap-1.5 p-1 rounded-md bg-cyan-500/10 border border-cyan-500/20 anim-pulse-cyan">
             {#if session.is_takeover}
               <span class="text-[7px] font-bold px-1 py-0.5 bg-yellow-500/20 text-yellow-500 rounded border border-yellow-500/30 uppercase tracking-tighter mr-1 anim-pulse">AI SILENCED</span>
             {/if}
             <span class="flex h-2 w-2">
               <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
               <span class="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
             </span>
             <span class="text-[8px] font-black text-cyan-400 uppercase tracking-widest leading-none">High Intent</span>
          </div>
        {:else if session.is_takeover}
          <div class="absolute top-2 right-2">
            <span class="text-[7px] font-bold px-1 py-0.5 bg-yellow-500/20 text-yellow-500 rounded border border-yellow-500/30 uppercase tracking-tighter">AI SILENCED</span>
          </div>
        {/if}
        
        <div class="flex justify-between items-start mb-1">
          <span class="font-bold truncate mr-2 transition-all duration-300 {session.is_high_intent ? 'text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.4)]' : 'text-white/90'}">
            <span class="inline-block w-2 h-2 rounded-full mr-1.5 {session.is_online ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.6)]' : 'bg-white/20'}"></span>
            {session.customer_name || "Khách ẩn danh"}
          </span>
          <span class="text-[10px] text-white/30 whitespace-nowrap">{formatDate(session.last_message_at)}</span>
        </div>
        
        <div class="flex items-center gap-3 text-xs text-white/50">
          {#if session.customer_phone}
            <span class="flex items-center gap-1"><Phone class="w-3 h-3" /> {session.customer_phone}</span>
          {/if}
          <span class="flex items-center gap-1"><MessageCircle class="w-3 h-3" /> {session.message_count}</span>
        </div>
        
        {#if session.last_intent}
          <div class="mt-2 flex gap-1">
            <span class="text-[9px] px-1.5 py-0.5 bg-white/5 rounded border border-white/10 uppercase tracking-tighter text-white/60">{session.last_intent}</span>
          </div>
        {/if}
      </button>
    {/each}
  {/if}
</aside>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
  .high-intent-glow {
    background: linear-gradient(90deg, rgba(6, 182, 212, 0.15) 0%, transparent 100%);
    box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.2), 0 0 15px rgba(6, 182, 212, 0.15);
    border-right: 3px solid rgba(6, 182, 212, 0.6);
  }
  @keyframes pulse-cyan {
    0% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.4); }
    70% { box-shadow: 0 0 0 6px rgba(6, 182, 212, 0); }
    100% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0); }
  }
  .anim-pulse-cyan { animation: pulse-cyan 2s infinite; }
</style>
