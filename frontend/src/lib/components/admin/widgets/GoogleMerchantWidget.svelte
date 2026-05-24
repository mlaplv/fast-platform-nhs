<script lang="ts">
  import { onMount } from "svelte";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Copy from "@lucide/svelte/icons/copy";
  import Check from "@lucide/svelte/icons/check";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import { fade, fly } from "svelte/transition";

  let feedUrl = $state("");
  let copied = $state(false);
  let loadingStats = $state(true);
  let totalItems = $state(0);
  let totalVariants = $state(0);
  let lastSyncTime = $state("");

  onMount(async () => {
    // Generate absolute feed URL based on current window origin
    feedUrl = `${window.location.origin}/google-merchant.xml`;
    lastSyncTime = new Date().toLocaleTimeString("vi-VN", { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    await fetchFeedStats();
  });

  async function fetchFeedStats() {
    try {
      const res = await fetch("/google-merchant.xml");
      if (res.ok) {
        const text = await res.text();
        // Dynamic XML parser to count items for real-time validation
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(text, "application/xml");
        const items = xmlDoc.getElementsByTagName("item");
        totalItems = items.length;

        // Count unique item groups to find base products vs variants
        const itemGroupIds = new Set();
        for (let i = 0; i < items.length; i++) {
          const groupId = items[i].getElementsByTagName("g:item_group_id")[0]?.textContent;
          if (groupId) {
            itemGroupIds.add(groupId);
          }
        }
        totalVariants = totalItems - itemGroupIds.size;
      }
    } catch (e) {
      console.error("Failed to parse dynamic feed stats:", e);
    } finally {
      loadingStats = false;
    }
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(feedUrl);
    copied = true;
    setTimeout(() => {
      copied = false;
    }, 2000);
  }

  let submitting = $state(false);
  let submitSuccess = $state(false);

  async function submitToGMC() {
    submitting = true;
    submitSuccess = false;
    try {
      const res = await fetch("/google-merchant.xml/sync", {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success") {
          submitSuccess = true;
          await fetchFeedStats();
          setTimeout(() => {
            submitSuccess = false;
          }, 3000);
        }
      }
    } catch (e) {
      console.error("Failed to submit feed to Google Merchant:", e);
    } finally {
      submitting = false;
    }
  }
</script>

<div 
  class="relative group overflow-hidden bg-[#0a0a0a]/80 backdrop-blur-3xl border border-white/5 rounded-[2.5rem] p-8 transition-all duration-700 hover:border-emerald-500/30"
  in:fade={{ duration: 800 }}
>
  <!-- Background Aura -->
  <div class="absolute -top-20 -right-20 w-64 h-64 bg-emerald-500/10 blur-[100px] rounded-full group-hover:bg-emerald-500/20 transition-all duration-1000"></div>
  
  <div class="relative z-10">
    <div class="flex items-center justify-between mb-8">
      <div class="flex items-center gap-4">
        <div class="p-3 bg-white/5 rounded-2xl border border-white/10 group-hover:border-emerald-500/50 transition-colors">
          <ShoppingBag size={24} class="text-white group-hover:text-emerald-400 transition-colors" />
        </div>
        <div>
          <h2 class="text-xl font-black tracking-tighter text-white italic">Google Merchant Center</h2>
          <p class="text-[10px] font-mono text-gray-500 tracking-[0.3em]">ADS & FREE LISTINGS SYNC</p>
        </div>
      </div>
      <div class="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
        <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></div>
        <span class="text-[9px] font-bold text-emerald-400 uppercase tracking-widest">Active & Synced</span>
      </div>
    </div>

    <!-- Feed configuration instructions -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <div class="lg:col-span-2 space-y-4">
        <p class="text-sm text-gray-400 leading-relaxed">
          Mở rộng phạm vi tiếp cận khách hàng trên Google Tìm kiếm, Tab Mua sắm (Shopping) và SGE bằng cách cung cấp dữ liệu sản phẩm chuẩn hóa độ trung thực cao.
        </p>
        
        <!-- Clipboard URL input row -->
        <div class="flex items-center gap-2 p-1.5 bg-black/40 border border-white/5 rounded-2xl">
          <input 
            type="text" 
            readonly 
            value={feedUrl} 
            class="flex-1 bg-transparent border-0 text-xs font-mono text-emerald-400 px-4 focus:ring-0"
          />
          <button 
            onclick={copyToClipboard}
            class="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-emerald-500/10 hover:text-emerald-400 border border-white/10 hover:border-emerald-500/20 text-xs font-bold transition-all active:scale-95"
          >
            {#if copied}
              <Check size={14} class="text-emerald-400" />
              <span>Copied!</span>
            {:else}
              <Copy size={14} />
              <span>Copy Feed URL</span>
            {/if}
          </button>
        </div>
      </div>

      <!-- Feed Stats Matrix -->
      <div class="grid grid-cols-2 gap-4 bg-white/[0.02] border border-white/5 rounded-3xl p-5">
        <div class="space-y-1">
          <span class="text-[9px] font-mono text-gray-500 tracking-wider block uppercase">Tổng sản phẩm</span>
          {#if loadingStats}
            <span class="text-lg font-black text-white/40 block">...</span>
          {:else}
            <span class="text-xl font-black text-white block">{totalItems} <span class="text-xs text-gray-500 font-normal">items</span></span>
          {/if}
        </div>
        
        <div class="space-y-1">
          <span class="text-[9px] font-mono text-gray-500 tracking-wider block uppercase">Biến thể (Variants)</span>
          {#if loadingStats}
            <span class="text-lg font-black text-white/40 block">...</span>
          {:else}
            <span class="text-xl font-black text-emerald-400 block">+{totalVariants} <span class="text-xs text-gray-500 font-normal">items</span></span>
          {/if}
        </div>

        <div class="col-span-2 border-t border-white/5 pt-4 flex justify-between items-center text-[10px] font-mono text-gray-500">
          <span>Format: RSS 2.0 XML</span>
          <span>VND Currency</span>
        </div>
      </div>
    </div>

    <!-- Actions / Preview links -->
    <div class="flex flex-wrap gap-4 border-t border-white/5 pt-6">
      <a 
        href="/google-merchant.xml" 
        target="_blank" 
        class="flex items-center gap-2 px-6 py-3 rounded-2xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.08] hover:border-white/20 text-xs font-bold text-white transition-all active:scale-95"
      >
        <ExternalLink size={14} class="text-gray-400" />
        <span>Xem trước XML Feed</span>
      </a>

      <button 
        onclick={submitToGMC}
        disabled={submitting}
        class="flex items-center gap-2 px-6 py-3 rounded-2xl bg-emerald-500 text-black hover:bg-emerald-400 hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] text-xs font-black transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
      >
        {#if submitting}
          <div class="w-3.5 h-3.5 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
          <span>Đang phát tín hiệu Ping...</span>
        {:else if submitSuccess}
          <Check size={14} />
          <span>Đã Ping GMC Thành Công!</span>
        {:else}
          <Sparkles size={14} />
          <span>Gửi & Ping GMC</span>
        {/if}
      </button>

      <div class="flex items-center gap-2 ml-auto text-[10px] font-mono text-gray-600">
        <Sparkles size={12} class="text-emerald-500/50" />
        <span>Cập nhật mới nhất lúc: {lastSyncTime}</span>
      </div>
    </div>
  </div>
</div>

<style>
  /* Premium card reflection */
  .group::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
    transition: 0.5s;
  }
  .group:hover::after {
    left: 100%;
    transition: 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  }
</style>
