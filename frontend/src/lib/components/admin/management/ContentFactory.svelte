<script lang="ts">
  // Core Dependencies
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade } from "svelte/transition";
  import Megaphone from "lucide-svelte/icons/megaphone";
  import PlusCircle from "lucide-svelte/icons/plus-circle";
  import Loader2 from "lucide-svelte/icons/loader-2";

  // Data
  let { data = {} } = $props();
  
  // Empty State logic - for now, always show empty state as we haven't built the full list yet
  let campaigns: any[] = $state([]); 
  let isLoading = $state(false);

  // Mock function to simulate creating a new campaign
  function handleCreateCampaign() {
    nanobot.processCommand("tạo tin tức", "text");
    nanobot.closeUniversalModal();
  }
</script>

<div class="w-full h-full flex flex-col pt-4" in:fade={{ duration: 200 }}>
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center text-cyan-500/50">
      <Loader2 class="w-8 h-8 animate-spin mb-4" />
      <p class="font-mono text-sm tracking-wider">Đang tải dữ liệu...</p>
    </div>
  {:else if campaigns.length === 0}
    <!-- GOD MODE: LEAN EMPTY STATE -->
    <div class="flex-1 flex flex-col items-center justify-center p-8 text-center border border-dashed border-gray-800 rounded-xl bg-black/20 backdrop-blur-sm">
      <div class="w-16 h-16 rounded-full bg-cyan-500/10 flex items-center justify-center mb-6 border border-cyan-500/20 shadow-[0_0_30px_rgba(0,255,255,0.1)]">
        <Megaphone class="w-8 h-8 text-cyan-400" />
      </div>
      <h3 class="text-xl font-bold text-gray-200 mb-2">Chưa có Chiến dịch nào</h3>
      <p class="text-gray-500 text-sm max-w-md mx-auto mb-8 leading-relaxed">
        Không gian sáng tạo của bạn đang trống. Hãy tạo chiến dịch mới để AI Xohi bắt đầu lên ý tưởng, viết bài và phân phối nội dung của bạn.
      </p>
      
      <button 
        onclick={handleCreateCampaign}
        class="group relative px-6 py-3 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 font-medium rounded-lg border border-cyan-500/30 transition-all active:scale-95 flex items-center gap-2 overflow-hidden"
      >
        <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
        <PlusCircle size={18} />
        <span>Tạo Chiến Dịch Đầu Tiên</span>
      </button>
    </div>
  {:else}
    <!-- Reserved for future Campaign List -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- List will go here -->
    </div>
  {/if}
</div>
