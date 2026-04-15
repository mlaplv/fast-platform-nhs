<script lang="ts">
  import { Edit3, Trash2, MapPin } from 'lucide-svelte';
  import { fade } from 'svelte/transition';

  interface Address {
    id: string;
    name: string;
    phone: string;
    address: string;
    city: string;
    ward: string;
    isDefault: boolean;
  }

  interface Props {
    addresses: Address[];
    onEdit: (addr: Address) => void;
    onDelete: (id: string) => void;
    onSetDefault: (id: string) => void;
  }

  let { addresses, onEdit, onDelete, onSetDefault }: Props = $props();
</script>

<div class="space-y-4">
  {#if addresses.length === 0}
    <div class="py-10 text-center text-stone-400 italic text-sm">Chưa có địa chỉ nào.</div>
  {:else}
    {#each addresses as addr (addr.id)}
      <div class="bg-white p-4 border border-stone-100 rounded-sm" in:fade>
        <div class="flex justify-between items-start mb-2">
           <div>
             <span class="text-[13px] font-bold text-stone-800">{addr.name}</span>
             {#if addr.isDefault}
               <span class="ml-2 px-1.5 py-0.5 border border-luxury-copper text-luxury-copper text-[9px] font-black uppercase tracking-widest">Mặc định</span>
             {/if}
           </div>
           <div class="flex gap-2">
             <button onclick={() => onEdit(addr)} class="text-stone-400 hover:text-luxury-copper"><Edit3 class="w-4 h-4" /></button>
             {#if !addr.isDefault}
               <button onclick={() => onDelete(addr.id)} class="text-stone-400 hover:text-red-400"><Trash2 class="w-4 h-4" /></button>
             {/if}
           </div>
        </div>
        <p class="text-[12px] text-stone-600">{addr.address}, {addr.ward}, {addr.city}</p>
        <p class="text-[12px] text-stone-500 mt-1">{addr.phone}</p>
        {#if !addr.isDefault}
            <button onclick={() => onSetDefault(addr.id)} class="mt-3 text-[10px] font-bold uppercase text-stone-500 hover:text-stone-800 border border-stone-200 px-2 py-1">Thiết lập mặc định</button>
        {/if}
      </div>
    {/each}
  {/if}
</div>
