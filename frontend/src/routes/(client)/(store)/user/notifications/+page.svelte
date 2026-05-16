<script lang="ts">
  import UserPageWrapper from '$lib/components/storefront/user/UserPageWrapper.svelte';
  import NotificationList from '$lib/components/storefront/user/NotificationList.svelte';
</script>

<UserPageWrapper 
  title="Thông báo" 
  description="Cập nhật tin tức và ưu đãi mới nhất từ hệ thống."
>
  <NotificationList />
</UserPageWrapper>