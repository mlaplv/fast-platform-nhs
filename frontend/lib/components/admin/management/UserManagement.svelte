<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import Users from "lucide-svelte/icons/users";
  import Shield from "lucide-svelte/icons/shield";
  import MoreVertical from "lucide-svelte/icons/more-vertical";
  import Check from "lucide-svelte/icons/check";
  import Search from "lucide-svelte/icons/search";
  import Info from "lucide-svelte/icons/info";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import Lock from "lucide-svelte/icons/lock";
  import Unlock from "lucide-svelte/icons/unlock";
  import UserPlus from "lucide-svelte/icons/user-plus";
  import Edit2 from "lucide-svelte/icons/edit-2";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import type { User, Role, Permission } from "$lib/types";
  import { apiClient, ApiError } from "$lib/utils/apiClient";
  import OrderPagination from "./OrderPagination.svelte";
  import UserForm from "./UserForm.svelte";

  import UserRow from "./UserRow.svelte";

  let users = $state<User[]>([]);
  let totalUsers = $state(0);
  let roles = $state<Role[]>([]);
  let isLoading = $state(true);
  let error = $state<string | null>(null);
  let searchTerm = $state("");
  let searchInput = $state("");
  let statusFilter = $state<"ALL" | "ACTIVE" | "LOCKED">("ALL");
  let expandedUserId = $state<string | null>(null);
  let editingUser = $state<User | null>(null);
  let isAddingUser = $state(false);
  let currentPage = $state(1);
  let pageSize = $state(10);

  const totalPages = $derived(Math.max(1, Math.ceil(totalUsers / pageSize)));

  async function loadUsers() {
    isLoading = true;
    try {
      const offset = (currentPage - 1) * pageSize;
      const params = new URLSearchParams({ limit: pageSize.toString(), offset: offset.toString() });
      if (statusFilter !== "ALL") params.append("status", statusFilter);
      if (searchTerm) params.append("search", searchTerm);

      const [uRes, rData] = await Promise.all([
        apiClient.get<{ data: User[]; total: number }>(`/api/v1/users?${params.toString()}`),
        roles.length ? Promise.resolve(null) : apiClient.get<Role[]>("/api/v1/users/roles"),
      ]);
      users = uRes.data;
      totalUsers = uRes.total;
      if (rData) roles = rData;
    } catch (e: unknown) {
      const err = e as Error;
      error = err.message;
      users = [];
      totalUsers = 0;
    } finally {
      isLoading = false;
    }
  }

  $effect(() => { loadUsers(); });

  let searchTimer: any;
  function handleSearchInput(e: Event) {
    const val = (e.target as HTMLInputElement).value;
    searchInput = val;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { searchTerm = val; currentPage = 1; }, 400);
  }

  function handleStatusChange(status: "ALL" | "ACTIVE" | "LOCKED") {
    if (statusFilter !== status) { statusFilter = status; currentPage = 1; }
  }

  async function toggleRole(userId: string, roleCode: string) {
    const user = users.find((u) => u.id === userId);
    if (!user) return;
    const currentRoles = user.roles.map((r: Role) => r.code);
    const newRoles = currentRoles.includes(roleCode)
      ? currentRoles.filter((c: string) => c !== roleCode)
      : [...currentRoles, roleCode];
    try {
      const updatedUser = await apiClient.patch<User>(`/api/v1/users/${userId}/roles`, newRoles);
      const idx = users.findIndex((u) => u.id === userId);
      users[idx] = updatedUser;
    } catch (e: unknown) {
      nanobot.addLog(`Update Error: ${(e as Error).message}`, "Nanobot-Sec");
    }
  }

  async function toggleUserStatus(userId: string) {
    const user = users.find((u) => u.id === userId);
    if (!user) return;
    const newStatus = user.status === "LOCKED" ? "ACTIVE" : "LOCKED";
    try {
      const updated = await apiClient.patch<User>(`/api/v1/users/${userId}`, { status: newStatus });
      const idx = users.findIndex((u) => u.id === userId);
      users[idx] = { ...users[idx], ...updated };
    } catch (e: any) {
      nanobot.addLog(`Status Update Error: ${e.message}`, "Nanobot-Sec");
    }
  }

  async function deleteUser(userId: string) {
    if (!confirm("Are you sure you want to permanently revoke this access identity?")) return;
    try {
      await apiClient.patch(`/api/v1/users/${userId}/delete`, {});
      await loadUsers();
    } catch (e: any) {
      nanobot.addLog(`Deletion Error: ${e.message}`, "Nanobot-Sec");
    }
  }

  $effect(() => {
    const data = nanobot.currentData;
    if (data?.ui_action === "show_user_management" && data?.intent_type === "MUTATE" && !editingUser && !isAddingUser) {
      editingUser = { id: "", name: data.name || "", email: data.email || "", status: "ACTIVE", roles: [], permissions: [] } as any;
      isAddingUser = true;
      nanobot.clearCurrentData();
    }
  });

  function startAddingUser() {
    editingUser = { id: "", name: "", email: "", status: "ACTIVE", roles: [], permissions: [] } as any;
    isAddingUser = true;
  }
</script>

<div class="w-full h-full flex flex-col relative bg-[#050505]">
  <div class="flex flex-col xl:flex-row xl:items-center gap-4 bg-white/[0.02] border border-white/10 p-3 sm:p-2.5 rounded-2xl">
    <div class="flex-1 relative group w-full xl:min-w-[250px]">
      <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
        <Search size={16} class="text-gray-500 group-focus-within:text-[#00FFFF] group-focus-within:scale-110 transition-all" />
      </div>
      <input
        value={searchInput}
        oninput={handleSearchInput}
        type="text"
        placeholder="QUERY_IDENTITY..."
        class="w-full bg-black/50 border border-white/5 rounded-xl py-3 pl-12 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-[#00FFFF]/50 focus:ring-2 focus:ring-[#00FFFF]/20 transition-all uppercase tracking-widest shadow-inner shadow-black/50"
      />
    </div>

    <div class="flex flex-col sm:flex-row xl:items-center gap-4 xl:gap-0 mt-2 xl:mt-0">
      <div class="flex items-center gap-2 sm:gap-1 px-1 sm:px-2 xl:border-l xl:border-white/10 xl:pl-4 overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
        {#each ["ALL", "ACTIVE", "LOCKED"] as status}
          <button
            onclick={() => handleStatusChange(status as any)}
            class="px-4 py-2 rounded-lg text-[9px] font-mono font-bold uppercase tracking-widest transition-all flex-shrink-0 {statusFilter === status
              ? status === 'LOCKED'
                ? 'bg-red-500/20 text-red-500 border border-red-500/30 ring-1 ring-red-500/30'
                : 'bg-[#00FFFF]/20 text-[#00FFFF] border border-[#00FFFF]/30 ring-1 ring-[#00FFFF]/30'
              : 'text-gray-500 hover:text-gray-300 border border-transparent hover:bg-white/5'}"
          >
            {status}
          </button>
        {/each}
      </div>

      <div class="flex items-center gap-2 sm:gap-3 xl:border-l xl:border-white/10 xl:pl-4 pr-1 sm:pr-2 justify-between sm:justify-start">
        <div class="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 uppercase tracking-widest bg-black/40 sm:bg-transparent px-2 sm:px-0 py-1.5 sm:py-0 rounded-lg sm:rounded-none">
          <span class="hidden sm:inline">Show</span>
          <select
            value={pageSize}
            onchange={(e) => { pageSize = Number((e.target as HTMLSelectElement).value); currentPage = 1; }}
            class="bg-transparent sm:bg-black/60 border-none sm:border sm:border-white/10 rounded-md px-1 sm:px-1.5 py-1 text-[#00FFFF] text-[10px] sm:text-[9px] font-mono font-bold focus:outline-none cursor-pointer appearance-none text-center"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
          <span class="opacity-50 sm:opacity-100">/ {totalUsers}</span>
        </div>

        <div class="flex items-center gap-2 sm:gap-3">
          <button onclick={loadUsers} title="Force Resync"
            class="p-2.5 sm:p-2.5 text-gray-500 hover:text-[#00FFFF] border border-white/5 hover:border-[#00FFFF]/30 rounded-xl bg-black/40 hover:bg-[#00FFFF]/10 transition-all hidden sm:block"
          >
            <RefreshCw size={14} class={isLoading ? "animate-spin text-[#00FFFF]" : ""} />
          </button>

          <button onclick={startAddingUser} title="Create New Identity"
            class="p-2.5 sm:px-4 sm:py-2 text-[#00FFFF] hover:bg-[#00FFFF]/10 border border-[#00FFFF]/20 rounded-xl bg-black/40 transition-all flex items-center justify-center gap-2 group"
          >
            <UserPlus size={14} class="group-hover:scale-110 transition-transform" />
            <span class="text-[10px] sm:text-[9px] font-mono font-bold uppercase tracking-widest hidden sm:inline">Add_Node</span>
          </button>
        </div>
    </div>
  </div>
</div>

<div class="flex-1 overflow-y-auto custom-scrollbar">
  {#if isLoading}
    <div class="h-full flex flex-col items-center justify-center gap-4">
      <div class="w-8 h-8 border-2 border-[#00FFFF]/10 border-t-[#00FFFF] rounded-full animate-spin"></div>
      <span class="text-[9px] font-mono text-[#00FFFF]/40 uppercase tracking-[0.3em]">Synchronizing Registry...</span>
    </div>
  {:else if error}
    <div class="h-full flex items-center justify-center text-red-500 font-mono text-xs uppercase tracking-widest">
      Connection Failure: {error}
    </div>
  {:else if users.length === 0}
    <div class="h-full flex flex-col items-center justify-center text-gray-600 font-mono text-[10px] uppercase tracking-widest gap-2">
      <span>No matching entities found in current sector</span>
      <button onclick={() => { searchInput = ""; searchTerm = ""; currentPage = 1; }}
        class="text-[#00FFFF]/40 hover:text-[#00FFFF] transition-colors">[ RESET_FILTER ]</button>
    </div>
  {:else}
    <div class="pl-0 sm:pl-6 sm:border-l sm:border-white/5 sm:ml-4 my-2 mb-[80px]">
      
      <!-- Responsive Table Header -->
      <div class="hidden md:grid grid-cols-[minmax(250px,2fr)_1fr_100px] gap-4 px-6 py-4 bg-black/50 border-b border-white/10 shadow-inner text-[9px] font-mono text-gray-500 uppercase tracking-widest font-bold">
        <div>Identity_Signature</div>
        <div>Assigned_Tiers</div>
        <div class="text-right">Access_Control</div>
      </div>

      <div class="flex flex-col gap-4 sm:gap-0 sm:divide-y sm:divide-white/[0.02] px-4 sm:px-0">
        {#each users as user (user.id)}
          <UserRow 
            {user} 
            {roles} 
            isExpanded={expandedUserId === user.id}
            onToggleExpand={(id) => expandedUserId = expandedUserId === id ? null : id}
            onToggleRole={toggleRole}
            onToggleStatus={toggleUserStatus}
            onDelete={deleteUser}
            onEdit={(u) => editingUser = u}
          />
        {/each}
      </div>
    </div>
  {/if}
</div>

  <div class="absolute bottom-0 left-0 right-0">
    <OrderPagination bind:currentPage {totalPages} {pageSize} totalItems={totalUsers} />
  </div>
</div>

{#if editingUser}
  <UserForm
    editingId={isAddingUser ? null : editingUser.id}
    initialData={editingUser}
    onClose={() => { editingUser = null; isAddingUser = false; }}
    onSuccess={async (user) => {
      if (isAddingUser) {
        await loadUsers();
      } else {
        const idx = users.findIndex((u) => u.id === user.id);
        if (idx !== -1) users[idx] = { ...users[idx], ...user };
      }
      editingUser = null;
      isAddingUser = false;
    }}
  />
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 20px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0, 255, 255, 0.1); }
</style>
