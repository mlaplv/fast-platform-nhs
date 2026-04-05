<script lang="ts">
    import type { PageData } from './$types';
    import type { Component } from 'svelte';
    import { fade } from 'svelte/transition';

    /**
     * Elite V2.2: Home Page Orchestrator.
     * Logic: Server-side tenant detection dictates the component layer.
     */
    let { data }: { data: PageData } = $props();
    
    // Static Typing for Dynamic Component
    let DynamicComponent = $state<Component<any> | null>(null);

    // Optimized Asset Loading Lifecycle
    $effect(() => {
        let isMounted = true;
        
        const loadComponent = async () => {
            try {
                if (data.tenant === 'admin') {
                    const mod = await import("$lib/components/admin/layout/AdminDashboard.svelte");
                    if (isMounted) DynamicComponent = mod.default;
                } else {
                    const mod = await import("$lib/components/storefront/StorefrontHome.svelte");
                    if (isMounted) DynamicComponent = mod.default;
                }
            } catch (err) {
                console.error("[RootPage] Failed to load dynamic component:", err);
            }
        };

        loadComponent();
        return () => { isMounted = false; };
    });
</script>

<svelte:head>
    <title>{data.tenant === 'admin' ? 'Xohi Darkboard' : 'SmartShop Storefront'}</title>
</svelte:head>

<div class="page-container h-screen overflow-hidden bg-[#020202]">
    {#if DynamicComponent}
        <div in:fade={{ duration: 400 }}>
            <DynamicComponent 
                userEmail={data.user?.email} 
                isMobile={data.isMobile}
            />
        </div>
    {:else}
        <!-- Liquid Loading State (Viral 2026) -->
        <div class="fixed inset-0 flex items-center justify-center bg-[#020202] z-[100]">
            <div class="relative flex flex-col items-center gap-4">
                <div class="w-12 h-12 border-2 border-[#00FFFF]/20 border-t-[#00FFFF] rounded-full animate-spin shadow-[0_0_15px_rgba(0,255,255,0.1)]"></div>
                <div class="text-[9px] font-mono text-[#00FFFF]/50 tracking-[0.4em] uppercase animate-pulse">Initializing Neural Link...</div>
            </div>
        </div>
    {/if}
</div>

<style>
    .page-container {
        display: grid;
        grid-template-rows: 1fr;
    }
</style>
