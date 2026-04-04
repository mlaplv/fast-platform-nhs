<script lang="ts">
  import PermissionManagement from "$lib/components/admin/management/PermissionManagement.svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { onMount } from "svelte";

  onMount(() => {
    nanobot.addLog("Accessing Permission Registry", "SYS", "info");
  });
</script>

<div class="h-full w-full">
  <PermissionManagement />
</div>
