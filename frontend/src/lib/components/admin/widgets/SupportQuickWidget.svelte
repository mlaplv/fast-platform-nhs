<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import HelpCircle from "lucide-svelte/icons/help-circle";
  import Inbox from "lucide-svelte/icons/inbox";
  import Settings from "lucide-svelte/icons/settings";
  import Sparkles from "lucide-svelte/icons/sparkles";
import Brain from "lucide-svelte/icons/brain";
  import ArrowUpRight from "lucide-svelte/icons/arrow-up-right";
  import { fade, fly } from "svelte/transition";

  const actions = [
    {
      id: "support",
      label: "Hỗ trợ Helen",
      sub: "Đào tạo & Tri thức",
      icon: Sparkles,
      color: "from-cyan-500 to-blue-600",
      widget: "SUPPORT_KNOWLEDGE"
    },
    {
      id: "inbox",
      label: "Hộp thư AI",
      sub: "Giám sát & Chốt đơn",
      icon: Inbox,
      color: "from-purple-500 to-pink-600",
      widget: "SUPPORT_INBOX"
    },
    {
      id: "brain",
      label: "Brain Hub",
      sub: "Audit & Đồng bộ",
      icon: Brain,
      color: "from-indigo-500 to-purple-600",
      widget: "BRAIN_MANAGEMENT"
    },
    {
      id: "settings",
      label: "Cấu hình",
      sub: "Hệ thống & Chiến dịch",
      icon: Settings,
      color: "from-amber-500 to-orange-600",
      widget: "SYSTEM_SETTINGS"
    }
  ];

  function openAction(widget: any) {
    nanobot.openWidget(widget);
  }
</script>

<div 
  class="relative group overflow-hidden bg-[#0a0a0a]/80 backdrop-blur-3xl border border-white/5 rounded-[2.5rem] p-8 transition-all duration-700 hover:border-cyan-500/30"
  in:fade={{ duration: 800 }}
>
  <!-- Background Aura -->
  <div class="absolute -top-20 -right-20 w-64 h-64 bg-cyan-500/10 blur-[100px] rounded-full group-hover:bg-cyan-500/20 transition-all duration-1000"></div>
  
  <div class="relative z-10">
    <div class="flex items-center justify-between mb-8">
      <div class="flex items-center gap-4">
        <div class="p-3 bg-white/5 rounded-2xl border border-white/10 group-hover:border-cyan-500/50 transition-colors">
          <HelpCircle size={24} class="text-white group-hover:text-cyan-400 transition-colors" />
        </div>
        <div>
          <h2 class="text-xl font-black tracking-tighter text-white uppercase italic">Quick Command</h2>
          <p class="text-[10px] font-mono text-gray-500 tracking-[0.3em] uppercase">Control Center v2.2</p>
        </div>
      </div>
      <div class="flex gap-1">
        <div class="w-1 h-1 bg-cyan-500 rounded-full animate-pulse"></div>
        <div class="w-1 h-1 bg-cyan-500/40 rounded-full"></div>
      </div>
    </div>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {#each actions as action, i}
        <button
          onclick={() => openAction(action.widget)}
          class="relative overflow-hidden group/btn bg-white/[0.03] border border-white/5 rounded-3xl p-5 text-left transition-all duration-500 hover:bg-white/[0.07] hover:border-white/20 hover:-translate-y-1 active:scale-95"
          in:fly={{ y: 20, delay: 100 * i, duration: 600 }}
        >
          <!-- Hover Glow -->
          <div class="absolute inset-0 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-500 bg-gradient-to-br {action.color} blur-[40px] -z-10"></div>
          
          <div class="flex justify-between items-start mb-4">
            <div class="p-2.5 rounded-xl bg-white/5 border border-white/10 group-hover/btn:border-white/30 transition-all">
              <action.icon size={20} class="text-white" />
            </div>
            <ArrowUpRight size={14} class="text-gray-600 group-hover/btn:text-white group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-all" />
          </div>

          <div>
            <div class="text-[13px] font-black text-white tracking-widest uppercase mb-1">{action.label}</div>
            <div class="text-[9px] font-mono text-gray-500 group-hover/btn:text-gray-300 transition-colors uppercase tracking-wider">{action.sub}</div>
          </div>
        </button>
      {/each}
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
