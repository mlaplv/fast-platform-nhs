<script lang="ts">
  import UserPageWrapper from '$lib/components/storefront/user/UserPageWrapper.svelte';
  import PurchaseList from '$lib/components/storefront/user/PurchaseList.svelte';
</script>

<UserPageWrapper 
  title="Đơn mua" 
  description="Theo dõi trạng thái và lịch sử các đơn hàng của Quý khách."
>
  <PurchaseList />
</UserPageWrapper>
