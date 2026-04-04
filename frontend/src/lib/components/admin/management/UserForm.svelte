<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import UserCircle from "lucide-svelte/icons/user-circle";
  import Mail from "lucide-svelte/icons/mail";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import type { User } from "$lib/types";

  let { editingId, initialData, onClose, onSuccess } = $props<{
    editingId: string | null;
    initialData: User | null;
    onClose: () => void;
    onSuccess: (updatedUser: User) => void;
  }>();

  let name = $state("");
  let email = $state("");
  let isLoading = $state(false);
  let error = $state<string | null>(null);

  // Sync state when initialData changes
  $effect(() => {
    name = initialData?.name || "";
    email = initialData?.email || "";
  });

  async function handleSubmit(e: Event) {
    e.preventDefault();
    isLoading = true;
    error = null;

    try {
      const payload: Record<string, unknown> = { name };
      if (!editingId) {
        payload.email = email;
        payload.password = "SmartShop@123"; // Reset-required default for AI nodes
        payload.role_codes = ["CUSTOMER"]; // Default safe role
      }

      const res = editingId
        ? await apiClient.patch<User>(`/api/v1/users/${editingId}`, payload)
        : await apiClient.post<User>(`/api/v1/users`, payload);

      nanobot.addLog(
        `Identity ${editingId ? "updated" : "synthesized"}: ${res.email}`,
        "Nanobot-Sec",
      );
      onSuccess(res);
    } catch (err: unknown) {
      const e = err as Error;
      error = e.message || "Failed to process identity operation.";
      nanobot.addLog(`Operation Error: ${error}`, "Nanobot-Sec");
    } finally {
      isLoading = false;
    }
  }
</script>

<!-- Backdrop -->
<div
  transition:fade={{ duration: 200 }}
  class="fixed inset-0 bg-black/95 md:bg-black/80 md:backdrop-blur-sm z-[100] flex items-center justify-center p-4"
>
  <!-- Modal Panel -->
  <div
    transition:slide={{ duration: 300, axis: "y" }}
    class="w-full max-w-lg bg-[#0a0a0a]/95 border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col relative"
  >
    <!-- Header -->
    <div
      class="p-6 border-b border-white/5 bg-gradient-to-r from-black/50 to-transparent flex items-center justify-between"
    >
      <div class="flex items-center gap-3">
        <div
          class="p-2 bg-[#00FFFF]/10 rounded-lg border border-[#00FFFF]/20 shadow-[0_0_15px_rgba(0,255,255,0.1)]"
        >
          <UserCircle size={18} class="text-[#00FFFF]" />
        </div>
        <div>
          <h2
            class="text-xs font-bold font-mono text-white uppercase tracking-widest"
          >
            Entity Configuration
          </h2>
          <p class="text-[9px] font-mono text-gray-500 tracking-wider">
            Modify identity attributes
          </p>
        </div>
      </div>
      <button
        onclick={onClose}
        class="p-2 text-gray-500 hover:text-white bg-white/5 hover:bg-white/10 rounded-xl transition-colors"
      >
        <X size={16} />
      </button>
    </div>

    <!-- Body -->
    <div class="p-6 overflow-y-auto custom-scrollbar">
      {#if error}
        <div
          class="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-500 text-[10px] font-mono tracking-widest uppercase"
        >
          [CRITICAL_ERROR]: {error}
        </div>
      {/if}

      <form
        id="user-config-form"
        onsubmit={handleSubmit}
        class="flex flex-col gap-5"
      >
        <!-- Field: Email (Readonly) -->
        <div class="flex flex-col gap-2 relative group">
          <label
            for="user-email"
            class="text-[9px] font-mono text-gray-400 uppercase tracking-widest font-bold"
            >Primary Identity (Email) <span class="text-red-500">*</span></label
          >
          <div class="relative">
            <div
              class="absolute inset-y-0 left-4 flex items-center pointer-events-none"
            >
              <Mail size={14} class="text-gray-600" />
            </div>
            <input
              id="user-email"
              type="text"
              bind:value={email}
              disabled={!!editingId}
              placeholder="user@example.com"
              required
              class="w-full bg-black/40 border border-white/5 rounded-xl py-3 pl-10 pr-4 text-[11px] font-mono text-gray-200 disabled:text-gray-500 disabled:cursor-not-allowed shadow-inner focus:outline-none focus:border-[#00FFFF]/50 transition-all"
            />
          </div>
        </div>

        <!-- Field: Name -->
        <div class="flex flex-col gap-2 relative group">
          <label
            for="user-name"
            class="text-[9px] font-mono text-white/60 uppercase tracking-widest font-bold group-focus-within:text-[#00FFFF] transition-colors"
            >Entity Name Alias</label
          >
          <div class="relative">
            <div
              class="absolute inset-y-0 left-4 flex items-center pointer-events-none"
            >
              <UserCircle
                size={14}
                class="text-gray-500 group-focus-within:text-[#00FFFF] transition-colors"
              />
            </div>
            <input
              id="user-name"
              bind:value={name}
              type="text"
              placeholder="Enter alias..."
              required
              class="w-full bg-black/50 border border-white/10 group-hover:border-white/20 rounded-xl py-3 pl-10 pr-4 text-[11px] font-mono text-white placeholder:text-gray-700 focus:outline-none focus:border-[#00FFFF]/50 focus:ring-1 focus:ring-[#00FFFF]/20 transition-all shadow-inner"
            />
          </div>
        </div>
      </form>
    </div>

    <!-- Footer -->
    <div
      class="p-5 border-t border-white/5 bg-black/40 flex items-center justify-end gap-3"
    >
      <button
        type="button"
        onclick={onClose}
        disabled={isLoading}
        class="px-5 py-2.5 rounded-xl text-[10px] font-mono text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 transition-colors uppercase tracking-widest"
      >
        Abort
      </button>
      <button
        type="submit"
        form="user-config-form"
        disabled={isLoading}
        class="px-6 py-2.5 rounded-xl text-[10px] font-bold font-mono text-[#00FFFF] hover:text-white bg-gradient-to-r from-[#00FFFF]/20 to-[#00FFFF]/5 border border-[#00FFFF]/40 hover:shadow-[0_0_20px_rgba(0,255,255,0.3)] transition-all uppercase tracking-widest relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <div
          class="absolute inset-0 bg-[#00FFFF]/20 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-300 ease-out"
        ></div>
        <span class="relative z-10"
          >{isLoading ? "SYNCING..." : "COMMIT_CHANGES"}</span
        >
      </button>
    </div>
  </div>
</div>
