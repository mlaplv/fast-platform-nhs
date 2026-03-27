<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import { X, Calendar, Clock, Activity, ChevronRight, Target } from "lucide-svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { portal } from "$lib/actions/portal";
  import { Z_INDEX } from "$lib/core/constants/zIndex";
  import type { Appointment } from "$lib/types";

  let {
    isOpen = $bindable(),
    appointment = $bindable(),
    onClose,
    onSave
  } = $props<{
    isOpen: boolean;
    appointment: Partial<Appointment>;
    onClose: () => void;
    onSave: () => void;
  }>();

  let isLoading = $state(false);

  async function handleSave() {
    if (!appointment.title || !appointment.start_time || !appointment.end_time) {
      nanobot.showToast("Vui lòng điền đầy đủ thông tin", "warning");
      return;
    }

    isLoading = true;
    try {
      const payload = {
        ...appointment,
        metadata_json: appointment.metadata_json || {}
      };

      if (appointment.id) {
        await apiClient.patch(`/api/v1/appointments/${appointment.id}/`, payload);
        nanobot.showToast("Cập nhật lịch hẹn thành công", "success");
      } else {
        await apiClient.post("/api/v1/appointments/", payload);
        nanobot.showToast("Đã lưu lịch hẹn thành công", "success");
      }
      onSave();
      onClose();
    } catch (e) {
      console.error("Failed to save appointment", e);
      nanobot.showToast("Không thể lưu lịch hẹn", "error");
    } finally {
      isLoading = false;
    }
  }

  const recurringTypes = ['none', 'daily', 'weekly', 'monthly'] as const;
  const operationTypes = ['STRATEGY', 'DEPLOYMENT', 'REVIEW'] as const;
  const stageStatuses = ['UPCOMING', 'ONGOING', 'COMPLETED'] as const;
</script>

{#if isOpen}
  <div use:portal class="relative" style="z-index: {Z_INDEX.MODAL};">
    <!-- Backdrop: Elite Deep Blur -->
    <div
      class="fixed inset-0 bg-black/95 md:bg-black/90 md:backdrop-blur-sm"
      style="z-index: {Z_INDEX.OVERLAY};"
      transition:fade={{ duration: 300 }}
      onclick={onClose}
      aria-label="Close modal"
      role="button"
      tabindex="0"
      onkeydown={(e) => e.key === 'Escape' && onClose()}
    ></div>

    <!-- Drawer Panel: ELITE DESIGN (Right Aligned) -->
    <div
      class="fixed top-0 right-0 h-full w-[500px] max-w-full bg-[#050505] border-l border-white/10 shadow-[-30px_0_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden"
      transition:fly={{ x: 500, duration: 300, opacity: 1 }}
      style="z-index: {Z_INDEX.MODAL + 10};"
    >
      <!-- Header Section -->
      <div class="h-16 flex items-center justify-between px-6 border-b border-white/10 relative bg-black/40">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <Activity size={14} class="text-blue-500 animate-pulse" />
          </div>
          <div>
            <h2 class="text-sm font-bold text-white tracking-widest uppercase">
              {appointment.id ? 'Edit Appointment' : 'New Appointment'}
            </h2>
            {#if appointment.id}
              <div class="text-[9px] font-mono text-gray-500 uppercase">SYS_ID: {appointment.id}</div>
            {/if}
          </div>
        </div>
        <button 
          onclick={onClose}
          class="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors border border-transparent hover:border-white/10"
        >
          <X size={16} />
        </button>

        <!-- Decorative bottom line -->
        <div class="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
      </div>

      <!-- Form Body -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
        <!-- Title Field -->
        <div class="space-y-3">
          <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1" for="title">Title</label>
          <input 
            id="title"
            bind:value={appointment.title}
            type="text" 
            placeholder="Elite Strategic Planning..."
            class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-5 text-sm font-bold text-white placeholder:text-white/5 focus:outline-none focus:border-blue-500/30 transition-all shadow-inner"
          />
        </div>

        <!-- Date Range Nexus -->
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-3">
            <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1" for="start">Start Time</label>
            <div class="relative">
              <input 
                id="start"
                bind:value={appointment.start_time}
                type="datetime-local" 
                class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-[11px] font-bold text-white/80 focus:outline-none focus:border-blue-500/30 transition-all custom-datetime"
              />
              <Calendar size={14} class="absolute right-5 top-1/2 -translate-y-1/2 text-white/10 pointer-events-none" />
            </div>
          </div>
          <div class="space-y-3">
            <label class="block text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1" for="end">End Time</label>
            <div class="relative">
              <input 
                id="end"
                bind:value={appointment.end_time}
                type="datetime-local" 
                class="w-full bg-white/[0.03] border border-white/5 rounded-2xl px-6 py-4 text-[11px] font-bold text-white/80 focus:outline-none focus:border-blue-500/30 transition-all custom-datetime"
              />
              <Calendar size={14} class="absolute right-5 top-1/2 -translate-y-1/2 text-white/10 pointer-events-none" />
            </div>
          </div>
        </div>

        <!-- Selector Rows -->
        <div class="space-y-8">
          <!-- Recurring Type -->
          <div class="space-y-4">
            <div class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Recurring Type</div>
            <div class="flex flex-wrap gap-2.5">
              {#each recurringTypes as type}
                {@const active = appointment.recurring_type === type}
                <button 
                  onclick={() => appointment.recurring_type = type}
                  class="px-6 py-3 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all
                  {active ? 'bg-blue-500 text-white shadow-[0_0_30px_rgba(59,130,246,0.4)] scale-105' : 'bg-white/[0.04] text-white/30 hover:bg-white/[0.08] hover:text-white/60'}"
                >
                  {type}
                </button>
              {/each}
            </div>
          </div>

          <!-- Operation Type -->
          <div class="space-y-4">
            <div class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Operation Type</div>
            <div class="flex flex-wrap gap-2.5">
              {#each operationTypes as type}
                {@const active = appointment.type === type}
                <button 
                  onclick={() => appointment.type = type}
                  class="px-6 py-3 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all
                  {active ? 'bg-[#a855f7] text-white shadow-[0_0_30px_rgba(168,85,247,0.4)] scale-105' : 'bg-white/[0.04] text-white/30 hover:bg-white/[0.08] hover:text-white/60'}"
                >
                  {type}
                </button>
              {/each}
            </div>
          </div>

          <!-- Stage Status -->
          <div class="space-y-4">
            <div class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Stage Status</div>
            <div class="flex flex-wrap gap-2.5">
              {#each stageStatuses as status}
                {@const active = appointment.status === status}
                <button 
                  onclick={() => appointment.status = status}
                  class="px-6 py-3 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all
                  {active ? 'bg-[#10b981] text-white shadow-[0_0_30px_rgba(16,185,129,0.4)] scale-105' : 'bg-white/[0.04] text-white/30 hover:bg-white/[0.08] hover:text-white/60'}"
                >
                  {status}
                </button>
              {/each}
            </div>
          </div>
        </div>

        <!-- Submit Nexus -->
        <div class="pt-6">
          <button 
            onclick={handleSave}
            disabled={isLoading}
            class="w-full py-4 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white text-[11px] font-black uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_10px_30px_-5px_rgba(37,99,235,0.4)] disabled:opacity-50 flex items-center justify-center overflow-hidden relative group"
          >
            <!-- Hover sheen effect -->
            <div class="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            
            {#if isLoading}
              <Activity size={16} class="animate-spin mr-3" />
              Processing...
            {:else}
              Save Operation Summary
            {/if}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0, 255, 255, 0.3); }

  /* Custom styling for datetime-local to match Elite aesthetics */
  .custom-datetime { color-scheme: dark; }
  .custom-datetime::-webkit-calendar-picker-indicator {
    opacity: 0;
    position: absolute;
    right: 0;
    top: 0;
    width: 100%;
    height: 100%;
    cursor: pointer;
  }
</style>
