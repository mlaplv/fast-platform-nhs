<script lang="ts">
  import { slide } from "svelte/transition";
  import Phone from "lucide-svelte/icons/phone";
  import Tag from "lucide-svelte/icons/tag";
  import Lock from "lucide-svelte/icons/lock";
  import Unlock from "lucide-svelte/icons/unlock";
  import Send from "lucide-svelte/icons/send";
  import ShieldAlert from "lucide-svelte/icons/shield-alert";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import RotateCcw from "lucide-svelte/icons/rotate-ccw";
  import Copy from "lucide-svelte/icons/copy";
  import Quote from "lucide-svelte/icons/quote";
  import X from "lucide-svelte/icons/x";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import MessageCircle from "lucide-svelte/icons/message-circle";
  
  interface MessageView {
    id: string; role: "user" | "assistant"; content: string; intent: string | null; created_at: string | null; is_revoked?: boolean;
  }
  interface SessionDetail {
    session_id: string; customer_name: string | null; customer_phone: string | null; product_slug: string | null; messages: MessageView[]; is_takeover: boolean; is_online: boolean;
  }

  interface Props {
    session: SessionDetail | null;
    isLoading: boolean;
    isTakeover: boolean;
    isSending: boolean;
    manualMessage: string;
    quotedMessage: MessageView | null;
    onToggleTakeover: () => void;
    onSendMessage: () => void;
    onRevokeMessage: (id: string) => void;
    onCopyMessage: (content: string) => void;
    onQuoteMessage: (msg: MessageView) => void;
    onClearQuote: () => void;
    onUpdateMessage: (v: string) => void;
  }

  let { session, isLoading, isTakeover, isSending, manualMessage, quotedMessage, 
        onToggleTakeover, onSendMessage, onRevokeMessage, onCopyMessage, onQuoteMessage, onClearQuote, onUpdateMessage }: Props = $props();

  let chatScrollRef: HTMLDivElement | null = $state(null);

  $effect(() => {
    if (session && chatScrollRef) {
      setTimeout(() => { chatScrollRef?.scrollTo({ top: chatScrollRef.scrollHeight, behavior: "smooth" }); }, 50);
    }
  });

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" });
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  }
</script>

<main class="flex-1 flex flex-col bg-black/20 overflow-hidden select-text h-full min-w-0 min-h-0">
  {#if session}
    <div class="p-4 bg-white/5 border-b border-white/10 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center font-bold text-white">
          {(session.customer_name || "K")[0]}
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="font-bold text-white/90">{session.customer_name || "Khách ẩn danh"}</h3>
            {#if session.is_online}<span class="text-[9px] px-1.5 py-0.5 bg-green-500/20 text-green-400 rounded-full border border-green-500/30 font-bold animate-pulse">ONLINE</span>
            {:else}<span class="text-[9px] px-1.5 py-0.5 bg-white/5 text-white/40 rounded-full border border-white/10 font-bold">OFFLINE</span>{/if}
          </div>
          <div class="text-xs text-white/40 flex gap-3">
            {#if session.customer_phone}<span class="flex items-center gap-1"><Phone class="w-3 h-3" /> {session.customer_phone}</span>{/if}
            {#if session.product_slug}<span class="flex items-center gap-1"><Tag class="w-3 h-3" /> SP: {session.product_slug}</span>{/if}
          </div>
        </div>
      </div>
      <button onclick={onToggleTakeover} class="flex items-center gap-2 px-3 py-1.5 {isTakeover ? 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30' : 'bg-white/5 text-white/40 border-white/10'} border rounded-lg text-xs font-bold transition-all">
        {#if isTakeover}<Lock class="w-3.5 h-3.5" /> Chặn Helen{:else}<Unlock class="w-3.5 h-3.5" /> Thả Helen{/if}
      </button>
    </div>

    <div class="flex-1 overflow-y-auto overflow-x-hidden p-6 space-y-4 custom-scrollbar" bind:this={chatScrollRef}>
      {#each session.messages as msg}
        <div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'} w-full">
          <div class="max-w-[80%] group relative">
            <div class="{msg.role === 'user' ? 'bg-cyan-600/20 border border-cyan-500/30 rounded-tr-none' : 'bg-white/10 border border-white/10 rounded-tl-none'} transition-all p-4 rounded-2xl {msg.is_revoked ? 'opacity-40 grayscale' : ''}">
              <div class="text-[9px] uppercase tracking-widest text-white/30 mb-1 flex justify-between gap-10">
                <span>{msg.role === 'user' ? 'KHÁCH HÀNG' : 'HELEN AI'}</span>
                <span>{msg.is_revoked ? '[ĐÃ THU HỒI]' : ''} {formatDate(msg.created_at)}</span>
              </div>
              <p class="text-sm leading-relaxed whitespace-pre-wrap {msg.is_revoked ? 'italic line-through' : ''}">{msg.content}</p>
              {#if msg.intent}<div class="mt-2 text-[8px] text-cyan-400/50 uppercase font-mono">INTENT: {msg.intent}</div>{/if}
            </div>
            
            <div class="absolute {msg.role === 'user' ? 'right-full mr-2' : 'left-full ml-2'} bottom-0 opacity-0 group-hover:opacity-100 transition-all z-20">
              <div class="flex items-center gap-0.5 bg-zinc-900 border border-white/10 rounded-full p-0.5 shadow-xl">
                 <button onclick={() => onQuoteMessage(msg)} class="p-2 text-white/40 hover:text-cyan-400"><Quote class="w-3 h-3" /></button>
                 <button onclick={() => onCopyMessage(msg.content)} class="p-2 text-white/40 hover:text-white"><Copy class="w-3 h-3" /></button>
                 <button onclick={() => onRevokeMessage(msg.id)} class="p-2 text-white/40 hover:text-red-400">
                    {#if msg.is_revoked}<RotateCcw class="w-3 h-3" />{:else}<Trash2 class="w-3 h-3" />{/if}
                 </button>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>

    <div class="p-4 bg-black/40 border-t border-white/10 backdrop-blur-xl shrink-0 relative">
      {#if quotedMessage}
        <div transition:slide={{ axis: 'y' }} class="absolute bottom-full left-0 right-0 bg-white/5 backdrop-blur-2xl border-t border-white/10 p-3 flex items-center justify-between z-10">
          <div class="flex items-center gap-3"><div class="w-1 h-8 bg-cyan-500 rounded-full"></div><div>
            <span class="text-[10px] font-bold text-cyan-400 uppercase">Trả lời {quotedMessage.role === 'assistant' ? 'Helen AI' : 'Khách'}</span>
            <p class="text-xs text-white/50 truncate max-w-md">{quotedMessage.content}</p>
          </div></div>
          <button onclick={onClearQuote} class="p-2 text-white/40 hover:text-white"><X class="w-4 h-4" /></button>
        </div>
      {/if}
      <div class="relative">
        <textarea bind:value={manualMessage} onkeydown={handleKeydown} oninput={(e) => onUpdateMessage(e.currentTarget.value)}
          placeholder={isTakeover ? "Nhân Enter để gửi..." : "Bật 'Chặn Helen' để chát..."} disabled={!isTakeover}
          class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white resize-none min-h-[50px] {isTakeover ? 'opacity-100' : 'opacity-40'}"></textarea>
        <button onclick={onSendMessage} disabled={!isTakeover || !manualMessage.trim() || isSending} class="absolute right-4 bottom-4 p-2 bg-cyan-500/20 text-cyan-400 rounded-lg border border-cyan-500/30">
          <Send class="w-4 h-4" />
        </button>
      </div>
    </div>
  {:else if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center text-white/20"><RefreshCw class="animate-spin mb-4" /><p>Đang tải...</p></div>
  {:else}
    <div class="flex-1 flex flex-col items-center justify-center text-white/10 text-center"><MessageCircle class="w-20 h-20 mb-6 opacity-20" /><h3 class="text-lg font-bold">Chọn hội thoại</h3></div>
  {/if}
</main>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(6, 182, 212, 0.5); }
</style>
