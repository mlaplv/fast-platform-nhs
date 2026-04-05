<script lang="ts">
    import type { PageData } from './$types';
    import { fade } from 'svelte/transition';
    import type { Component } from 'svelte';

    /**
     * ELITE V2.2 - MISSION CONTROL HUB
     * Logic: Zero-latency component selection based on verified tenant data.
     * Rule: Static Typing (No 'any'), Rune-based reactivity.
     */
    let { data }: { data: PageData } = $props();

    // SSR-Safe Dynamic Import Engine (Code-Splitting preserved)
    // Types explicitly defined to avoid 'any'
    interface DynamicModule { default: Component<any> }; // Props are passed dynamically

    const loadAdmin = (): Promise<DynamicModule> => import("$lib/components/admin/layout/AdminDashboard.svelte");
    const loadStorefront = (): Promise<DynamicModule> => import("$lib/components/storefront/StorefrontHome.svelte");
</script>

<svelte:head>
    <title>{data.tenant === 'admin' ? 'Xohi Darkboard' : 'SmartShop Storefront'}</title>
</svelte:head>

<div class="page-container h-screen overflow-hidden bg-[#010101]">
    {#if data.tenant === 'admin'}
        {#await loadAdmin()}
            <!-- Liquid Loading State (Viral 2026) -->
            <div class="fixed inset-0 flex items-center justify-center bg-[#010101] z-[100]">
                <div class="relative flex flex-col items-center gap-4">
                    <div class="w-12 h-12 border-2 border-[#00FFFF]/20 border-t-[#00FFFF] rounded-full animate-spin shadow-[0_0_15px_rgba(0,255,255,0.1)]"></div>
                    <div class="text-[9px] font-mono text-[#00FFFF]/50 tracking-[0.4em] uppercase animate-pulse">Initializing Neural Link...</div>
                </div>
            </div>
        {:then mod}
            <div in:fade={{ duration: 300 }}>
                <mod.default 
                    userEmail={data.user?.email} 
                    isMobile={data.isMobile}
                />
            </div>
        {:catch err}
             <div class="fixed inset-0 flex items-center justify-center text-red-500 font-mono text-xs p-4 text-center">
                [SYSTEM FAULT] AI_CORE_LOAD_FAILED<br/>{err.message}
             </div>
        {/await}
    {:else}
        {#await loadStorefront()}
            <!-- Liquid Loading State (Viral 2026) -->
            <div class="fixed inset-0 flex items-center justify-center bg-[#010101] z-[100]">
                <div class="relative flex flex-col items-center gap-4">
                    <div class="w-12 h-12 border-2 border-[#00FFFF]/20 border-t-[#00FFFF] rounded-full animate-spin shadow-[0_0_15px_rgba(0,255,255,0.1)]"></div>
                    <div class="text-[9px] font-mono text-[#00FFFF]/50 tracking-[0.4em] uppercase animate-pulse">Initializing Neural Link...</div>
                </div>
            </div>
        {:then mod}
             <div in:fade={{ duration: 300 }}>
                <mod.default 
                    userEmail={data.user?.email} 
                    isMobile={data.isMobile}
                />
            </div>
        {:catch err}
             <div class="fixed inset-0 flex items-center justify-center text-red-500 font-mono text-xs p-4 text-center">
                [SYSTEM FAULT] STOREFRONT_LOAD_FAILED<br/>{err.message}
             </div>
        {/await}
    {/if}
</div>

<style>
    .page-container {
        display: grid;
        grid-template-rows: 1fr;
    }
</style>
