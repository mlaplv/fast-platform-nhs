<script lang="ts">
    import { onMount } from 'svelte';
    let { children } = $props();
</script>

<div class="admin-layout flex min-h-screen bg-black overflow-hidden font-sans">
    <!-- Sidebar / Navigation can go here -->
    <main class="flex-1 overflow-y-auto">
        {@render children()}
    </main>
</div>

<style>
    :global(body) {
        margin: 0;
        padding: 0;
        background: black;
    }
</style>
