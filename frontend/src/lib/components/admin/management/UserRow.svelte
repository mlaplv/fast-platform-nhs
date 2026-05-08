<script lang="ts">
  // Transitions removed for speed
  import Shield from "@lucide/svelte/icons/shield";
  import MoreVertical from "@lucide/svelte/icons/more-vertical";
  import Check from "@lucide/svelte/icons/check";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Lock from "@lucide/svelte/icons/lock";
  import Unlock from "@lucide/svelte/icons/unlock";
  import Edit2 from "@lucide/svelte/icons/edit-2";
  import Trash2 from "@lucide/svelte/icons/trash-2";
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

  // R12: Optimization — Lazy calculation only on expand
  const effectivePermissions = $derived.by(() => {
    if (!isExpanded) return [];
    const perms = new Set<string>();
    (user.roles || []).forEach((r: Role) => {
      (r?.permissions || []).forEach((p: Permission) => perms.add(p.code));
    });
    return Array.from(perms).sort();
  });
</script>

<div
  class="group relative z-10 hover:z-50 flex flex-col md:grid md:grid-cols-[60px_60px_minmax(250px,2fr)_1fr_120px] md:items-center bg-[#0a0a0a] md:bg-transparent border border-white/5 md:border-none rounded-xl md:rounded-none p-4 sm:p-0 hover:bg-white/[0.04] {isExpanded
    ? 'bg-white/[0.03] border-l border-l-[#00FFFF]/50'
    : ''} {isSelected ? 'bg-[#00FFFF]/5' : ''}"
>
  <!-- Selection Column -->
  <div class="hidden md:flex items-center justify-center p-4 border-r border-white/[0.01]">
    <button 
      onclick={onToggleSelect}
      class="w-4 h-4 rounded border {isSelected ? 'bg-[#00FFFF] border-[#00FFFF]' : 'border-white/10 bg-black/40'} flex items-center justify-center transition-colors hover:border-[#00FFFF]/40 shadow-inner"
    >
      {#if isSelected}
        <Check size={12} class="text-black" />
      {/if}
    </button>
  </div>

  <!-- Expansion Column -->
  <div class="hidden md:flex items-center justify-center p-4 border-r border-white/[0.01]">
    <button
      onclick={() => onToggleExpand(user.id)}
      class="p-2 bg-black/40 hover:bg-[#00FFFF]/10 border border-transparent hover:border-[#00FFFF]/20 shadow-sm rounded-xl {isExpanded
        ? 'rotate-180 text-[#00FFFF] border-[#00FFFF]/20 bg-[#00FFFF]/5'
        : 'text-gray-500 hover:text-[#00FFFF]'}"
    >
      <ChevronDown size={14} />
    </button>
  </div>

  <!-- User Info Column -->
  <div class="sm:px-6 sm:py-5 relative z-10">
    <div class="flex items-start sm:items-center gap-3">
      <!-- Mobile Checkbox -->
      <button 
        onclick={onToggleSelect}
        class="md:hidden w-6 h-6 rounded border {isSelected ? 'bg-[#00FFFF] border-[#00FFFF]' : 'border-white/20 bg-black/40'} flex items-center justify-center transition-colors"
      >
        {#if isSelected}
          <Check size={14} class="text-black" />
        {/if}
      </button>

      <div class="md:hidden">
        <button
          onclick={() => onToggleExpand(user.id)}
          class="p-2 bg-black/40 hover:bg-[#00FFFF]/10 border border-transparent hover:border-[#00FFFF]/20 shadow-sm rounded-xl {isExpanded
            ? 'rotate-180 text-[#00FFFF] border-[#00FFFF]/20 bg-[#00FFFF]/5'
            : 'text-gray-500 hover:text-[#00FFFF]'}"
        >
          <ChevronDown size={14} />
        </button>
      </div>
      <div class="flex flex-col justify-center min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-[14px] sm:text-[13px] font-bold text-gray-100 group-hover:text-white transition-colors tracking-wide truncate">
            {user.name || "Unknown Entity"}
          </span>
          {#if user.username}
            <span class="text-[9px] font-mono font-bold bg-[#00FFFF]/10 text-[#00FFFF]/70 px-1.5 py-0.5 rounded border border-[#00FFFF]/20">@{user.username}</span>
          {/if}
          {#if user.status === "LOCKED"}
            <span class="px-2 py-0.5 rounded text-[8px] font-mono font-bold bg-red-500/20 text-red-500 uppercase tracking-widest border border-red-500/30">LOCKED</span>
          {/if}
        </div>
        
        <div class="flex items-center gap-3 mt-1.5 overflow-hidden">
          <span class="text-[10px] font-mono text-gray-400 group-hover:text-gray-300 transition-colors truncate">
            {user.email}
          </span>
          {#if user.phone}
            <span class="hidden sm:inline text-[9px] font-mono text-[#00FFFF]/30 border-l border-white/10 pl-3">
              {user.phone}
            </span>
          {/if}
          <span class="hidden lg:inline text-[9px] font-mono text-gray-600 border-l border-white/10 pl-3 uppercase">
            Joined: {new Date(user.createdAt).toLocaleDateString('vi-VN')}
          </span>
        </div>
      </div>
    </div>
  </div>

  <!-- Assigned Tiers -->
  <div class="sm:px-6 sm:py-5 mt-3 sm:mt-0 pl-11 sm:pl-0">
    <div class="flex flex-wrap gap-2">
      {#each (user.roles || []) as role}
        <span
          class="px-2.5 py-1 rounded-lg text-[9px] font-bold font-mono uppercase tracking-widest inline-flex border border-[#00FFFF]/30 bg-[#00FFFF]/5 text-[#00FFFF]/70"
        >
          {role.code}
        </span>
      {/each}
    </div>
  </div>

  <!-- Access Control Actions -->
  <div class="absolute top-4 right-4 sm:relative sm:top-0 sm:right-0 sm:px-6 sm:py-5 md:text-right relative z-30 sm:w-full">
    <div class="relative inline-block text-left group/menu {isExpanded ? 'z-50' : ''}">
      <button class="p-2 text-gray-500 hover:text-white transition-colors bg-white/5 sm:bg-transparent hover:bg-white/10 rounded-xl border border-white/5">
        <MoreVertical size={16} />
      </button>
      
      <div class="absolute right-0 top-full sm:pt-2 w-56 opacity-0 invisible group-hover/menu:opacity-100 group-hover/menu:visible duration-0 z-[var(--z-admin-hud)] origin-top-right group-hover/menu:scale-100 scale-95 mt-1 sm:mt-0 border border-white/10 rounded-xl bg-[#0a0a0a] shadow-[0_10px_40px_rgba(0,0,0,0.8)]">
        <div class="flex flex-col overflow-hidden">
          <div class="p-1 border-b border-white/5">
            <button onclick={() => onEdit(user)} class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-gray-400 hover:text-white hover:bg-white/10">
              <Edit2 size={12} class="text-[#00FFFF]/70" /><span>Modify Identity</span>
            </button>
            <button onclick={() => onToggleStatus(user.id)} class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-gray-400 hover:text-white hover:bg-white/10">
              {#if user.status === "LOCKED"}
                <Unlock size={12} class="text-[#00FFFF]/70" /><span>Unlock Entity</span>
              {:else}
                <Lock size={12} class="text-red-500/70" /><span class="text-red-400">Lock Entity</span>
              {/if}
            </button>
            <button onclick={() => onDelete(user.id)} class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[10px] font-mono tracking-wide transition-colors text-red-500/70 hover:text-red-500 hover:bg-red-500/10">
              <Trash2 size={12} /><span>Revoke Access</span>
            </button>
          </div>
          
          <div class="px-4 py-2 bg-white/[0.02] border-b border-white/5">
            <span class="text-[9px] font-mono font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
              <Shield size={10} class="text-[#00FFFF]" /> Security Tiers
            </span>
          </div>
          
          <div class="max-h-[180px] overflow-y-auto p-1 scrollbar-mission">
            {#each roles as role}
              <button
                onclick={() => onToggleRole(user.id, role.code)}
                class="w-full flex items-center justify-between px-3 py-3 rounded-lg text-[10px] font-mono tracking-wide transition-colors {(user.roles || []).some((r) => r.code === role.code) ? 'text-white bg-white/5' : 'text-gray-400 hover:text-white hover:bg-white/10'}"
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
    <div class="col-span-1 md:col-span-12 mt-4 sm:mt-0 px-2 sm:px-0">
      <div class="sm:px-16 py-4 sm:py-8 bg-black/40 sm:bg-black/30 rounded-xl sm:rounded-none border-t border-white/5">
        <div class="flex flex-col gap-5 px-3 sm:px-0">
          <div class="flex items-center gap-3 border-b border-white/5 pb-3">
            <Shield size={14} class="text-[#00FFFF]/60" />
            <div class="flex flex-col">
              <span class="text-[10px] font-mono text-white font-bold uppercase tracking-widest">Effective Permission Matrix</span>
              <span class="text-[8px] font-mono text-gray-500 uppercase tracking-tight">Derived from assigned security tiers and overrides</span>
            </div>
          </div>
          <div class="grid grid-cols-2 xs:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {#each effectivePermissions as perm}
              <div class="px-3 py-2 bg-white/[0.02] border border-white/5 rounded-lg flex items-center justify-center text-center hover:border-[#00FFFF]/20 transition-colors group/perm">
                <span class="text-[8px] font-mono text-gray-500 group-hover/perm:text-[#00FFFF] uppercase break-all leading-tight transition-colors">{perm}</span>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
