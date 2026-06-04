<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { fade } from 'svelte/transition';
    import XohiLogo from '$lib/components/admin/XohiLogo.svelte';

    // We'll dynamically load vis-network from CDN to keep the bundle size small
    let container: HTMLDivElement;
    let network = $state<any>(null);
    let isLoading = $state(true);

    // Props (Svelte 5 Runes)
    let {
        data = { nodes: [], edges: [] },
        height = "600px",
        onNodeSelect = () => {}
    } = $props();

    onMount(() => {
        // Dynamically load vis-network script
        const script = document.createElement('script');
        script.id = "vis-network-script";
        script.src = "https://unpkg.com/vis-network/standalone/umd/vis-network.min.js";
        script.onload = () => {
            initGraph();
        };
        document.head.appendChild(script);

        return () => {
            if (network) {
                network.destroy();
            }
            // Elite V2.2: Extreme resource discipline - purge DOM script pollution and release heavy global objects
            const el = document.getElementById("vis-network-script");
            if (el) el.remove();
            
            if ((window as any).vis) {
                try {
                    delete (window as any).vis;
                } catch {
                    (window as any).vis = undefined;
                }
            }
        };
    });

    function initGraph() {
        if (!container || !(window as any).vis) return;
        isLoading = false;

        const vis = (window as any).vis;

        // Default Cyberpunk / Dark Mode Options for XOHI Trinity Core
        const options = {
            nodes: {
                shape: 'dot',
                size: 20,
                font: {
                    size: 14,
                    color: '#ffffff',
                    face: 'system-ui',
                    strokeWidth: 2,
                    strokeColor: '#000000'
                },
                borderWidth: 2,
                shadow: true
            },
            edges: {
                width: 1.5,
                color: { color: 'rgba(6, 182, 212, 0.4)', highlight: '#06b6d4' },
                smooth: {
                    type: 'continuous'
                },
                font: {
                    size: 11,
                    color: 'rgba(255, 255, 255, 0.6)',
                    face: 'system-ui',
                    align: 'middle',
                    background: 'rgba(0, 0, 0, 0.5)'
                },
                arrows: {
                    to: { enabled: true, scaleFactor: 0.5 }
                }
            },
            physics: {
                forceAtlas2Based: {
                    gravitationalConstant: -100,
                    centralGravity: 0.01,
                    springLength: 200,
                    springConstant: 0.08
                },
                maxVelocity: 50,
                solver: 'forceAtlas2Based',
                timestep: 0.35,
                stabilization: { iterations: 150 }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true
            }
        };

        network = new vis.Network(container, data, options);
        
        // Add some interaction events
        network.on("selectNode", function (params: any) {
            if (params.nodes && params.nodes.length > 0) {
                onNodeSelect(params.nodes[0]);
            }
        });
    }

    // Reactively update graph if data changes (Svelte 5 $effect)
    $effect(() => {
        if (network && data && data.nodes && data.nodes.length > 0) {
            network.setData(data);
        }
    });
</script>

<div class="relative w-full rounded-3xl overflow-hidden border border-cyan-500/20 bg-[#050505]" style="height: {height};">
    {#if isLoading}
        <div class="absolute inset-0 flex flex-col items-center justify-center bg-black/50 backdrop-blur-sm z-10" in:fade>
            <XohiLogo variant="simple" size={60} />
            <p class="mt-6 text-xs font-mono font-black tracking-[0.3em] text-cyan-400 animate-pulse">
                INITIALIZING TRINITY KNOWLEDGE GRAPH...
            </p>
        </div>
    {/if}
    <div bind:this={container} class="w-full h-full"></div>
</div>

<style>
    /* Add any specific styles if needed, vis-network canvas takes full width/height */
</style>
