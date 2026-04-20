<script lang="ts">
  // Transitions removed for zero-lag
  import X from "lucide-svelte/icons/x";
  import UserCircle from "lucide-svelte/icons/user-circle";
  import Mail from "lucide-svelte/icons/mail";
  import Phone from "lucide-svelte/icons/phone";
  import Calendar from "lucide-svelte/icons/calendar";
  import Hash from "lucide-svelte/icons/hash";
  import Shield from "lucide-svelte/icons/shield";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import AlertCircle from "lucide-svelte/icons/alert-circle";
  import Coins from "lucide-svelte/icons/coins";
  import Plus from "lucide-svelte/icons/plus";
  import History from "lucide-svelte/icons/history";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import type { User, Role } from "$lib/types";

  let { editingId, initialData, roles = [], onClose, onSuccess } = $props<{
    editingId: string | null;
    initialData: User | null;
    roles: Role[];
    onClose: () => void;
    onSuccess: (updatedUser: User) => void;
  }>();

  // Unified State
  let formData = $state({
    name: "",
    email: "",
    username: "",
    phone: "",
    gender: "OTHER",
    dob: "",
    status: "ACTIVE",
    role_codes: [] as string[]
  });

  let isLoading = $state(false);
  let error = $state<string | null>(null);

  // Loyalty State
  let loyaltyData = $state<any>(null);
  let isAdjusting = $state(false);
  let adjustAmount = $state(0);
  let adjustNotes = $state("");

  // Sync state when initialData changes
  $effect(() => {
    if (initialData) {
      formData.name = initialData.name || "";
      formData.email = initialData.email || "";
      formData.username = initialData.username || "";
      formData.phone = initialData.phone || "";
      formData.gender = initialData.gender || "OTHER";
      formData.dob = initialData.dob ? initialData.dob.split('T')[0] : "";
      formData.status = initialData.status || "ACTIVE";
      formData.role_codes = initialData.roles?.map(r => r.code) || [];
      if (editingId) fetchLoyalty();
    }
  });

  async function fetchLoyalty() {
    if (!editingId) return;
    try {
      loyaltyData = await apiClient.get(`/api/v1/users/${editingId}/loyalty`);
    } catch (e) {
      console.error("Failed to fetch loyalty:", e);
    }
  }

  async function handleAdjustPoints() {
    if (!editingId || adjustAmount === 0 || !adjustNotes) return;
    isAdjusting = true;
    try {
      await apiClient.post(`/api/v1/users/${editingId}/loyalty/adjust`, {
        amount: adjustAmount,
        notes: adjustNotes,
        transaction_type: "ADJUST_ADMIN"
      });
      nanobot.addLog(`System points adjusted for user ${editingId}: ${adjustAmount}`, "Nanobot-Sec");
      adjustAmount = 0;
      adjustNotes = "";
      fetchLoyalty();
    } catch (err: any) {
      error = err.message || "Failed to adjust points.";
    } finally {
      isAdjusting = false;
    }
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    isLoading = true;
    error = null;

    try {
      const payload: Record<string, unknown> = { 
        name: formData.name,
        username: formData.username,
        phone: formData.phone,
        gender: formData.gender,
        dob: formData.dob || null,
        status: formData.status,
        roles: formData.role_codes
      };

      if (!editingId) {
        payload.email = formData.email;
        payload.password = "SmartShop@123";
        payload.role_codes = formData.role_codes.length > 0 ? formData.role_codes : ["CUSTOMER"];
      }

      const res = editingId
        ? await apiClient.patch<User>(`/api/v1/users/${editingId}`, payload)
        : await apiClient.post<User>(`/api/v1/users`, payload);

      nanobot.addLog(`Identity ${editingId ? "updated" : "synthesized"}: ${res.email}`, "Nanobot-Sec");
      onSuccess(res);
    } catch (err: unknown) {
      const e = err as Error;
      error = e.message || "Failed to process identity operation.";
      nanobot.addLog(`Operation Error: ${error}`, "Nanobot-Sec");
    } finally {
      isLoading = false;
    }
  }

  function toggleRole(code: string) {
    if (formData.role_codes.includes(code)) {
      formData.role_codes = formData.role_codes.filter(c => c !== code);
    } else {
      formData.role_codes = [...formData.role_codes, code];
    }
  }
</script>

<div
  class="fixed inset-0 bg-black/80 z-[var(--z-modal-overlay)] flex items-center justify-center p-4"
>
  <!-- Modal Panel -->
  <div
    class="w-full max-w-2xl bg-[#0a0a0a] border border-white/10 rounded-2xl shadow-[0_30px_100px_rgba(0,0,0,0.9)] overflow-hidden flex flex-col relative max-h-[90vh]"
  >

    <!-- Header -->
    <div class="p-6 border-b border-white/5 bg-gradient-to-r from-[#00FFFF]/5 to-transparent flex items-center justify-between relative z-10">
      <div class="flex items-center gap-4">
        <div class="p-2.5 bg-[#00FFFF]/10 rounded-xl border border-[#00FFFF]/20 shadow-[0_0_20px_rgba(0,255,255,0.1)]">
          <UserCircle size={20} class="text-[#00FFFF]" />
        </div>
        <div>
          <h2 class="text-sm font-bold font-mono text-white uppercase tracking-[0.2em]">Identity_Config_Panel</h2>
          <p class="text-[9px] font-mono text-[#00FFFF]/50 tracking-widest mt-0.5 uppercase">Sector: User_Management_V2.2</p>
        </div>
      </div>
      <button
        onclick={onClose}
        class="p-2.5 text-gray-500 hover:text-white bg-white/5 hover:bg-white/10 rounded-xl transition-all hover:rotate-90"
      >
        <X size={18} />
      </button>
    </div>

    <!-- Body -->
    <div class="p-8 overflow-y-auto custom-scrollbar relative z-10">
      {#if error}
        <div class="mb-8 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
          <AlertCircle size={16} class="text-red-500 mt-0.5" />
          <div class="flex-1">
            <span class="text-red-500 text-[10px] font-mono font-bold uppercase tracking-widest block">Core_Exceptions_Detected</span>
            <p class="text-red-400/70 text-[9px] font-mono mt-1">{error}</p>
          </div>
        </div>
      {/if}

      <form id="user-config-form" onsubmit={handleSubmit} class="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        <!-- SECTION: CORE IDENTITY -->
        <div class="flex flex-col gap-6">
          <div class="flex items-center gap-2 border-b border-white/5 pb-2 mb-2">
            <Hash size={12} class="text-[#00FFFF]/50" />
            <span class="text-[9px] font-mono text-gray-400 uppercase tracking-widest font-bold">Core_Identity</span>
          </div>

          <!-- Email -->
          <div class="flex flex-col gap-2 relative group">
            <label for="f-email" class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Primary_Email <span class="text-red-500/50">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none"><Mail size={14} class="text-gray-600 group-focus-within:text-[#00FFFF] transition-colors" /></div>
              <input id="f-email" type="email" bind:value={formData.email} disabled={!!editingId} required placeholder="SYSTEM@SHADOW.NODE"
                class="w-full bg-black/60 border border-white/5 rounded-xl py-3.5 pl-11 pr-4 text-[11px] font-mono text-gray-200 disabled:text-gray-600 focus:outline-none focus:border-[#00FFFF]/40 focus:ring-4 focus:ring-[#00FFFF]/5 transition-all"
              />
            </div>
          </div>

          <!-- Username -->
          <div class="flex flex-col gap-2 relative group">
            <label for="f-username" class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Login_Alias</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none"><UserCircle size={14} class="text-gray-600 group-focus-within:text-[#00FFFF] transition-colors" /></div>
              <input id="f-username" bind:value={formData.username} type="text" placeholder="SHADOW_AGENT_01"
                class="w-full bg-black/60 border border-white/5 rounded-xl py-3.5 pl-11 pr-4 text-[11px] font-mono text-gray-200 focus:outline-none focus:border-[#00FFFF]/40 focus:ring-4 focus:ring-[#00FFFF]/5 transition-all"
              />
            </div>
          </div>

          <!-- Name -->
          <div class="flex flex-col gap-2 relative group">
            <label for="f-name" class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Entity_Signature <span class="text-red-500/50">*</span></label>
            <div class="relative">
              <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none"><UserCircle size={14} class="text-gray-600 group-focus-within:text-[#00FFFF] transition-colors" /></div>
              <input id="f-name" bind:value={formData.name} type="text" required placeholder="NEXUS_CORE"
                class="w-full bg-black/60 border border-white/5 rounded-xl py-3.5 pl-11 pr-4 text-[11px] font-mono text-gray-200 focus:outline-none focus:border-[#00FFFF]/40 focus:ring-4 focus:ring-[#00FFFF]/5 transition-all"
              />
            </div>
          </div>
        </div>

        <!-- SECTION: PROFILE DETAILS -->
        <div class="flex flex-col gap-6">
          <div class="flex items-center gap-2 border-b border-white/5 pb-2 mb-2">
            <UserCircle size={12} class="text-[#00FFFF]/50" />
            <span class="text-[9px] font-mono text-gray-400 uppercase tracking-widest font-bold">Profile_Matrix</span>
          </div>

          <!-- Phone -->
          <div class="flex flex-col gap-2 relative group">
            <label for="f-phone" class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Comms_Channel</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none"><Phone size={14} class="text-gray-600 group-focus-within:text-[#00FFFF] transition-colors" /></div>
              <input id="f-phone" bind:value={formData.phone} type="text" placeholder="+84 XXX XXX XXX"
                class="w-full bg-black/60 border border-white/5 rounded-xl py-3.5 pl-11 pr-4 text-[11px] font-mono text-gray-200 focus:outline-none focus:border-[#00FFFF]/40 focus:ring-4 focus:ring-[#00FFFF]/5 transition-all"
              />
            </div>
          </div>

          <!-- Gender & DOB Grid -->
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-2 relative group">
              <label for="f-gender" class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Biological_ID</label>
              <select id="f-gender" bind:value={formData.gender}
                class="w-full bg-black/60 border border-white/5 rounded-xl py-3.5 px-4 text-[11px] font-mono text-gray-200 focus:outline-none focus:border-[#00FFFF]/40 focus:ring-4 focus:ring-[#00FFFF]/5 transition-all appearance-none cursor-pointer"
              >
                <option value="MALE">MALE</option>
                <option value="FEMALE">FEMALE</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>
            <div class="flex flex-col gap-2 relative group">
              <label for="f-dob" class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Origin_Date</label>
              <div class="relative">
                <input id="f-dob" bind:value={formData.dob} type="date"
                  class="w-full bg-black/60 border border-white/5 rounded-xl py-3.5 px-4 text-[11px] font-mono text-gray-200 focus:outline-none focus:border-[#00FFFF]/40 focus:ring-4 focus:ring-[#00FFFF]/5 transition-all"
                />
              </div>
            </div>
          </div>

          <!-- Status Toggle -->
          <div class="flex flex-col gap-3">
             <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Operational_Status</span>
             <div class="flex gap-2">
               {#each ["ACTIVE", "LOCKED"] as s}
                 <button type="button" onclick={() => formData.status = s}
                  class="flex-1 py-2.5 rounded-xl border font-mono text-[9px] font-bold uppercase tracking-widest transition-all {formData.status === s ? 
                    (s === 'ACTIVE' ? 'bg-[#00FFFF]/20 border-[#00FFFF]/40 text-[#00FFFF]' : 'bg-red-500/20 border-red-500/40 text-red-500') : 
                    'bg-white/5 border-transparent text-gray-500 hover:bg-white/10'}"
                 >
                   {s}
                 </button>
               {/each}
             </div>
          </div>
        </div>

        <!-- SECTION: SECURITY TIERS -->
        <div class="md:col-span-2 flex flex-col gap-4">
          <div class="flex items-center gap-2 border-b border-white/5 pb-2 mb-2">
            <Shield size={12} class="text-[#00FFFF]/50" />
            <span class="text-[9px] font-mono text-gray-400 uppercase tracking-widest font-bold">Assigned_Security_Tiers</span>
          </div>
          
          <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            {#each roles as role}
              <button type="button" onclick={() => toggleRole(role.code)}
                class="px-3 py-3 rounded-xl border font-mono text-[9px] font-bold tracking-tight transition-all flex flex-col gap-1 items-center justify-center text-center {formData.role_codes.includes(role.code) ? 
                  'bg-[#00FFFF]/10 border-[#00FFFF]/40 text-[#00FFFF] shadow-[0_0_20px_rgba(0,255,255,0.1)]' : 
                  'bg-white/5 border-white/5 text-gray-500 hover:border-white/10 hover:bg-white/8'}"
              >
                <Shield size={14} class={formData.role_codes.includes(role.code) ? "text-[#00FFFF]" : "text-gray-700"} />
                <span class="truncate w-full">{role.name}</span>
              </button>
            {/each}
          </div>
        </div>

        <!-- SECTION: LOYALTY PROTOCOL -->
        {#if editingId}
        <div class="md:col-span-2 flex flex-col gap-4 mt-4 border-t border-white/5 pt-6">
          <div class="flex items-center justify-between border-b border-white/5 pb-2">
            <div class="flex items-center gap-2">
              <Coins size={12} class="text-amber-400" />
              <span class="text-[9px] font-mono text-gray-400 uppercase tracking-widest font-bold">Loyalty_Rewards_Matrix</span>
            </div>
            {#if loyaltyData}
              <div class="flex items-center gap-3">
                <div class="flex flex-col items-end">
                   <span class="text-[8px] font-mono text-gray-500 uppercase">Current_Balance</span>
                   <span class="text-xs font-mono font-bold text-amber-400">{loyaltyData.available_points} PTS</span>
                </div>
                <div class="w-px h-6 bg-white/10"></div>
                <div class="flex flex-col items-end">
                   <span class="text-[8px] font-mono text-gray-500 uppercase">User_Tier</span>
                   <span class="text-[10px] font-mono font-bold text-white tracking-widest">{loyaltyData.tier}</span>
                </div>
              </div>
            {/if}
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Point Adjustment -->
            <div class="space-y-4 bg-white/[0.02] p-4 rounded-xl border border-white/5">
               <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest block mb-2">Manual_Adjustment</span>
               <div class="flex flex-col gap-3">
                 <div class="flex gap-4">
                    <div class="flex-1">
                      <label class="text-[8px] font-mono text-gray-600 uppercase mb-1 block">Points_Delta</label>
                      <input type="number" bind:value={adjustAmount} placeholder="+/- Amount"
                        class="w-full bg-black/40 border border-white/10 rounded-lg py-2 px-3 text-[11px] font-mono text-white focus:outline-none focus:border-amber-500/50"
                      />
                    </div>
                    <div class="flex-[2]">
                      <label class="text-[8px] font-mono text-gray-600 uppercase mb-1 block">Adjustment_Reason</label>
                      <input type="text" bind:value={adjustNotes} placeholder="Reason for change..."
                        class="w-full bg-black/40 border border-white/10 rounded-lg py-2 px-3 text-[11px] font-mono text-white focus:outline-none focus:border-amber-500/50"
                      />
                    </div>
                 </div>
                 <button type="button" onclick={handleAdjustPoints} disabled={isAdjusting || adjustAmount === 0 || !adjustNotes}
                   class="w-full py-2.5 bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500/20 rounded-lg text-[9px] font-mono font-bold uppercase tracking-widest transition-all disabled:opacity-30 flex items-center justify-center gap-2"
                 >
                   <Plus size={12} /> Commit_Adjustment
                 </button>
               </div>
            </div>

            <!-- Mini History -->
            <div class="space-y-3">
              <div class="flex items-center gap-2 mb-1">
                <History size={10} class="text-gray-500" />
                <span class="text-[8px] font-mono text-gray-500 uppercase tracking-widest">Recent_Activity_Ledger</span>
              </div>
              <div class="max-h-[120px] overflow-y-auto custom-scrollbar space-y-2 pr-2">
                {#if loyaltyData?.history?.length > 0}
                  {#each loyaltyData.history.slice(0, 5) as tx}
                    <div class="flex items-center justify-between text-[9px] font-mono p-2 bg-white/5 rounded-lg border border-white/5">
                      <div class="flex flex-col">
                        <span class="text-gray-400 uppercase tracking-tighter">{tx.transaction_type}</span>
                        <span class="text-[8px] text-gray-600">{tx.notes || 'No notes'}</span>
                      </div>
                      <span class={tx.amount > 0 ? "text-green-400" : "text-red-400"}>
                        {tx.amount > 0 ? '+' : ''}{tx.amount} P
                      </span>
                    </div>
                  {/each}
                {:else}
                  <div class="text-[9px] font-mono text-gray-600 italic py-4 text-center">No transactions recorded.</div>
                {/if}
              </div>
            </div>
          </div>
        </div>
        {/if}

      </form>
    </div>

    <!-- Footer -->
    <div class="p-6 border-t border-white/5 bg-black/60 flex items-center justify-between relative z-10">
      <div class="flex items-center gap-2 text-[9px] font-mono text-gray-600 uppercase tracking-widest">
        <CheckCircle size={12} /> Auto_Validate: Enabled
      </div>
      <div class="flex items-center gap-3">
        <button type="button" onclick={onClose} disabled={isLoading}
          class="px-6 py-3 rounded-xl text-[10px] font-mono text-gray-500 hover:text-white bg-white/5 hover:bg-white/10 transition-colors uppercase tracking-[0.2em]"
        >
          [ ABORT ]
        </button>
        <button type="submit" form="user-config-form" disabled={isLoading}
          class="px-10 py-3 rounded-xl text-[10px] font-bold font-mono text-[#00FFFF] bg-black border border-[#00FFFF]/50 hover:border-[#00FFFF] hover:shadow-[0_0_30px_rgba(0,255,255,0.2)] transition-all uppercase tracking-[0.3em] relative group disabled:opacity-50"
        >
          <span class="relative z-10">{isLoading ? "SYNCING..." : "COMMIT_IDENTITY"}</span>
        </button>
      </div>
    </div>
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0, 255, 255, 0.1); border-radius: 10px; }
  input[type="date"]::-webkit-calendar-picker-indicator {
    filter: invert(1) sepia(100%) saturate(10000%) hue-rotate(180deg);
    cursor: pointer;
  }
</style>
