<script lang="ts">
    let { data } = $props();
</script>
<div class="p-4 text-center text-blue-400 font-bold">
    Bảng Dữ Liệu Người Dùng
    <p class="text-sm text-gray-400 mt-2">Dữ liệu giả định: {data?.users?.length || 0} users.</p>
</div>
