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

  function togglePermissionMatrix(id: string) {
    expandedUserId = expandedUserId === id ? null : id;
  }

  function getUniquePermissions(user: User) {
    const perms = new Set<string>();
    user.roles.forEach((r: Role) => { r.permissions.forEach((p: Permission) => perms.add(p.code)); });
    return Array.from(perms).sort();
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

  // V22: Voice Mutation Injection - Listen for XoHi data payloads
  $effect(() => {
    const data = nanobot.currentData;
    if (data?.ui_action === "show_user_management" && data?.intent_type === "MUTATE" && !editingUser && !isAddingUser) {
      // Auto-open create form with pre-filled AI data
      editingUser = {
        id: "",
        name: data.name || "",
        email: data.email || "",
        status: "ACTIVE",
        roles: [],
        permissions: []
      } as any;
      isAddingUser = true;
      // V22: Consume the data so it doesn't re-trigger on re-mount
      nanobot.clearCurrentData();
    }
  });

  function startAddingUser() {
    editingUser = { id: "", name: "", email: "", status: "ACTIVE", roles: [], permissions: [] } as any;
    isAddingUser = true;
  }
</script>

<div class="w-full h-full flex flex-col relative bg-black/40 backdrop-blur-xl">
  <div
    class="sticky top-0 z-20 bg-black/80 backdrop-blur-xl border-b border-white/[0.05] p-6 flex flex-col gap-6 shadow-[0_10px_30px_rgba(0,0,0,0.5)]"
  >
    <div
      class="flex items-center gap-4 bg-white/[0.02] border border-white/10 p-2.5 rounded-2xl shadow-inner backdrop-blur-md"
    >
      <div class="flex-1 relative group">
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
      <div class="flex items-center gap-2 px-2 border-l border-white/10 pl-4">
        {#each ["ALL", "ACTIVE", "LOCKED"] as status}
          <button
            onclick={() => handleStatusChange(status as any)}
            class="px-4 py-2 rounded-lg text-[9px] font-mono font-bold uppercase tracking-widest transition-all {statusFilter === status
              ? status === 'LOCKED'
                ? 'bg-red-500/20 text-red-500 border border-red-500/30'
                : 'bg-[#00FFFF]/20 text-[#00FFFF] border border-[#00FFFF]/30'
              : 'text-gray-500 hover:text-gray-300 border border-transparent hover:bg-white/5'}"
          >
            {status}
          </button>
        {/each}
      </div>

      <div class="flex items-center gap-3 border-l border-white/10 pl-4">
        <div class="flex items-center gap-1.5 text-[9px] font-mono text-gray-500 uppercase tracking-widest">
          <span>Show</span>
          <select
            value={pageSize}
            onchange={(e) => { pageSize = Number((e.target as HTMLSelectElement).value); currentPage = 1; }}
            class="bg-black/60 border border-white/10 rounded-md px-1.5 py-1 text-[#00FFFF] text-[9px] font-mono font-bold focus:outline-none focus:border-[#00FFFF]/50 cursor-pointer appearance-none text-center w-12"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
          <span>of {totalUsers}</span>
        </div>

        <button onclick={loadUsers} title="Force Resync"
          class="p-2.5 text-gray-500 hover:text-[#00FFFF] border border-white/5 hover:border-[#00FFFF]/30 rounded-xl bg-black/40 hover:bg-[#00FFFF]/10 transition-all"
        >
          <RefreshCw size={14} class={isLoading ? "animate-spin text-[#00FFFF]" : ""} />
        </button>

        <button onclick={startAddingUser} title="Create New Identity"
          class="p-2.5 text-[#00FFFF] hover:bg-[#00FFFF]/10 border border-[#00FFFF]/20 rounded-xl bg-black/40 transition-all flex items-center gap-2 group"
        >
          <UserPlus size={14} class="group-hover:scale-110 transition-transform" />
          <span class="text-[9px] font-mono font-bold uppercase tracking-widest hidden sm:inline">Add_Node</span>
        </button>
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
      <div class="pl-6 border-l border-white/5 ml-4 my-2 mb-[80px]">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-black/50 border-b border-white/10 shadow-inner">
              <th class="px-6 py-4 text-[9px] font-mono text-gray-500 uppercase tracking-widest font-bold">Identity_Signature</th>
              <th class="px-6 py-4 text-[9px] font-mono text-gray-500 uppercase tracking-widest font-bold">Assigned_Tiers</th>
              <th class="px-6 py-4 text-[9px] font-mono text-gray-500 uppercase tracking-widest font-bold text-right">Access_Control</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/[0.02]">
            {#each users as user (user.id)}
              <tr
                class="hover:bg-white/[0.03] transition-colors duration-300 group relative z-10 hover:z-50 focus-within:z-50 {expandedUserId === user.id ? 'bg-white/[0.03] border-l border-l-[#00FFFF]/50' : ''}"
              >
                <td class="px-6 py-5 relative z-10">
                  <div class="absolute inset-y-0 left-0 w-[2px] bg-gradient-to-b from-[#00FFFF]/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <div class="flex items-center gap-3">
                    <button
                      onclick={() => togglePermissionMatrix(user.id)}
                      class="p-2 bg-black/40 hover:bg-[#00FFFF]/10 border border-transparent hover:border-[#00FFFF]/20 shadow-sm rounded-xl transition-all {expandedUserId === user.id ? 'rotate-180 text-[#00FFFF] border-[#00FFFF]/20 bg-[#00FFFF]/5' : 'text-gray-500 hover:text-[#00FFFF]'}"
                    >
                      <ChevronDown size={14} />
                    </button>
                    <div class="flex flex-col justify-center">
                      <span class="text-[13px] font-bold text-gray-100 group-hover:text-white transition-colors tracking-wide flex items-center gap-2">
                        {user.name || "Unknown Entity"}
                        {#if user.status === "LOCKED"}
                          <span class="px-2 py-0.5 rounded text-[8px] font-mono font-bold bg-red-500/20 text-red-500 uppercase tracking-widest border border-red-500/30">LOCKED</span>
                        {/if}
                      </span>
                      <span class="text-[10px] font-mono text-gray-500 mt-1 uppercase tracking-widest group-hover:text-[#00FFFF]/50 transition-colors">{user.email}</span>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-5">
                  <div class="flex flex-wrap gap-2">
                    {#each user.roles as role}
                      <span class="px-3 py-1.5 rounded-lg text-[9px] font-bold font-mono uppercase tracking-widest shadow-inner inline-flex border border-[#00FFFF]/40 bg-[#00FFFF]/10 text-[#00FFFF]">
                        {role.code}
                      </span>
                    {/each}
                  </div>
                </td>
                <td class="px-6 py-5 text-right relative z-10 w-[120px]">
                  <div class="relative inline-block text-left group/menu">
                    <button class="p-2 text-gray-500 hover:text-white transition-colors hover:bg-white/10 rounded-xl">
                      <MoreVertical size={16} />
                    </button>
                    <div class="absolute right-0 pt-2 w-56 opacity-0 invisible group-hover/menu:opacity-100 group-hover/menu:visible transition-all duration-300 z-50 origin-top-right group-hover/menu:scale-100 scale-95">
                      <div class="bg-[#0a0a0a]/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden">
                        <div class="p-1 border-b border-white/5">
                          <button onclick={() => (editingUser = user)}
                            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-gray-400 hover:text-white hover:bg-white/10">
                            <Edit2 size={12} class="text-[#00FFFF]/70" /><span>Modify Identity</span>
                          </button>
                          <button onclick={() => toggleUserStatus(user.id)}
                            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-gray-400 hover:text-white hover:bg-white/10">
                            {#if user.status === "LOCKED"}
                              <Unlock size={12} class="text-[#00FFFF]/70" /><span>Unlock Entity</span>
                            {:else}
                              <Lock size={12} class="text-red-500/70" /><span class="text-red-400">Lock Entity</span>
                            {/if}
                          </button>
                          <button onclick={() => deleteUser(user.id)}
                            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-red-500/70 hover:text-red-500 hover:bg-red-500/10">
                            <Trash2 size={12} /><span>Revoke Access</span>
                          </button>
                        </div>
                        <div class="px-4 py-2 bg-white/[0.02] border-b border-white/5">
                          <span class="text-[9px] font-mono font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
                            <Shield size={10} class="text-[#00FFFF]" /> Assign Security Tier
                          </span>
                        </div>
                        <div class="max-h-[180px] overflow-y-auto custom-scrollbar p-1">
                          {#each roles as role}
                            <button onclick={() => toggleRole(user.id, role.code)}
                              class="w-full flex items-center justify-between px-3 py-3 rounded-lg text-[10px] font-mono tracking-wide transition-colors {user.roles.some((r: Role) => r.code === role.code)
                                ? 'text-white bg-white/5' : 'text-gray-400 hover:text-white hover:bg-white/10'}">
                              <span>{role.name}</span>
                              {#if user.roles.some((r: Role) => r.code === role.code)}
                                <Check size={14} class="text-[#00FFFF] drop-shadow-[0_0_5px_rgba(0,255,255,0.5)]" />
                              {/if}
                            </button>
                          {/each}
                        </div>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>

              {#if expandedUserId === user.id}
                <tr>
                  <td colspan="3" class="p-0">
                    <div class="px-16 py-6 bg-black/20 transition-all duration-300">
                      <div class="flex flex-col gap-4">
                        <div class="flex items-center gap-2">
                          <Lock size={12} class="text-[#FFB800]/60" />
                          <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Effective Permission Matrix</span>
                        </div>
                        <div class="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                          {#each getUniquePermissions(user) as perm}
                            <div class="px-2 py-1 bg-white/[0.02] border border-white/5 rounded-lg flex items-center justify-center">
                              <span class="text-[8px] font-mono text-gray-400 uppercase">{perm}</span>
                            </div>
                          {/each}
                        </div>
                        {#if getUniquePermissions(user).length === 0}
                          <span class="text-[9px] font-mono text-gray-700 italic">No valid permissions found in sector hierarchy.</span>
                        {/if}
                      </div>
                    </div>
                  </td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
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
