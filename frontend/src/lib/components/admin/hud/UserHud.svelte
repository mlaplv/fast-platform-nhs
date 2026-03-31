<script lang="ts">
  import { fade, scale } from "svelte/transition";
  import LucideUser from "lucide-svelte/icons/user";
  import LucideSettings from "lucide-svelte/icons/settings";
  import LucideLogOut from "lucide-svelte/icons/log-out";
  import LucideShield from "lucide-svelte/icons/shield";
  import LucideGlobe from "lucide-svelte/icons/globe";
import LucideLayout from "lucide-svelte/icons/layout";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

  function toggleDropdown() {
    nanobot.toggleHudPopup("USER");
  }

  function handleLogout() {
    // Clear cookies & local storage
    document.cookie = "admin_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    localStorage.removeItem("admin_token");
    window.location.href = "/login";
  }
</script>

<div class="relative">
  <button 
    onclick={toggleDropdown}
    class="flex items-center gap-3 p-1 pl-4 bg-black/80 md:bg-black/40 md:backdrop-blur-md border border-white/5 rounded-full hover:border-[#00FFFF]/40 hover:bg-[#00FFFF]/5 transition-all group relative overflow-hidden"
  >
    <div class="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>

    <div class="flex flex-col items-end mr-1">
      <span class="text-[8px] font-mono text-gray-400 uppercase tracking-[0.2em] leading-tight opacity-70">Identity Verified</span>
      <span class="text-[11px] font-black text-white group-hover:text-[#00FFFF] transition-colors tracking-tight uppercase">
        {nanobot.userName || "OPERATOR"}
      </span>
    </div>
    
    <div class="w-9 h-9 rounded-full border border-white/10 bg-[#050505] flex items-center justify-center relative group-hover:border-[#00FFFF]/50 transition-all duration-500 shadow-inner">
      <div class="absolute inset-0 bg-gradient-to-tr from-[#00FFFF]/10 to-transparent rounded-full opacity-50"></div>
      <div class="absolute inset-[-2px] rounded-full border border-[#00FFFF]/20 group-hover:border-[#00FFFF]/40 transition-all duration-700 animate-pulse"></div>
      <LucideUser size={18} class="text-[#00FFFF] relative z-10 group-hover:scale-110 transition-transform duration-500" />
      <div class="absolute bottom-0 left-1/4 right-1/4 h-[2px] bg-[#00FFFF] shadow-[0_0_8px_#00FFFF]"></div>
    </div>
  </button>

  {#if nanobot.activeHudPopup === "USER"}
    <div 
      in:scale={{duration: 250, start: 0.95, opacity: 0}}
      out:fade={{duration: 150}}
      class="absolute right-0 mt-4 w-80 bg-[#080808] md:bg-[#080808]/98 md:backdrop-blur-3xl border border-white/10 rounded-2xl shadow-[0_20px_80px_rgba(0,0,0,0.9),0_0_30px_rgba(0,255,255,0.05)] overflow-hidden"
      style="z-index: {Z_INDEX_ADMIN.HUD_DROPDOWN};"
    >
      <!-- MISSION CONTROL HEADER -->
      <div class="p-6 pb-4 border-b border-white/5 relative">
        <!-- Technical Grid Underlay -->
        <div class="absolute inset-0 opacity-[0.03] pointer-events-none" style="background-image: radial-gradient(#00FFFF 0.5px, transparent 0.5px); background-size: 10px 10px;"></div>
        
        <div class="flex items-start justify-between mb-6 relative z-10">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-2xl border border-[#00FFFF]/20 bg-black flex items-center justify-center relative group/avatar">
              <div class="absolute inset-0 bg-cyan-500/10 rounded-2xl blur-sm group-hover:blur-md transition-all"></div>
              <LucideShield size={32} class="text-[#00FFFF] relative z-10 drop-shadow-[0_0_10px_rgba(0,255,255,0.5)]" />
              <!-- Status corner indicator -->
              <div class="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-black shadow-[0_0_8px_#22c55e]"></div>
            </div>
            <div>
              <p class="text-[9px] font-mono text-cyan-500/60 uppercase tracking-[0.4em] mb-1">Authenticated Identity</p>
              <h3 class="text-xl font-black text-white leading-none mb-1.5 tracking-tighter uppercase italic">
                {nanobot.userName || "OPERATOR"}
              </h3>
              <p class="text-[10px] font-mono text-gray-500 lowercase tracking-tight">{nanobot.userEmail || "ghost@smartshop.test"}</p>
            </div>
          </div>
        </div>

        <!-- TACTICAL STATUS MODULE -->
        <div class="bg-white/[0.02] border border-white/5 rounded-xl p-4 relative overflow-hidden group/status">
          <div class="absolute top-0 left-0 w-1 h-full bg-[#00FFFF] opacity-40"></div>
          
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="text-[10px] font-black text-white/90 uppercase tracking-widest">Access Level:</span>
              <span class="px-2 py-0.5 bg-[#00FFFF]/10 border border-[#00FFFF]/30 rounded text-[9px] font-bold text-[#00FFFF] uppercase tracking-tighter">
                {permissionState.roles[0] || "USER"}
              </span>
            </div>
            <span class="text-[8px] font-mono text-gray-600 uppercase">LVL_0{permissionState.roles.length}</span>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div class="flex items-center gap-2 p-2 bg-black/40 border border-white/5 rounded-lg">
              <div class="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_5px_#22c55e]"></div>
              <span class="text-[9px] font-black text-green-500 uppercase tracking-widest">GOD_MODE</span>
            </div>
            <div class="flex items-center gap-2 p-2 bg-black/40 border border-white/5 rounded-lg opacity-60">
              <div class="w-1.5 h-1.5 bg-gray-500 rounded-full"></div>
              <span class="text-[9px] font-black text-gray-500 uppercase tracking-widest">ENCRYPTED</span>
            </div>
          </div>
          
          <!-- Decorative bits -->
          <div class="absolute bottom-1 right-1 flex gap-0.5">
            <div class="w-4 h-0.5 bg-white/10"></div>
            <div class="w-1 h-0.5 bg-[#00FFFF]/40"></div>
          </div>
        </div>
      </div>

      <!-- SYSTEM COMMAND GRID -->
      <div class="p-4 grid grid-cols-2 gap-2 bg-white/[0.01]">
        <button 
          onclick={() => nanobot.openWidget("USER_MANAGEMENT")}
          class="flex flex-col items-center justify-center p-4 bg-white/[0.02] border border-white/5 rounded-xl hover:bg-[#00FFFF]/5 hover:border-[#00FFFF]/30 transition-all group/btn"
        >
          <LucideSettings size={20} class="mb-2 text-gray-500 group-hover:text-[#00FFFF] group-hover:rotate-45 transition-all duration-500" />
          <span class="text-[10px] font-black text-gray-400 group-hover:text-white uppercase tracking-widest">Management</span>
          <span class="text-[7px] font-mono text-gray-600 mt-1">PROTO_MGR</span>
        </button>

        <button 
          onclick={handleLogout}
          class="flex flex-col items-center justify-center p-4 bg-white/[0.02] border border-white/5 rounded-xl hover:bg-red-500/5 hover:border-red-500/30 transition-all group/btn"
        >
          <LucideLogOut size={20} class="mb-2 text-gray-500 group-hover:text-red-500 group-hover:translate-x-1 transition-all duration-500" />
          <span class="text-[10px] font-black text-gray-400 group-hover:text-white uppercase tracking-widest">Terminate</span>
          <span class="text-[7px] font-mono text-gray-600 mt-1">EXIT_SHUTDOWN</span>
        </button>
      </div>

      <!-- FOOTER TELEMETRY -->
      <div class="px-6 py-2 bg-black border-t border-white/5 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="flex gap-0.5">
            {#each Array(4) as _, i}
              <div class="w-1 h-2 {i < 3 ? 'bg-cyan-500' : 'bg-white/10'} rounded-full"></div>
            {/each}
          </div>
          <span class="text-[8px] font-mono text-gray-600 uppercase">SYS_LINK_STABLE</span>
        </div>
        <span class="text-[8px] font-mono text-gray-700 tracking-tighter">REF: {nanobot.userName?.substring(0,8).toUpperCase() || "X-000"}</span>
      </div>
    </div>
  {/if}
</div>
