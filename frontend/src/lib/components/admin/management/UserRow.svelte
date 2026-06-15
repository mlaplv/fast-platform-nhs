<script lang="ts">
  // Modern Bento card design for user identities
  import Shield from "@lucide/svelte/icons/shield";
  import MoreVertical from "@lucide/svelte/icons/more-vertical";
  import Check from "@lucide/svelte/icons/check";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Lock from "@lucide/svelte/icons/lock";
  import Unlock from "@lucide/svelte/icons/unlock";
  import Edit2 from "@lucide/svelte/icons/edit-2";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Mail from "@lucide/svelte/icons/mail";
  import Phone from "@lucide/svelte/icons/phone";
  import Calendar from "@lucide/svelte/icons/calendar";
  import type { User, Role, Permission } from "$lib/types";

  let {
    user,
    roles,
    isSelected,
    onToggleSelect,
    isExpanded,
    onToggleExpand,
    onToggleRole,
    onToggleStatus,
    onDelete,
    onEdit,
  } = $props<{
    user: User;
    roles: Role[];
    isSelected: boolean;
    onToggleSelect: () => void;
    isExpanded: boolean;
    onToggleExpand: (id: string) => void;
    onToggleRole: (userId: string, roleCode: string) => void;
    onToggleStatus: (userId: string) => void;
    onDelete: (userId: string) => void;
    onEdit: (user: User) => void;
  }>();

  // Lazy calculation only on expand
  const effectivePermissions = $derived.by(() => {
    if (!isExpanded) return [];
    const perms = new Set<string>();
    (user.roles || []).forEach((r: Role) => {
      (r?.permissions || []).forEach((p: Permission) => perms.add(p.code));
    });
    return Array.from(perms).sort();
  });

  // Initials Avatar Generation
  const initials = $derived(
    (user.name || "Unknown")
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase()
  );

  // Dynamic Role Style Picker
  function getRoleStyles(roleCode: string) {
    const styles: Record<string, { bg: string; text: string; border: string; iconColor: string }> = {
      SUPER_ADMIN: {
        bg: "bg-red-500/10",
        text: "text-red-400",
        border: "border-red-500/20",
        iconColor: "text-red-400",
      },
      ADMIN: {
        bg: "bg-orange-500/10",
        text: "text-orange-400",
        border: "border-orange-500/20",
        iconColor: "text-orange-400",
      },
      STORE_MANAGER: {
        bg: "bg-amber-500/10",
        text: "text-amber-400",
        border: "border-amber-500/20",
        iconColor: "text-amber-400",
      },
      CONTENT_EDITOR: {
        bg: "bg-emerald-500/10",
        text: "text-emerald-400",
        border: "border-emerald-500/20",
        iconColor: "text-emerald-400",
      },
      CUSTOMER: {
        bg: "bg-blue-500/10",
        text: "text-blue-400",
        border: "border-blue-500/20",
        iconColor: "text-blue-400",
      },
    };
    return (
      styles[roleCode] || {
        bg: "bg-gray-500/10",
        text: "text-gray-400",
        border: "border-gray-500/20",
        iconColor: "text-gray-400",
      }
    );
  }
</script>

<div
  class="group relative z-10 hover:z-20 flex flex-col md:grid md:grid-cols-[60px_60px_minmax(250px,2fr)_1fr_120px] md:items-center bg-white/[0.01] hover:bg-white/[0.03] border border-white/5 hover:border-[#00FFFF]/20 rounded-2xl p-4 sm:p-2.5 transition-all duration-300 shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:shadow-[0_10px_35px_rgba(0,255,255,0.03)] mb-3 {isExpanded
    ? 'border-l-2 border-l-[#00FFFF] bg-white/[0.02]'
    : ''} {isSelected ? 'bg-[#00FFFF]/5 border-[#00FFFF]/30' : ''}"
>
  <!-- Selection Column -->
  <div class="hidden md:flex items-center justify-center p-4 border-r border-white/5">
    <button
      onclick={onToggleSelect}
      class="w-4 h-4 rounded border {isSelected
        ? 'bg-[#00FFFF] border-[#00FFFF]'
        : 'border-white/10 bg-black/40'} flex items-center justify-center transition-colors hover:border-[#00FFFF]/40 shadow-inner"
    >
      {#if isSelected}
        <Check size={12} class="text-black" />
      {/if}
    </button>
  </div>

  <!-- Expansion Column -->
  <div class="hidden md:flex items-center justify-center p-4 border-r border-white/5">
    <button
      onclick={() => onToggleExpand(user.id)}
      class="p-2 bg-black/40 hover:bg-[#00FFFF]/10 border border-transparent hover:border-[#00FFFF]/20 shadow-sm rounded-xl transition-all {isExpanded
        ? 'rotate-180 text-[#00FFFF] border-[#00FFFF]/20 bg-[#00FFFF]/5'
        : 'text-gray-500 hover:text-[#00FFFF]'}"
    >
      <ChevronDown size={14} />
    </button>
  </div>

  <!-- User Info Column -->
  <div class="sm:px-4 sm:py-2 relative z-10">
    <div class="flex items-center gap-4">
      <!-- Mobile Controls -->
      <div class="flex md:hidden items-center gap-2">
        <button
          onclick={onToggleSelect}
          class="w-5 h-5 rounded border {isSelected
            ? 'bg-[#00FFFF] border-[#00FFFF]'
            : 'border-white/20 bg-black/40'} flex items-center justify-center transition-colors"
        >
          {#if isSelected}
            <Check size={14} class="text-black" />
          {/if}
        </button>
        <button
          onclick={() => onToggleExpand(user.id)}
          class="p-2 bg-black/40 hover:bg-[#00FFFF]/10 border border-transparent hover:border-[#00FFFF]/20 shadow-sm rounded-xl transition-all {isExpanded
            ? 'rotate-180 text-[#00FFFF] border-[#00FFFF]/20 bg-[#00FFFF]/5'
            : 'text-gray-500 hover:text-[#00FFFF]'}"
        >
          <ChevronDown size={14} />
        </button>
      </div>

      <!-- Avatar with Live Status -->
      <div class="relative flex-shrink-0 w-11 h-11 rounded-xl bg-gradient-to-br from-white/10 to-white/5 border border-white/10 flex items-center justify-center font-mono text-xs font-bold text-white shadow-inner">
        {initials}
        <span
          class="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full border-2 border-black flex items-center justify-center {user.status === 'ACTIVE'
            ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
            : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'}"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span>
        </span>
      </div>

      <!-- Core Details -->
      <div class="flex flex-col justify-center min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-[14px] sm:text-[13px] font-bold text-gray-100 group-hover:text-white transition-colors tracking-wide truncate">
            {user.name || "Unknown Entity"}
          </span>
          {#if user.username}
            <span class="text-[9px] font-mono font-bold bg-[#00FFFF]/15 text-[#00FFFF] px-1.5 py-0.5 rounded border border-[#00FFFF]/30 shadow-sm">@{user.username}</span>
          {/if}
          {#if user.status === "LOCKED"}
            <span class="px-2 py-0.5 rounded text-[8px] font-mono font-bold bg-red-500/20 text-red-500 tracking-widest border border-red-500/30">LOCKED</span>
          {/if}
        </div>

        <div class="flex items-center gap-3 mt-1.5 overflow-hidden flex-wrap sm:flex-nowrap">
          <span class="flex items-center gap-1 text-[11px] sm:text-[10px] font-mono text-gray-400 group-hover:text-gray-300 transition-colors truncate">
            <Mail size={12} class="text-gray-600 flex-shrink-0" />
            {user.email}
          </span>
          {#if user.phone}
            <span class="flex items-center gap-1 text-[10px] font-mono text-gray-400 border-l border-white/10 pl-3">
              <Phone size={11} class="text-gray-600 flex-shrink-0" />
              {user.phone}
            </span>
          {/if}
          <span class="hidden lg:flex items-center gap-1 text-[10px] font-mono text-gray-500 border-l border-white/10 pl-3">
            <Calendar size={11} class="text-gray-700 flex-shrink-0" />
            Joined: {new Date(user.created_at || user.createdAt || Date.now()).toLocaleDateString('vi-VN')}
          </span>
        </div>
      </div>
    </div>
  </div>

  <!-- Assigned Tiers (Roles) -->
  <div class="sm:px-4 sm:py-2 mt-3 sm:mt-0 pl-[52px] sm:pl-0 border-t border-white/5 sm:border-none pt-2.5 sm:pt-0">
    <div class="flex flex-wrap gap-2">
      {#each user.roles || [] as role}
        {@const style = getRoleStyles(role.code)}
        <span
          class="flex items-center gap-1.5 px-3 py-1 rounded-xl text-[10px] font-bold font-mono tracking-wider border {style.bg} {style.text} {style.border} shadow-sm transition-all hover:brightness-110"
        >
          <Shield size={11} class={style.iconColor} />
          {role.code}
        </span>
      {/each}
    </div>
  </div>

  <!-- Access Control Actions -->
  <div class="absolute top-4 right-4 sm:relative sm:top-0 sm:right-0 sm:px-4 sm:py-2 md:text-right relative z-30 sm:w-full">
    <div class="relative inline-block text-left group/menu {isExpanded ? 'z-50' : ''}">
      <button class="p-2.5 text-gray-500 hover:text-white transition-all bg-white/5 sm:bg-transparent hover:bg-white/10 rounded-xl border border-white/5 hover:border-white/10">
        <MoreVertical size={16} />
      </button>

      <div class="absolute right-0 top-full sm:pt-2 w-56 opacity-0 invisible group-hover/menu:opacity-100 group-hover/menu:visible duration-150 z-[50] origin-top-right group-hover/menu:scale-100 scale-95 mt-1 sm:mt-0 border border-white/10 rounded-2xl bg-[#080808]/95 backdrop-blur-md shadow-[0_15px_50px_rgba(0,0,0,0.9)] transition-all">
        <div class="flex flex-col overflow-hidden">
          <div class="p-1 border-b border-white/5">
            <button
              onclick={() => onEdit(user)}
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[11px] font-mono tracking-wide transition-colors text-gray-400 hover:text-white hover:bg-white/5"
            >
              <Edit2 size={12} class="text-[#00FFFF]" />
              <span>Modify Identity</span>
            </button>
            <button
              onclick={() => onToggleStatus(user.id)}
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[11px] font-mono tracking-wide transition-colors text-gray-400 hover:text-white hover:bg-white/5"
            >
              {#if user.status === "LOCKED"}
                <Unlock size={12} class="text-[#00FFFF]" />
                <span>Unlock Entity</span>
              {:else}
                <Lock size={12} class="text-red-500" />
                <span class="text-red-400">Lock Entity</span>
              {/if}
            </button>
            <button
              onclick={() => onDelete(user.id)}
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[11px] font-mono tracking-wide transition-colors text-red-500/70 hover:text-red-500 hover:bg-red-500/10"
            >
              <Trash2 size={12} />
              <span>Revoke Access</span>
            </button>
          </div>

          <div class="px-4 py-2 bg-white/[0.02] border-b border-white/5">
            <span class="text-[9px] font-mono font-bold text-gray-500 tracking-widest flex items-center gap-2">
              <Shield size={10} class="text-[#00FFFF]" /> Security Tiers
            </span>
          </div>

          <div class="max-h-[180px] overflow-y-auto p-1 custom-scrollbar">
            {#each roles as role}
              <button
                onclick={() => onToggleRole(user.id, role.code)}
                class="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-[11px] font-mono tracking-wide transition-colors {(user.roles || []).some((r) => r.code === role.code)
                  ? 'text-white bg-white/5'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'}"
              >
                <span>{role.name}</span>
                {#if (user.roles || []).some((r) => r.code === role.code)}
                  <Check size={14} class="text-[#00FFFF]" />
                {/if}
              </button>
            {/each}
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Permission Matrix Expandable Section -->
  {#if isExpanded}
    <div class="col-span-1 md:col-span-12 mt-4 sm:mt-2 px-2 sm:px-4">
      <div class="py-4 sm:py-6 bg-black/40 rounded-2xl border border-white/5">
        <div class="flex flex-col gap-4 px-4">
          <div class="flex items-center gap-3 border-b border-white/5 pb-3">
            <Shield size={14} class="text-[#00FFFF]" />
            <div class="flex flex-col">
              <span class="text-[10px] font-mono text-white font-bold tracking-widest">Effective Permission Matrix</span>
              <span class="text-[8px] font-mono text-[#00FFFF]/50 tracking-tight">Derived from assigned security tiers and overrides</span>
            </div>
          </div>
          {#if effectivePermissions.length > 0}
            <div class="grid grid-cols-2 xs:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {#each effectivePermissions as perm}
                <div class="px-3 py-2 bg-white/[0.02] border border-white/5 rounded-xl flex items-center justify-center text-center hover:border-[#00FFFF]/30 hover:bg-[#00FFFF]/5 transition-all group/perm">
                  <span class="text-[9px] font-mono text-gray-400 group-hover/perm:text-[#00FFFF] break-all leading-tight transition-colors">{perm}</span>
                </div>
              {/each}
            </div>
          {:else}
            <div class="text-[10px] font-mono text-gray-600 italic py-2">No active permissions loaded.</div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 255, 0.1);
    border-radius: 10px;
  }
</style>
