<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { fade, fly } from 'svelte/transition';
  import { Camera } from 'lucide-svelte';
  import { untrack } from 'svelte';
  import MemberCard from './MemberCard.svelte';
  import SkinProfile from './SkinProfile.svelte';

  const ui = getClientUi();

  // Profile States
  let name = $state(authStore.user?.name || '');
  let email = $state(authStore.user?.email || '');
  let username = $state(authStore.user?.username || '');
  let isEditingEmail = $state(false);
  let gender = $state(authStore.user?.gender || 'OTHER');
  let dob = $state(authStore.user?.dob ? new Date(authStore.user.dob) : new Date());

  let birthDay = $state(dob.getDate());
  let birthMonth = $state(dob.getMonth() + 1);
  let birthYear = $state(dob.getFullYear());
  let phone = $state(authStore.user?.phone || '');

  // Skin Profile States (Nested in extra_metadata)
  let skinData = $state(authStore.user?.extra_metadata?.skinProfile || {
    skinType: '',
    concerns: [],
    sensitivity: 5
  });

  // Log initial read
  console.log('📖 [Beauty Profile] Khởi tạo hồ sơ vẻ đẹp từ authStore:', $state.snapshot(skinData));

  let isSaving = $state(false);
  let activeTab = $state('basic'); // basic | beauty
  let fileInput: HTMLInputElement;

  // Handle avatar selection and upload
  async function handleAvatarUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;

    const file = target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    isSaving = true;
    try {
      const res = await apiClient.upload<{ data: { avatar_url: string } }>('/api/v1/client/user/avatar', formData);

      // Sync authStore with new avatar
      authStore.syncUser({ avatar_url: res.data.avatar_url });
      ui.showToast('Cập nhật ảnh đại diện thành công! ✨', 'success');
    } catch (e) {
      ui.showToast('Lỗi khi cập nhật ảnh đại diện.', 'error');
      console.error(e);
    } finally {
      isSaving = false;
      target.value = ''; // Reset input
    }
  }

  // Required because $state initializers only run once.
  $effect(() => {
    // Elite V3.2: Prevent infinite loops by using untrack for local state updates
    if (authStore.user) {
      const user = authStore.user;
      untrack(() => {
        name = user.name || '';
        email = user.email || '';
        username = user.username || '';
        gender = user.gender || 'OTHER';

        if (user.phone) {
          phone = user.phone;
        }

        if (user.dob) {
          const d = new Date(user.dob);
          birthDay = d.getDate();
          birthMonth = d.getMonth() + 1;
          birthYear = d.getFullYear();
        }

        if (user.extra_metadata?.skinProfile) {
          skinData = {
            ...user.extra_metadata.skinProfile
          };
          console.log('📖 [Beauty Profile] Đã cập nhật (re-hydrate) hồ sơ vẻ đẹp:', $state.snapshot(skinData));
        }
      });
    }
  });

  function generateCardNumber(id: string = '') {
    if (!id) return '';
    const cleanId = id.replace(/-/g, '').toUpperCase();
    return `${cleanId.substring(0, 4)} ${cleanId.substring(4, 8)} ${cleanId.substring(8, 12)} ${cleanId.substring(12, 16)}`.toUpperCase();
  }

  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const years = Array.from({ length: 80 }, (_, i) => new Date().getFullYear() - 10 - i);

  async function handleSave() {
    // 🛡️ Client-side Validation
    if (!name.trim()) {
      ui.showToast('Quý khách vui lòng điền họ và tên ạ.', 'warning');
      return;
    }
    if (!username.trim() || username.length < 3) {
      ui.showToast('Tên đăng nhập cần có tối thiểu 3 ký tự.', 'warning');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim() || !emailRegex.test(email)) {
      ui.showToast('Quý khách vui lòng kiểm tra lại định dạng địa chỉ email.', 'warning');
      return;
    }

    isSaving = true;
    try {
      const updatedDob = new Date(birthYear, birthMonth - 1, birthDay).toISOString();
      console.log('💾 [Beauty Profile] Đang gửi yêu cầu lưu hồ sơ vẻ đẹp:', $state.snapshot(skinData));
      const cardNumber = authStore.user?.extra_metadata?.cardNumber || generateCardNumber(authStore.user?.id);

      const res = await apiClient.patch<{ ok: boolean }>('/api/v1/client/user/profile', {
        name,
        gender,
        username,
        email,
        phone,
        dob: updatedDob,
        extra_metadata: {
          ...authStore.user?.extra_metadata,
          skinProfile: $state.snapshot(skinData),
          cardNumber
        }
      });
      console.log('✅ [Beauty Profile] Kết quả lưu từ server:', res);

      authStore.syncUser({
        name,
        gender,
        username,
        email,
        phone,
        dob: updatedDob,
        extra_metadata: {
          skinProfile: $state.snapshot(skinData),
          cardNumber
        }
      });
      console.log('✅ [Beauty Profile] Dữ liệu trong authStore sau khi sync:', $state.snapshot(authStore.user?.extra_metadata));
      isEditingEmail = false;
      ui.showToast('Thông tin của Quý khách đã được ghi nhận! ✨', 'success');
    } catch (e: unknown) {
      // 🛡️ Làm sạch Log Console: Khởi tạo cảnh báo thân thiện nếu lỗi validation
      const error = e as { status?: number; message?: string };
      if (error && typeof error === 'object' && 'status' in error) {
        if (error.status === 409 || error.status === 400 || (error.message && error.message.includes('tồn tại'))) {
          console.warn('⚠️ [Beauty Profile] Validation/Conflict:', error.message);
          ui.showToast(error.message || 'Dữ liệu không hợp lệ', 'warning');
        } else {
          console.error('❌ [Beauty Profile] Lỗi hệ thống khi cập nhật:', e);
          ui.showToast(error.message || 'Có lỗi xảy ra, mong Quý khách thứ lỗi.', 'error');
        }
      } else {
        ui.showToast('Có lỗi xảy ra, mong Quý khách thứ lỗi.', 'error');
      }
    } finally {
      isSaving = false;
    }
  }

  function maskEmail(val: string) {
    if (!val) return 'Chưa cập nhật';
    const [user, domain] = val.split('@');
    return `${user.substring(0, 3)}***@${domain}`;
  }
</script>

<div class="max-w-4xl mx-auto space-y-6 pb-20">
  <!-- Elite Header Section -->
  <div class="flex flex-col md:flex-row gap-10 items-start">
    <div class="w-full md:w-1/2">
       <MemberCard />
    </div>

    <div class="w-full md:w-1/2 flex flex-col items-center justify-center space-y-4 pt-4">
      <!-- Avatar Display (Elite V3.2) - Desktop Only -->
      {#if !ui.isMobile}
        <div class="relative group w-24 h-24">
          <div class="w-24 h-24 rounded-full overflow-hidden border-2 border-stone-100 bg-white shadow-sm transition-transform duration-700 group-hover:scale-105">
            {#if authStore.user?.avatar_url}
              <img src={authStore.user.avatar_url} alt="Avatar" class="w-full h-full object-cover" />
            {:else}
              <div class="w-full h-full flex items-center justify-center text-3xl font-serif italic text-luxury-copper bg-stone-50 uppercase">
                {authStore.user?.name?.charAt(0) || 'U'}
              </div>
            {/if}
          </div>
          <!-- Hidden file input -->
          <input
            type="file"
            accept="image/*"
            class="hidden"
            bind:this={fileInput}
            onchange={handleAvatarUpload}
          />
          <!-- Overlay Edit Button -->
          <button
            type="button"
            class="absolute bottom-0 right-0 w-8 h-8 bg-stone-900 rounded-full flex items-center justify-center text-white border-2 border-white shadow-md hover:bg-luxury-copper transition-colors z-20"
            onclick={() => fileInput.click()}
          >
            <Camera class="w-4 h-4" />
          </button>
        </div>
        <div class="text-center">
          <h2 class="text-xl font-serif italic text-stone-800">{authStore.user?.name || 'Quý khách'}</h2>
        </div>
      {/if}
    </div>
  </div>

  <!-- Navigation Tabs -->
  <div class="flex border-b border-stone-100 gap-8">
    <button
      onclick={() => activeTab = 'basic'}
      class="pb-4 text-[13px] uppercase tracking-widest font-medium transition-all relative {activeTab === 'basic' ? 'text-stone-800' : 'text-stone-400 hover:text-stone-600'}"
    >
      Thông tin cơ bản
      {#if activeTab === 'basic'}
        <div class="absolute bottom-0 left-0 w-full h-0.5 bg-luxury-copper" in:fly={{ y: 2 }}></div>
      {/if}
    </button>
    <button
      onclick={() => activeTab = 'beauty'}
      class="pb-4 text-[13px] uppercase tracking-widest font-medium transition-all relative {activeTab === 'beauty' ? 'text-stone-800' : 'text-stone-400 hover:text-stone-600'}"
    >
      Hồ sơ vẻ đẹp
      {#if activeTab === 'beauty'}
        <div class="absolute bottom-0 left-0 w-full h-0.5 bg-luxury-copper" in:fly={{ y: 2 }}></div>
      {/if}
    </button>
  </div>

  <!-- Form Content -->
  <div class="min-h-[400px]">
    {#if activeTab === 'basic'}
      <div class="space-y-8 py-6" in:fade>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-2">
            <label for="username" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Tên đăng nhập</label>
            <input
              id="username"
              type="text"
              bind:value={username}
              placeholder="Thiết lập tên đăng nhập..."
              class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 font-medium placeholder:text-stone-300 placeholder:italic placeholder:font-normal"
            />
          </div>

          <div class="space-y-2">
            <label for="email" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Địa chỉ Email</label>
            <div class="w-full h-11 border-b border-stone-100 flex items-center justify-between">
              {#if isEditingEmail}
                <input
                  id="email"
                  type="email"
                  bind:value={email}
                  class="w-full h-full outline-none focus:text-stone-900 text-stone-800 font-medium bg-transparent"
                  onblur={() => { if (!email) isEditingEmail = false; }}
                  autoFocus
                />
              {:else}
                <span class="text-stone-800 font-medium">{maskEmail(email)}</span>
                <button 
                  type="button"
                  onclick={() => isEditingEmail = true}
                  class="text-[11px] text-luxury-copper hover:underline font-bold uppercase tracking-wider"
                >
                  Thay đổi
                </button>
              {/if}
            </div>
          </div>

          <div class="space-y-2">
            <label for="fullname" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Họ và tên</label>
            <input
              id="fullname"
              type="text"
              bind:value={name}
              placeholder="Nhập họ tên..."
              class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 placeholder:text-stone-300"
            />
          </div>

          <div class="space-y-2">
            <label for="phone" class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Số điện thoại</label>
            <input
              id="phone"
              type="tel"
              bind:value={phone}
              placeholder="Nhập số điện thoại..."
              class="w-full h-11 border-b border-stone-200 outline-none focus:border-luxury-copper transition-colors text-stone-800 placeholder:text-stone-300"
            />
          </div>

          <div class="space-y-2">
            <label class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Giới tính</label>
            <div class="flex items-center gap-8 h-11">
              {#each [['Nam', 'MALE'], ['Nữ', 'FEMALE'], ['Khác', 'OTHER']] as [label, val]}
                <label class="flex items-center gap-3 cursor-pointer group">
                  <div class="w-4 h-4 rounded-full border border-stone-300 flex items-center justify-center transition-all group-hover:border-luxury-copper {gender === val ? 'border-luxury-copper' : ''}">
                    {#if gender === val}
                      <div class="w-2 h-2 bg-luxury-copper rounded-full" in:fade></div>
                    {/if}
                  </div>
                  <input type="radio" bind:group={gender} value={val} class="hidden" />
                  <span class="text-[13px] text-stone-600 group-hover:text-stone-900 transition-colors">{label}</span>
                </label>
              {/each}
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <label class="text-[11px] uppercase tracking-widest text-stone-400 font-bold">Ngày sinh</label>
          <div class="flex gap-4">
             <div class="flex-1 border-b border-stone-200">
               <select bind:value={birthDay} class="w-full h-11 bg-transparent outline-none text-[14px] text-stone-800 cursor-pointer appearance-none">
                 {#each days as d}<option value={d}>{d}</option>{/each}
               </select>
             </div>
             <div class="flex-1 border-b border-stone-200">
               <select bind:value={birthMonth} class="w-full h-11 bg-transparent outline-none text-[14px] text-stone-800 cursor-pointer appearance-none">
                 {#each months as m}<option value={m}>Tháng {m}</option>{/each}
               </select>
             </div>
             <div class="flex-1 border-b border-stone-200">
               <select bind:value={birthYear} class="w-full h-11 bg-transparent outline-none text-[14px] text-stone-800 cursor-pointer appearance-none">
                 {#each years as y}<option value={y}>{y}</option>{/each}
               </select>
             </div>
          </div>
        </div>
      </div>
    {:else}
      <SkinProfile bind:data={skinData} />
    {/if}
  </div>

  <!-- Footer Action -->
  <div class="pt-10 flex justify-center">
    <button
      onclick={handleSave}
      disabled={isSaving}
      class="group relative px-12 py-3 bg-stone-900 text-white overflow-hidden transition-all duration-500 hover:shadow-[0_10px_30px_rgba(0,0,0,0.15)] disabled:opacity-50"
    >
      <div class="absolute inset-0 bg-luxury-copper translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
      <span class="relative z-10 text-[12px] uppercase tracking-[4px] font-bold">
        {isSaving ? 'Đang lưu hồ sơ...' : 'Cập nhật thay đổi'}
      </span>
    </button>
  </div>
</div>

<style>
  :global(.luxury-copper) {
    color: #c5a059;
  }
  :global(.bg-luxury-copper) {
    background-color: #c5a059;
  }
  :global(.border-luxury-copper) {
    border-color: #c5a059;
  }
</style>
