<script lang="ts">
  import PermissionManagement from "$lib/components/admin/management/PermissionManagement.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { onMount } from "svelte";

  onMount(() => {
    nanobot.addLog("Accessing Permission Registry", "SYS", "info");
  });
</script>

<div class="h-full w-full">
  <PermissionManagement />
</div>
