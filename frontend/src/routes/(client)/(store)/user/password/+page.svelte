<script lang="ts">
  import UserPageWrapper from '$lib/components/storefront/user/UserPageWrapper.svelte';
  import PasswordForm from '$lib/components/storefront/user/PasswordForm.svelte';
</script>

<UserPageWrapper 
  title="Đổi mật khẩu" 
  description="Để bảo mật tài khoản, vui lòng không chia sẻ mật khẩu cho người khác."
>
  <div class="max-w-md">
    <PasswordForm />
  </div>
</UserPageWrapper>