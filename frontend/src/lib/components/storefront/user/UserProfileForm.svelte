<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount } from 'svelte';

  const ui = getClientUi();

  let name = $state(authStore.user?.name || '');
  let email = $state(authStore.user?.email || '');
  let username = $state(authStore.user?.username || '');
  let gender = $state(authStore.user?.gender || 'OTHER');
  let dob = $state(authStore.user?.dob ? new Date(authStore.user.dob) : new Date());
  
  let birthDay = $state(dob.getDate());
  let birthMonth = $state(dob.getMonth() + 1);
  let birthYear = $state(dob.getFullYear());
  let avatarUrl = $state(authStore.user?.avatar_url || '');

  let isSaving = $state(false);
  let isUploading = $state(false);
  let fileInput = $state<HTMLInputElement>();

  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const years = Array.from({ length: 100 }, (_, i) => new Date().getFullYear() - i);

  async function handleSave() {
    isSaving = true;
    try {
      const updatedDob = new Date(birthYear, birthMonth - 1, birthDay).toISOString();
      const res = await fetch('/api/v1/client/user/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          gender,
          dob: updatedDob,
          avatar_url: avatarUrl
        })
      });
      if (res.ok) {
        if (authStore.user) {
          authStore.user.name = name;
          authStore.user.gender = gender;
          authStore.user.dob = updatedDob;
          authStore.user.avatar_url = avatarUrl;
        }
        ui.showToast('Cập nhật hồ sơ thành công! 🟢', 'success');
      }
    } catch (e) {
      console.error(e);
      ui.showToast('Có lỗi xảy ra khi cập nhật.', 'error');
    } finally {
      isSaving = false;
    }
  }

  async function handleAvatarUpload(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;

    if (file.size > 1 * 1024 * 1024) {
      ui.showToast('Dung lượng file tối đa 1 MB', 'warning');
      return;
    }

    isUploading = true;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/v1/client/user/avatar', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        avatarUrl = data.data.avatar_url;
        if (authStore.user) {
          authStore.user.avatar_url = avatarUrl;
        }
        ui.showToast('Thay đổi ảnh đại diện thành công!', 'success');
      }
    } catch (e) {
      console.error(e);
      ui.showToast('Lỗi upload avatar', 'error');
    } finally {
      isUploading = false;
    }
  }

  function maskEmail(email: string) {
    if (!email) return '';
    const [user, domain] = email.split('@');
    return `${user.substring(0, 2)}${'*'.repeat(user.length - 2)}@${domain}`;
  }
</script>

<div class="space-y-6">
  <div class="border-b border-gray-100 pb-5">
    <h1 class="text-[18px] font-semibold text-gray-900">Hồ Sơ Của Tôi</h1>
    <p class="text-[14px] text-gray-500 mt-1">Quản lý thông tin hồ sơ để bảo mật tài khoản</p>
  </div>

  <div class="flex pt-6">
    <div class="flex-grow pr-12 space-y-8">
      <div class="flex items-center gap-5">
        <span class="w-[150px] text-right text-[14px] text-gray-400 font-medium">Tên đăng nhập</span>
        <div class="flex-grow flex flex-col gap-1.5">
          <span class="text-[14px] text-gray-900 font-semibold">{username || 'N/A'}</span>
        </div>
      </div>

      <div class="flex items-center gap-5">
        <label for="profile_name" class="w-[150px] text-right text-[14px] text-gray-400 font-medium">Tên</label>
        <div class="flex-grow">
          <input 
            id="profile_name"
            type="text" 
            bind:value={name}
            class="w-full h-10 border border-gray-200 px-3 text-[14px] outline-none focus:border-luxury-copper transition-colors" 
          />
        </div>
      </div>

      <div class="flex items-center gap-5">
        <span class="w-[150px] text-right text-[14px] text-gray-400 font-medium">Email</span>
        <div class="flex-grow text-[14px] text-gray-900 font-semibold flex items-center gap-3">
          {maskEmail(email)}
          <button class="text-blue-500 text-[13px] hover:underline font-normal">Thay Đổi</button>
        </div>
      </div>

      <!-- Gender -->
      <div class="flex items-center gap-5">
        <span class="w-[150px] text-right text-[14px] text-gray-400 font-medium">Giới tính</span>
        <div class="flex-grow flex items-center gap-6">
          {#each [['Nam', 'MALE'], ['Nữ', 'FEMALE'], ['Khác', 'OTHER']] as [label, val]}
            <label class="flex items-center gap-2.5 cursor-pointer group">
              <div class="relative w-4.5 h-4.5 rounded-full border border-gray-200 flex items-center justify-center transition-all {gender === val ? 'border-luxury-copper' : ''}">
                <input type="radio" bind:group={gender} value={val} class="absolute inset-0 opacity-0 cursor-pointer" />
                {#if gender === val}
                  <div class="w-2.5 h-2.5 bg-luxury-copper rounded-full"></div>
                {/if}
              </div>
              <span class="text-[14px] text-gray-700">{label}</span>
            </label>
          {/each}
        </div>
      </div>

      <!-- DOB -->
      <div class="flex items-center gap-5">
        <span class="w-[150px] text-right text-[14px] text-gray-400 font-medium">Ngày sinh</span>
        <div class="flex-grow flex items-center gap-4">
          <div class="relative flex-1 group">
            <select bind:value={birthDay} class="w-full h-10 border border-gray-200 px-3 pr-10 appearance-none outline-none focus:border-gray-400 text-[14px] bg-white cursor-pointer">
              {#each days as d}<option value={d}>{d}</option>{/each}
            </select>
            <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
               <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
            </div>
          </div>
          <div class="relative flex-1 group">
            <select bind:value={birthMonth} class="w-full h-10 border border-gray-200 px-3 pr-10 appearance-none outline-none focus:border-gray-400 text-[14px] bg-white cursor-pointer">
              {#each months as m}<option value={m}>Tháng {m}</option>{/each}
            </select>
            <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
               <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
            </div>
          </div>
          <div class="relative flex-1 group">
             <select bind:value={birthYear} class="w-full h-10 border border-gray-200 px-3 pr-10 appearance-none outline-none focus:border-gray-400 text-[14px] bg-white cursor-pointer">
              {#each years as y}<option value={y}>{y}</option>{/each}
            </select>
            <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
               <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Action -->
      <div class="flex items-center gap-5 pt-4">
        <label class="w-[150px]"></label>
        <button 
          onclick={handleSave}
          disabled={isSaving}
          class="px-8 py-2.5 bg-luxury-copper text-white text-[14px] rounded-[2px] hover:brightness-110 transition-all active:scale-95 disabled:bg-gray-300"
        >
          {isSaving ? 'Đang lưu...' : 'Lưu'}
        </button>
      </div>
    </div>

    <!-- Avatar Area -->
    <div class="w-[280px] shrink-0 border-l border-gray-100 flex flex-col items-center gap-4 py-4">
       <div class="w-24 h-24 rounded-full overflow-hidden border border-gray-100 shadow-sm relative group bg-gray-50 flex items-center justify-center">
          {#if isUploading}
            <div class="absolute inset-0 bg-white/60 flex items-center justify-center z-10">
               <svg class="animate-spin h-5 w-5 text-[#ee4d2d]" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            </div>
          {/if}
          
          {#if avatarUrl}
            <img src={avatarUrl} alt="Avatar" class="w-full h-full object-cover" />
          {:else}
             <div class="w-full h-full flex items-center justify-center text-2xl font-black text-gray-200 uppercase">
                {authStore.user?.name?.charAt(0).toUpperCase()}
             </div>
          {/if}
       </div>

       <input 
         type="file" 
         accept=".jpeg,.jpg,.png" 
         class="hidden" 
         bind:this={fileInput} 
         onchange={handleAvatarUpload} 
       />

       <button 
         onclick={() => fileInput?.click()}
         disabled={isUploading}
         class="px-5 py-2 border border-gray-100 text-[14px] text-gray-600 shadow-sm hover:bg-gray-50 transition-colors disabled:opacity-50"
       >
          {isUploading ? 'Đang tải...' : 'Chọn Ảnh'}
       </button>
       <div class="text-[13px] text-gray-400 flex flex-col items-center gap-1">
          <span>Dung lượng file tối đa 1 MB</span>
          <span>Định dạng: .JPEG, .PNG</span>
       </div>
    </div>
  </div>
</div>
