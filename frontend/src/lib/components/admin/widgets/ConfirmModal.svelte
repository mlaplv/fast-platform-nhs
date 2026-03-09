<script lang="ts">
    let { data } = $props();
</script>
<div class="p-4 text-center text-red-400 font-bold bg-red-950/30 rounded border border-red-900">
    ⚠️ {data?.message || 'Bạn có chắc chắn muốn thực hiện hành động này?'}
    <div class="mt-4 flex justify-center gap-4">
        <button class="px-4 py-2 bg-red-600 rounded text-white">Xác nhận</button>
        <button class="px-4 py-2 bg-gray-700 rounded text-white">Hủy bỏ</button>
    </div>
</div>
