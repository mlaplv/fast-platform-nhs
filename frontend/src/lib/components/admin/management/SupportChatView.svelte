<script lang="ts">
  import { slide } from "svelte/transition";
  import Phone from "@lucide/svelte/icons/phone";
  import Tag from "@lucide/svelte/icons/tag";
  import Lock from "@lucide/svelte/icons/lock";
  import Unlock from "@lucide/svelte/icons/unlock";
  import Send from "@lucide/svelte/icons/send";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Copy from "@lucide/svelte/icons/copy";
  import Quote from "@lucide/svelte/icons/quote";
  import X from "@lucide/svelte/icons/x";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import MessageCircle from "@lucide/svelte/icons/message-circle";
  
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
  let textareaRef: HTMLTextAreaElement | null = $state(null);

  $effect(() => {
    if (session && chatScrollRef) {
      setTimeout(() => { chatScrollRef?.scrollTo({ top: chatScrollRef.scrollHeight, behavior: "smooth" }); }, 50);
    }
  });

  $effect(() => {
    if (isTakeover && textareaRef) {
      // Focus instantly when taking over the chat
      textareaRef.focus();
    }
  });

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  }

  function getDateGroupLabel(dateStr: string | null): string {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    const now = new Date();
    
    const dDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    const diffTime = nowDate.getTime() - dDate.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return "Hôm nay";
    } else if (diffDays === 1) {
      return "Hôm qua";
    } else if (diffDays > 1 && diffDays <= 7) {
      return `${diffDays} ngày trước`;
    } else {
      return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
    }
  }

  // Reactive derived grouping (Svelte 5 Rune thưa sếp)
  let groupedMessages = $derived.by(() => {
    if (!session || !session.messages) return [];
    const items: ({ type: 'date'; label: string } | { type: 'message'; message: MessageView })[] = [];
    let lastLabel = "";
    
    for (const msg of session.messages) {
      const label = getDateGroupLabel(msg.created_at);
      if (label && label !== lastLabel) {
        items.push({ type: 'date', label });
        lastLabel = label;
      }
      items.push({ type: 'message', message: msg });
    }
    return items;
  });

  // Helper to parse content of quoted message
  function parseQuotedContent(content: string) {
    if (!content) return { text: "", imageUrl: null };
    // 1. Detect markdown image: ![alt](url)
    const mdImgRegex = /!\[.*?\]\((.*?)\)/;
    const mdMatch = content.match(mdImgRegex);
    if (mdMatch) {
      const imageUrl = mdMatch[1];
      const textWithoutImg = content.replace(mdImgRegex, "").trim() || "[Hình ảnh]";
      return { text: textWithoutImg, imageUrl };
    }
    // 2. Detect raw URL that is an image
    const rawUrlRegex = /(https?:\/\/[^\s]+?\.(?:png|jpg|jpeg|gif|webp|svg)(?:\?[^\s]*)?)/i;
    const rawMatch = content.match(rawUrlRegex);
    if (rawMatch) {
      const imageUrl = rawMatch[1];
      const textWithoutImg = content.replace(rawUrlRegex, "").trim() || "[Hình ảnh]";
      return { text: textWithoutImg, imageUrl };
    }
    return { text: content, imageUrl: null };
  }

  interface ParsedMessage {
    quoteAuthor: string | null;
    quoteText: string | null;
    quoteImageUrl: string | null;
    mainContent: string;
    mainImageUrl: string | null;
  }

  // Helper to parse full message content (extract quotes and main content images)
  function parseMessageContent(content: string): ParsedMessage {
    if (!content) return { quoteAuthor: null, quoteText: null, quoteImageUrl: null, mainContent: "", mainImageUrl: null };

    // Detect if there is a quoted section: > Author: QuotedText\n\nMainText
    const quoteRegex = /^>\s*([^:\n]+):\s*([\s\S]+?)\n\n([\s\S]*)$/;
    const match = content.match(quoteRegex);

    let quoteAuthor: string | null = null;
    let quoteText: string | null = null;
    let quoteImageUrl: string | null = null;
    let remainingContent = content;

    if (match) {
      quoteAuthor = match[1].trim();
      const rawQuoteContent = match[2].trim();
      remainingContent = match[3].trim();

      const parsedQuote = parseQuotedContent(rawQuoteContent);
      quoteText = parsedQuote.text;
      quoteImageUrl = parsedQuote.imageUrl;
    }

    // Now detect if the main content itself has a single image or multiple
    const parsedMain = parseQuotedContent(remainingContent);

    return {
      quoteAuthor,
      quoteText,
      quoteImageUrl,
      mainContent: parsedMain.text,
      mainImageUrl: parsedMain.imageUrl
    };
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
      {#each groupedMessages as item}
        {#if item.type === 'date'}
          <div class="flex justify-center my-4">
            <span class="text-[9px] px-3 py-1 bg-white/5 border border-white/10 rounded-full text-white/40 uppercase tracking-widest font-semibold font-mono">
              {item.label}
            </span>
          </div>
        {:else}
          {@const msg = item.message}
          {@const parsed = parseMessageContent(msg.content)}
          <div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'} w-full animate-fade-in">
            <div class="max-w-[85%] sm:max-w-[70%] group relative">
              <div class="{msg.role === 'user' ? 'bg-cyan-600/10 border border-cyan-500/20 rounded-tr-none' : 'bg-white/5 border border-white/5 rounded-tl-none'} transition-all p-4 rounded-2xl {msg.is_revoked ? 'opacity-40 grayscale' : ''}">
                <div class="text-[9px] tracking-widest text-white/30 mb-1.5 flex justify-between gap-10">
                  <span>{msg.role === 'user' ? 'KHÁCH HÀNG' : 'HELEN AI'}</span>
                  <span>{msg.is_revoked ? '[ĐÃ THU HỒI]' : ''} {formatDate(msg.created_at)}</span>
                </div>
                
                {#if !msg.is_revoked}
                  <!-- Render Nested Quoted Message (Zalo Style) -->
                  {#if parsed.quoteText}
                    <div class="mb-3 p-2 bg-black/35 rounded-lg border-l-[3px] border-cyan-500/80 flex items-center gap-2 max-w-full overflow-hidden select-none">
                      {#if parsed.quoteImageUrl}
                        <img src={parsed.quoteImageUrl} alt="Quote thumbnail" class="w-8 h-8 rounded object-cover border border-white/10 shrink-0" />
                      {/if}
                      <div class="min-w-0 flex-1">
                        <span class="text-[10px] font-bold text-cyan-400 block leading-tight">{parsed.quoteAuthor}</span>
                        <p class="text-xs text-white/50 truncate leading-snug">
                          {#if parsed.quoteImageUrl && parsed.quoteText === "[Hình ảnh]"}
                            <span class="text-cyan-500/90 font-medium">[Hình ảnh]</span>
                          {:else if parsed.quoteImageUrl}
                            <span class="text-cyan-500/90 font-medium">[Hình ảnh]</span> {parsed.quoteText}
                          {:else}
                            {parsed.quoteText}
                          {/if}
                        </p>
                      </div>
                    </div>
                  {/if}

                  <!-- Render Main Message Text -->
                  {#if parsed.mainContent && parsed.mainContent !== "[Hình ảnh]"}
                    <p class="text-sm leading-relaxed whitespace-pre-wrap">{parsed.mainContent}</p>
                  {/if}

                  <!-- Render Main Message Image Attachment (Zalo Style Image bubble) -->
                  {#if parsed.mainImageUrl}
                    <div class="mt-2 relative rounded-xl overflow-hidden border border-white/10 max-w-xs group/img shadow-md bg-black/20">
                      <a href={parsed.mainImageUrl} target="_blank" rel="noopener noreferrer" class="block cursor-zoom-in">
                        <img src={parsed.mainImageUrl} alt="Attachment" class="w-full max-h-60 object-cover transition-transform duration-300 group-hover/img:scale-[1.03]" loading="lazy" />
                      </a>
                    </div>
                  {/if}
                {:else}
                  <p class="text-sm leading-relaxed whitespace-pre-wrap italic line-through opacity-60">{msg.content}</p>
                {/if}

                {#if msg.intent && !msg.is_revoked}<div class="mt-2 text-[8px] text-cyan-400/40 font-mono tracking-wider">INTENT: {msg.intent}</div>{/if}
              </div>
              
              <div class="absolute {msg.role === 'user' ? 'right-full mr-2' : 'left-full ml-2'} bottom-0 opacity-0 group-hover:opacity-100 transition-all z-20">
                <div class="flex items-center gap-0.5 bg-zinc-950/90 border border-white/10 rounded-full p-0.5 shadow-2xl backdrop-blur-md">
                   <button onclick={() => onQuoteMessage(msg)} class="p-2 text-white/40 hover:text-cyan-400" title="Trích dẫn"><Quote class="w-3 h-3" /></button>
                   <button onclick={() => onCopyMessage(msg.content)} class="p-2 text-white/40 hover:text-white" title="Sao chép"><Copy class="w-3 h-3" /></button>
                   {#if !msg.is_revoked}
                     <button onclick={() => onRevokeMessage(msg.id)} class="p-2 text-white/40 hover:text-red-400" title="Thu hồi"><Trash2 class="w-3 h-3" /></button>
                   {/if}
                </div>
              </div>
            </div>
          </div>
        {/if}
      {/each}
    </div>

    <div class="p-4 bg-black/40 border-t border-white/10 backdrop-blur-xl shrink-0">
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div 
        onclick={() => { if (!isTakeover) onToggleTakeover(); }}
        class="relative flex flex-col bg-white/5 border border-white/10 rounded-xl overflow-hidden {!isTakeover ? 'cursor-pointer hover:bg-white/10 transition-colors' : ''}">
        {#if quotedMessage}
          {@const parsedCompose = parseQuotedContent(quotedMessage.content)}
          <div transition:slide={{ axis: 'y' }} class="bg-white/[0.02] border-b border-white/10 p-3 pl-4 flex items-center justify-between z-10 relative">
            <div class="flex items-center gap-3 min-w-0 flex-1 border-l-2 border-cyan-500 pl-3">
              {#if parsedCompose.imageUrl}
                <img src={parsedCompose.imageUrl} alt="Quote composer thumbnail" class="w-9 h-9 rounded object-cover border border-white/10 shrink-0" />
              {/if}
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5 text-cyan-400 block leading-tight">
                  <Quote class="w-3 h-3 shrink-0" />
                  <span class="text-[11px] font-semibold">Trả lời {quotedMessage.role === 'assistant' ? 'Helen AI' : 'Khách'}</span>
                </div>
                <p class="text-xs text-white/50 truncate pr-4 mt-0.5 leading-normal">
                  {#if parsedCompose.imageUrl && parsedCompose.text === "[Hình ảnh]"}
                    <span class="text-cyan-400/80 font-medium">[Hình ảnh]</span>
                  {:else if parsedCompose.imageUrl}
                    <span class="text-cyan-400/80 font-medium">[Hình ảnh]</span> {parsedCompose.text}
                  {:else}
                    {parsedCompose.text}
                  {/if}
                </p>
              </div>
            </div>
            <button onclick={(e) => { e.stopPropagation(); onClearQuote(); }} class="p-1.5 text-white/40 hover:text-white rounded-full hover:bg-white/5 shrink-0 active:scale-95 transition-all"><X class="w-4 h-4" /></button>
          </div>
        {/if}
        <div class="relative">
          <textarea bind:this={textareaRef} bind:value={manualMessage} onkeydown={handleKeydown} oninput={(e) => onUpdateMessage(e.currentTarget.value)}
            placeholder={isTakeover ? "Nhập nội dung tin nhắn..." : "Bật 'Chặn Helen' để chat..."} disabled={!isTakeover}
            class="w-full bg-transparent border-0 focus:ring-0 focus:outline-none px-4 py-3 pb-12 text-sm text-white resize-none min-h-[60px] {isTakeover ? 'opacity-100' : 'opacity-40'}"></textarea>
          <button onclick={onSendMessage} disabled={!isTakeover || !manualMessage.trim() || isSending} class="absolute right-4 bottom-4 p-2 bg-cyan-500/20 text-cyan-400 rounded-lg border border-cyan-500/30 transition-all hover:bg-cyan-500/30 active:scale-95">
            <Send class="w-4 h-4" />
          </button>
        </div>
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
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(6, 182, 212, 0.3); }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
  }
</style>
