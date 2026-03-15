<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import Check from "lucide-svelte/icons/check";
  import X from "lucide-svelte/icons/x";
  import Search from "lucide-svelte/icons/search";
  import Pencil from "lucide-svelte/icons/pencil";
  import Shield from "lucide-svelte/icons/shield";
  import LayoutGrid from "lucide-svelte/icons/layout-grid";
  import List from "lucide-svelte/icons/list";
  import CircleCheck from "lucide-svelte/icons/circle-check";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import RoleCard from "./RoleCard.svelte";
  import PermissionGroup from "./PermissionGroup.svelte";
  import PermissionEditGrid from "./PermissionEditGrid.svelte";

  interface Permission {
    id: string;
    name: string;
    code: string;
    description?: string;
  }
  interface Role {
    id: string;
    code: string;
    name: string;
    permissions: Permission[];
  }

  interface RoleStyle {
    gradient: string;
    badge: string;
    border: string;
  }

  const ROLE_STYLES: Record<string, RoleStyle> = {
    CUSTOMER: {
      gradient: "from-blue-900/80 to-blue-800/40",
      badge: "bg-blue-600",
      border: "border-blue-500/40",
    },
    EDITOR: {
      gradient: "from-green-900/80 to-green-800/40",
      badge: "bg-green-500",
      border: "border-green-500/40",
    },
    MANAGER: {
      gradient: "from-purple-900/80 to-purple-800/40",
      badge: "bg-purple-500",
      border: "border-purple-500/40",
    },
    ADMIN: {
      gradient: "from-red-900/80 to-red-800/40",
      badge: "bg-red-500",
      border: "border-red-500/40",
    },
    SUPER_ADMIN: {
      gradient: "from-fuchsia-900/80 to-purple-800/40",
      badge: "bg-fuchsia-500",
      border: "border-fuchsia-400/50",
    },
  };

  interface PermissionGroupDef {
    label: string;
    icon: string;
  }

  const PERMISSION_GROUPS: Record<string, PermissionGroupDef> = {
    sys: { label: "Hệ thống", icon: "⚙️" },
    user: { label: "Người dùng", icon: "👤" },
    product: { label: "Sản phẩm", icon: "📦" },
    order: { label: "Đơn hàng", icon: "🛒" },
    content: { label: "Nội dung", icon: "📝" },
    agent: { label: "AI Agent", icon: "🤖" },
    security: { label: "Bảo mật", icon: "🔒" },
  };

  let roles = $state<Role[]>([]),
    allPermissions = $state<Permission[]>([]),
    isLoading = $state(true);
  let error = $state<string | null>(null),
    searchTerm = $state(""),
    selectedRoleId = $state<string | null>(null);
  let isEditing = $state(false),
    editPermissions = $state<Set<string>>(new Set()),
    originalPermissions = $state<Set<string>>(new Set()),
    activeGroupFilter = $state("all"),
    viewMode = $state<"grid" | "list">("grid");

  let hasChanges = $derived.by(() => {
    if (!isEditing) return false;
    if (editPermissions.size !== originalPermissions.size) return true;
    for (const p of editPermissions) { if (!originalPermissions.has(p)) return true; }
    return false;
  });

  let selectedRole = $derived(
    roles.find((r) => r.id === selectedRoleId) || null,
  );
  let groupedPermissions = $derived.by(() => {
    const groups: Record<string, Permission[]> = {};
    for (const p of allPermissions) {
      const pre = p.code.split(":")[0] || "other";
      (groups[pre] ??= []).push(p);
    }
    return groups;
  });

  let filteredPermissions = $derived.by(() => {
    let perms = allPermissions;
    if (activeGroupFilter !== "all")
      perms = perms.filter((p) => p.code.startsWith(activeGroupFilter + ":"));
    if (searchTerm) {
      const t = searchTerm.toLowerCase();
      perms = perms.filter(
        (p) =>
          p.name?.toLowerCase().includes(t) || p.code.toLowerCase().includes(t),
      );
    }
    return perms;
  });

  $effect(() => {
    (async () => {
      try {
        roles = await apiClient.get<Role[]>("/api/v1/users/roles");
        const permSet = new Map<string, Permission>();
        roles.forEach((r) =>
          r.permissions.forEach((p) => permSet.set(p.code, p)),
        );
        allPermissions = Array.from(permSet.values()).sort((a, b) =>
          a.code.localeCompare(b.code),
        );
        if (roles.length > 0) selectedRoleId = roles[0].id;
      } catch (e: unknown) {
        const err = e as Error;
        error = err.message;
      } finally {
        isLoading = false;
      }
    })();
  });

  // V22: Voice Mutation Injection - Permission Management
  $effect(() => {
    const action = nanobot.commandAction;

    if (action?.entity === "permission" || action?.entity === "role") {
      if (action.verb === "search" && action.args) {
        if (nanobot.consumeCommand("search", action.entity)) {
          searchTerm = action.args;
        }
      } else if (action.verb === "select" && action.args) {
        if (nanobot.consumeCommand("select", action.entity)) {
          const r = roles.find(
            (role) =>
              role.name.toLowerCase().includes(action.args!.toLowerCase()) ||
              role.code.toLowerCase().includes(action.args!.toLowerCase()),
          );
          if (r) selectRole(r.id);
        }
      } else if (action.verb === "edit") {
        if (nanobot.consumeCommand("edit", action.entity)) {
          startEditing();
        }
      }
    }
  });

  function selectRole(id: string) {
    selectedRoleId = id;
    isEditing = false;
    activeGroupFilter = "all";
    searchTerm = "";
  }
  function startEditing() {
    if (selectedRole) {
      const permSet = new Set(selectedRole.permissions.map((p) => p.code));
      editPermissions = new Set(permSet);
      originalPermissions = new Set(permSet);
      isEditing = true;
    }
  }
  function togglePermission(code: string) {
    if (!isEditing) return;
    const n = new Set(editPermissions);
    n.has(code) ? n.delete(code) : n.add(code);
    editPermissions = n;
  }
  function roleHasPerm(c: string) {
    return isEditing
      ? editPermissions.has(c)
      : (selectedRole?.permissions.some((p) => p.code === c) ?? false);
  }
  function getRoleStyle(c: string) {
    return (
      ROLE_STYLES[c] || {
        gradient: "from-gray-800/80 to-gray-700/40",
        badge: "bg-gray-500",
        border: "border-gray-500/40",
      }
    );
  }
  async function savePermissions() {
    if (!selectedRole || !hasChanges) return;
    try {
      await apiClient.patch(
        `/api/v1/users/${selectedRole.id}/permissions`,
        Array.from(editPermissions),
      );
      // Update local role data immediately (R4: BE is source of truth, but reflect optimistically)
      const updatedPerms = allPermissions.filter(p => editPermissions.has(p.code));
      const idx = roles.findIndex(r => r.id === selectedRole!.id);
      if (idx !== -1) {
        roles[idx] = { ...roles[idx], permissions: updatedPerms };
        roles = [...roles]; // trigger reactivity
      }
      isEditing = false;
      nanobot.addLog("RBAC updated", "Nanobot-Sec");
    } catch {
      nanobot.addLog("Update failed", "Nanobot-Sec");
    }
  }
</script>

<div class="w-full h-full flex flex-col relative">
  {#if isLoading}
    <div
      class="flex-1 flex flex-col items-center justify-center gap-4 animate-pulse"
    >
      <span
        class="text-[9px] font-mono text-fuchsia-400/40 uppercase tracking-[0.3em]"
        >Decrypting RBAC Registry...</span
      >
    </div>
  {:else if error}
    <div
      class="flex-1 flex items-center justify-center text-red-400 font-mono text-xs uppercase tracking-widest"
    >
      Connection Failure: {error}
    </div>
  {:else}
    <div class="flex-1 overflow-y-auto px-6 pb-6 space-y-6 custom-scrollbar">
      <div>
        <div class="flex items-center gap-3 mb-5">
          <div class="w-5 h-5 rounded border border-fuchsia-500/40 flex items-center justify-center bg-fuchsia-500/10">
            <Shield size={11} class="text-fuchsia-400" />
          </div>
          <span
            class="text-[10px] font-mono text-fuchsia-400/80 uppercase tracking-[0.4em] font-bold"
            >Authority_Tiers</span
          >
          <div class="flex-1 h-px bg-gradient-to-r from-fuchsia-500/20 to-transparent"></div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {#each roles as role (role.id)}
            <RoleCard
              {role}
              isSelected={selectedRoleId === role.id}
              allPermissionsCount={allPermissions.length}
              style={getRoleStyle(role.code)}
              onSelect={selectRole}
            />
          {/each}
        </div>
      </div>

      {#if selectedRole}
        <div>
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-0 mb-5">
            <div class="flex items-center gap-3">
              <div class="w-1 h-5 rounded-full bg-fuchsia-500"></div>
              <h2 class="text-sm font-bold text-white tracking-wide">Quyền hạn</h2>
              <span class="text-[9px] font-mono text-gray-600 uppercase truncate max-w-[120px] sm:max-w-none">// {selectedRole.name}</span>
            </div>
            <div class="flex items-center justify-between sm:justify-end gap-2 w-full sm:w-auto mt-2 sm:mt-0">
              <div class="flex items-center bg-white/5 rounded-lg p-0.5">
                <button
                  onclick={() => (viewMode = "grid")}
                  class="p-1.5 rounded-md transition-all {viewMode === 'grid'
                    ? 'bg-fuchsia-500/20 text-fuchsia-400'
                    : 'text-gray-600 hover:text-white'}"
                  ><LayoutGrid size={14} /></button
                >
                <button
                  onclick={() => (viewMode = "list")}
                  class="p-1.5 rounded-md transition-all {viewMode === 'list'
                    ? 'bg-fuchsia-500/20 text-fuchsia-400'
                    : 'text-gray-600 hover:text-white'}"
                  ><List size={14} /></button
                >
              </div>
              {#if !isEditing}
                <button
                  onclick={startEditing}
                  class="flex items-center gap-2 px-3 py-1.5 bg-fuchsia-500/10 border border-fuchsia-500/30 rounded-xl text-[10px] font-semibold text-fuchsia-400 hover:bg-fuchsia-500/20 transition-all"
                  ><Pencil size={12} /> Chỉnh sửa</button
                >{/if}
            </div>
          </div>

          {#if isEditing}
            <div
              class="flex flex-col sm:flex-row items-center gap-3 sm:gap-4 bg-white/[0.01] border border-white/5 p-3 sm:p-2 rounded-2xl mb-6"
            >
              <div class="flex-1 relative group w-full">
                <div
                  class="absolute inset-y-0 left-4 flex items-center pointer-events-none"
                >
                  <Search
                    size={14}
                    class="text-gray-600 group-focus-within:text-fuchsia-400 transition-colors"
                  />
                </div>
                <input
                  bind:value={searchTerm}
                  type="text"
                  placeholder="QUERY_PERMISSION_SECTOR..."
                  class="w-full bg-black/40 border border-white/5 rounded-xl py-3 pl-11 pr-4 text-[11px] font-mono text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-fuchsia-400/40 focus:ring-1 focus:ring-fuchsia-400/10 transition-all uppercase tracking-widest"
                />
              </div>
              <button
                onclick={() =>
                  (editPermissions =
                    editPermissions.size === allPermissions.length
                      ? new Set()
                      : new Set(allPermissions.map((p) => p.code)))}
                class="w-full sm:w-auto px-5 py-3 bg-fuchsia-500/10 border border-fuchsia-500/30 rounded-xl text-[10px] font-mono uppercase text-fuchsia-400 hover:bg-fuchsia-500/20 transition-all tracking-widest"
              >
                Sync_All ({editPermissions.size})
              </button>
            </div>
            <PermissionEditGrid
              {filteredPermissions}
              {roleHasPerm}
              {togglePermission}
              getGroupLabel={(p) => PERMISSION_GROUPS[p]?.label || p}
              {viewMode}
            />
          {:else}
            <div class="space-y-3 pb-6">
              {#each Object.entries(groupedPermissions) as [group, perms]}
                <PermissionGroup
                  {group}
                  {perms}
                  getGroupIcon={(g) => PERMISSION_GROUPS[g]?.icon || "📋"}
                  getGroupLabel={(g) => PERMISSION_GROUPS[g]?.label || g}
                  {roleHasPerm}
                />
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </div>

    {#if isEditing}
      <div
        class="absolute bottom-0 left-0 right-0 px-4 sm:px-8 py-3 sm:py-4 bg-[#080808]/95 backdrop-blur-xl border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-0 z-50 shadow-[0_-20px_40px_rgba(0,0,0,0.5)]"
        transition:slide
      >
        <div class="flex items-center justify-between sm:justify-start gap-4 w-full sm:w-auto">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full {hasChanges ? 'bg-fuchsia-500 animate-pulse shadow-[0_0_10px_#d946ef]' : 'bg-gray-600'}"></div>
            <span class="text-[10px] font-mono {hasChanges ? 'text-fuchsia-400' : 'text-gray-500'} uppercase tracking-widest font-bold hidden sm:inline">{hasChanges ? 'MODE: EDITS_PENDING' : 'MODE: NO_CHANGES'}</span>
            <span class="text-[9px] font-mono {hasChanges ? 'text-fuchsia-400' : 'text-gray-500'} uppercase tracking-widest font-bold sm:hidden">{hasChanges ? 'EDITS_PENDING' : 'NO_CHANGES'}</span>
          </div>
        </div>

        <div class="flex items-center gap-2 sm:gap-3 w-full sm:w-auto">
          <button
            onclick={() => (isEditing = false)}
            class="flex-1 sm:flex-none justify-center flex items-center gap-2 px-3 sm:px-6 py-3 sm:py-2.5 rounded-xl border border-white/10 text-[10px] sm:text-[10px] font-mono uppercase tracking-widest text-gray-400 hover:text-white hover:bg-white/5 transition-all"
            ><X size={14} /> <span class="hidden xs:inline">Huỷ bỏ</span><span class="xs:hidden">Hủy</span></button
          >
          <button
            onclick={savePermissions}
            disabled={!hasChanges}
            class="flex-[2] sm:flex-none justify-center flex items-center gap-2 px-3 sm:px-6 py-3 sm:py-2.5 rounded-xl text-[10px] font-mono uppercase tracking-widest transition-all {hasChanges
              ? 'bg-fuchsia-600 text-white hover:bg-fuchsia-500 shadow-[0_0_15px_rgba(217,70,239,0.3)] hover:shadow-[0_0_25px_rgba(217,70,239,0.5)]'
              : 'bg-gray-800 text-gray-600 cursor-not-allowed'}"
            ><Check size={14} /> <span class="hidden xs:inline">Cập nhật thao tác</span><span class="xs:hidden">Cập nhật</span></button
          >
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(168, 85, 247, 0.15);
  }
</style>
