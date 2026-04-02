<script lang="ts">
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import type { BaseWidgetProps } from "$lib/types";

  import Save from "lucide-svelte/icons/save";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Globe from "lucide-svelte/icons/globe";
  import Phone from "lucide-svelte/icons/phone";
  import Share2 from "lucide-svelte/icons/share-2";
  import Search from "lucide-svelte/icons/search";
  import MapPin from "lucide-svelte/icons/map-pin";
  import Tool from "lucide-svelte/icons/wrench";
  import Plus from "lucide-svelte/icons/plus";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Upload from "lucide-svelte/icons/upload";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
  import type { MediaAsset } from "$lib/state/types";

  let { data = {} } = $props<BaseWidgetProps>();

  interface BasicInfo {
    site_name: string;
    description: string;
    logo_desktop: string | null;
    logo_mobile: string | null;
    favicon: string | null;
  }

  interface ContactInfo {
    phone: string;
    hotline: string;
    email: string;
    address: string;
    working_hours: string;
  }

  interface SocialMediaItem {
    platform: string;
    url: string;
    icon_url: string | null;
  }

  interface SeoAnalytics {
    meta_title: string;
    meta_description: string;
    meta_keywords: string;
    google_analytics_id: string;
    facebook_pixel_id: string;
  }

  interface GoogleMaps {
    map_iframe: string;
    api_key: string;
  }

  interface MaintenanceMode {
    is_enabled: boolean;
    message: string;
  }

  interface SupportBotSettings {
    helen_enabled: boolean;
    offline_message: string;
  }

  interface SystemSettings {
    basic_info: BasicInfo;
    contact_info: ContactInfo;
    social_media: SocialMediaItem[];
    seo_analytics: SeoAnalytics;
    google_maps: GoogleMaps;
    maintenance: MaintenanceMode;
    support_bot: SupportBotSettings;
  }

  let settings = $state<SystemSettings>({
    basic_info: { site_name: "", description: "", logo_desktop: null, logo_mobile: null, favicon: null },
    contact_info: { phone: "", hotline: "", email: "", address: "", working_hours: "" },
    social_media: [],
    seo_analytics: { meta_title: "", meta_description: "", meta_keywords: "", google_analytics_id: "", facebook_pixel_id: "" },
    google_maps: { map_iframe: "", api_key: "" },
    maintenance: { is_enabled: false, message: "" },
    support_bot: { helen_enabled: true, offline_message: "" }
  });

  let activeTab = $state("basic");
  let isLoading = $state(true);
  let isSaving = $state(false);

  // Media Picker State
  let showMediaModal = $state(false);
  let currentPickField = $state<string | null>(null);
  let currentPickType = $state<'basic' | 'social'>('basic');
  let currentSocialIndex = $state<number | null>(null);

  type TabId = "basic" | "contact" | "social" | "seo" | "maps" | "maintenance" | "helen";

  interface TabDefinition {
    id: TabId;
    label: string;
    icon: typeof Globe;
  }

  const tabs: TabDefinition[] = [
    { id: "basic", label: "Thông tin cơ bản", icon: Globe },
    { id: "contact", label: "Liên hệ", icon: Phone },
    { id: "social", label: "Mạng xã hội", icon: Share2 },
    { id: "seo", label: "SEO & Analytics", icon: Search },
    { id: "maps", label: "Google Maps", icon: MapPin },
    { id: "maintenance", label: "Bảo trì", icon: Tool },
    { id: "helen", label: "Helen AI", icon: Sparkles }
  ];

  onMount(async () => {
    try {
      const res = await apiClient.get<{ settings: SystemSettings }>("/api/v1/settings/general");
      if (res?.settings) {
        settings = res.settings;
      }
    } catch (e) {
      nanobot.showToast("Failed to fetch settings.", "error");
    } finally {
      isLoading = false;
    }
  });

  async function saveSettings() {
    isSaving = true;
    try {
      await apiClient.post("/api/v1/settings/general", settings);
      nanobot.showToast("Cấu hình hệ thống đã được lưu.", "success");
    } catch (e) {
      nanobot.showToast("Không thể lưu cấu hình.", "error");
    } finally {
      isSaving = false;
    }
  }

  function addSocial() {
    settings.social_media = [...settings.social_media, { platform: "", url: "", icon_url: null }];
  }

  function removeSocial(index: number) {
    settings.social_media = settings.social_media.filter((_, i) => i !== index);
  }

  function handleUpload(field: keyof BasicInfo) {
    currentPickField = field;
    currentPickType = 'basic';
    showMediaModal = true;
  }

  function handleSocialUpload(index: number) {
    currentSocialIndex = index;
    currentPickType = 'social';
    showMediaModal = true;
  }

  function handleMediaSelect(url: string) {
    if (currentPickType === 'basic' && currentPickField) {
      // @ts-ignore - dynamic key access
      settings.basic_info[currentPickField] = url;
    } else if (currentPickType === 'social' && currentSocialIndex !== null) {
      settings.social_media[currentSocialIndex].icon_url = url;
    }
    showMediaModal = false;
    currentPickField = null;
    currentSocialIndex = null;
  }

  const brandAssets = [
    { label: 'Logo Desktop', field: 'logo_desktop' as keyof BasicInfo, icon: Globe },
    { label: 'Logo Mobile', field: 'logo_mobile' as keyof BasicInfo, icon: Share2 },
    { label: 'Favicon / Icon', field: 'favicon' as keyof BasicInfo, icon: Globe }
  ];

</script>

<div class="w-full h-full flex flex-col bg-[#020202] text-zinc-100 selection:bg-cyan-500/30 font-sans">
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center gap-8">
      <div class="relative">
        <div class="w-24 h-24 border-2 border-cyan-500/5 border-t-cyan-400 rounded-full animate-spin"></div>
      </div>
      <h2 class="text-xs font-mono text-cyan-400 uppercase tracking-[0.6em] animate-pulse">
        Accessing System Core
      </h2>
    </div>
  {:else}
    <header class="h-auto min-h-[3.5rem] lg:h-16 px-4 sm:px-6 lg:px-8 border-b border-white/5 flex flex-col lg:flex-row items-center justify-between bg-zinc-950/40 backdrop-blur-xl gap-4 py-2 lg:py-0 z-50 sticky top-0">
      <div class="flex items-center gap-4">
        <div class="flex flex-col lg:flex-row lg:items-center gap-2 lg:gap-4">
          <h1 class="text-lg lg:text-xl font-black italic tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 to-zinc-500">
            SYSTEM CONFIGURATION
          </h1>
          <div class="flex items-center gap-2 px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded-md">
            <div class="w-1 h-1 rounded-full bg-cyan-500 animate-pulse"></div>
            <span class="text-[8px] font-mono text-cyan-500 uppercase tracking-widest">Core Access Granted</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          onclick={saveSettings}
          disabled={isSaving}
          class="group relative h-9 lg:h-10 px-6 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-lg shadow-[0_0_15px_rgba(8,145,178,0.3)] transition-all disabled:opacity-50 flex items-center gap-2"
        >
          {#if isSaving}
            <RefreshCw size={14} class="animate-spin" />
          {:else}
            <Save size={14} class="group-hover:scale-110 transition-transform" />
          {/if}
          <span class="text-[10px] uppercase tracking-[0.15em] font-black">
            {isSaving ? "Saving..." : "Save Config"}
          </span>
        </button>
      </div>
    </header>

    <main class="flex-1 flex flex-col lg:flex-row min-h-0">
      <!-- Sidebar Tabs -->
      <aside class="w-full lg:w-64 border-b lg:border-b-0 lg:border-r border-white/5 bg-zinc-950/20 overflow-y-auto custom-scrollbar flex flex-col p-4 gap-2">
        {#each tabs as tab}
          <button
            onclick={() => activeTab = tab.id}
            class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left group
              {activeTab === tab.id ? 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-400' : 'hover:bg-white/5 border border-transparent text-zinc-500 hover:text-zinc-300'}"
          >
            <tab.icon size={18} class={activeTab === tab.id ? 'text-cyan-400' : 'group-hover:text-zinc-300'} />
            <span class="text-xs font-bold uppercase tracking-wider">{tab.label}</span>
          </button>
        {/each}
      </aside>

      <!-- Content Area -->
      <section class="flex-1 overflow-y-auto custom-scrollbar bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.03),transparent_70%)] p-4 sm:p-6 lg:p-8">
        <div class="max-w-4xl mx-auto">
          
          {#if activeTab === 'basic'}
            <div class="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <section class="space-y-4">
                <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Globe size={16} /> Thông tin cơ bản
                </h3>
                <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                  <div class="space-y-1">
                    <label for="site_name" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Tên Website</label>
                    <input id="site_name" bind:value={settings.basic_info.site_name} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="e.g. SmartShop" />
                  </div>
                  <div class="space-y-1">
                    <label for="site_desc" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Mô tả hệ thống</label>
                    <textarea id="site_desc" bind:value={settings.basic_info.description} rows="3" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors resize-none" placeholder="Mô tả ngắn về website..."></textarea>
                  </div>
                </div>
              </section>

              <section class="space-y-4">
                <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-widest">Brand Assets</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {#each brandAssets as item}
                    <div class="bg-zinc-950/40 border border-white/5 rounded-2xl p-6 flex flex-col items-center gap-4 group/asset">
                      <div class="w-16 h-16 rounded-xl bg-black border border-white/5 flex items-center justify-center relative overflow-hidden group-hover/asset:border-cyan-500/30 transition-colors">
                        {#if settings.basic_info[item.field]}
                          <img src={settings.basic_info[item.field]} alt={item.label} class="w-full h-full object-contain p-2" />
                        {:else}
                          <item.icon size={24} class="text-zinc-700 group-hover/asset:text-cyan-500/50 transition-colors" />
                        {/if}
                      </div>
                      <div class="text-center">
                        <p class="text-[10px] font-black uppercase tracking-tighter mb-2">{item.label}</p>
                        <button 
                          onclick={() => handleUpload(item.field)}
                          aria-label={`Upload ${item.label}`}
                          class="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[9px] font-mono uppercase tracking-widest transition-all flex items-center gap-2 mx-auto"
                        >
                          <Upload size={10} /> Sync Asset
                        </button>
                      </div>
                    </div>
                  {/each}
                </div>
              </section>
            </div>

          {:else if activeTab === 'contact'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <Phone size={16} /> Thông tin liên hệ
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                <div class="space-y-1">
                  <label for="phone" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Điện thoại</label>
                  <input id="phone" bind:value={settings.contact_info.phone} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="0901 234 567" />
                </div>
                <div class="space-y-1">
                  <label for="hotline" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Hotline</label>
                  <input id="hotline" bind:value={settings.contact_info.hotline} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="1800 XXXX" />
                </div>
                <div class="space-y-1">
                  <label for="email" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Email</label>
                  <input id="email" bind:value={settings.contact_info.email} type="email" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="admin@example.com" />
                </div>
                <div class="space-y-1">
                  <label for="hours" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Giờ làm việc</label>
                  <input id="hours" bind:value={settings.contact_info.working_hours} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="8:00 - 22:00" />
                </div>
                <div class="space-y-1 md:col-span-2">
                  <label for="address" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Địa chỉ</label>
                  <input id="address" bind:value={settings.contact_info.address} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="Số 1, Đường ABC, Quận XYZ..." />
                </div>
              </div>
            </div>

          {:else if activeTab === 'social'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Share2 size={16} /> Mạng xã hội
                </h3>
                <button 
                  onclick={addSocial}
                  class="px-4 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-600/30 rounded-lg text-xs font-black text-cyan-400 uppercase tracking-widest transition-all flex items-center gap-2"
                >
                  <Plus size={14} /> Add Channel
                </button>
              </div>

              {#if settings.social_media.length === 0}
                <div class="bg-zinc-950/40 border border-dashed border-white/10 rounded-2xl p-12 text-center">
                  <Share2 size={32} class="text-zinc-800 mx-auto mb-4" />
                  <p class="text-zinc-600 text-sm font-mono uppercase tracking-widest">No social channels configured</p>
                </div>
              {/if}

              <div class="grid grid-cols-1 gap-4">
                {#each settings.social_media as item, i}
                  <div class="bg-zinc-950/40 border border-white/5 rounded-2xl p-4 flex items-center gap-4 animate-in slide-in-from-left-2 duration-200">
                    <button 
                      onclick={() => handleSocialUpload(i)}
                      aria-label="Upload Social Icon"
                      class="w-12 h-12 rounded-lg bg-black border border-white/5 flex items-center justify-center group/socialico relative overflow-hidden"
                    >
                      {#if item.icon_url}
                        <img src={item.icon_url} alt="Icon" class="w-full h-full object-contain p-1" />
                      {:else}
                        <Upload size={16} class="text-zinc-700 group-hover/socialico:text-cyan-500 transition-colors" />
                      {/if}
                    </button>
                    <div class="flex-1 grid grid-cols-2 gap-4">
                      <input bind:value={item.platform} type="text" autocomplete="off" aria-label="Platform Name" class="bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-xs focus:border-cyan-500/50 outline-none" placeholder="Tên (e.g. Facebook)" />
                      <input bind:value={item.url} type="text" autocomplete="off" aria-label="Platform URL" class="bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-xs focus:border-cyan-500/50 outline-none" placeholder="Link liên kết" />
                    </div>
                    <button 
                      onclick={() => removeSocial(i)}
                      aria-label="Remove Social Channel"
                      class="p-2 text-zinc-600 hover:text-red-400 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                {/each}
              </div>
            </div>

          {:else if activeTab === 'seo'}
            <div class="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <section class="space-y-4">
                <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Search size={16} /> SEO Optimization
                </h3>
                <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                  <div class="space-y-1">
                    <label for="seo_title" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Meta Title (Default)</label>
                    <input id="seo_title" bind:value={settings.seo_analytics.meta_title} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="Tiêu đề trang mẫu..." />
                  </div>
                  <div class="space-y-1">
                    <label for="seo_keys" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Meta Keywords</label>
                    <input id="seo_keys" bind:value={settings.seo_analytics.meta_keywords} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="AI, mua sắm, thời trang..." />
                  </div>
                  <div class="space-y-1">
                    <label for="seo_desc" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Meta Description</label>
                    <textarea id="seo_desc" bind:value={settings.seo_analytics.meta_description} rows="3" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors resize-none" placeholder="Mô tả chuẩn SEO..."></textarea>
                  </div>
                </div>
              </section>

              <section class="space-y-4">
                <h3 class="text-sm font-black text-emerald-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Search size={16} /> Analytics & Tracking
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                  <div class="space-y-1">
                    <label for="ga_id" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Google Analytics ID</label>
                    <input id="ga_id" bind:value={settings.seo_analytics.google_analytics_id} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-emerald-500/50 outline-none transition-colors" placeholder="G-XXXXXXXX" />
                  </div>
                  <div class="space-y-1">
                    <label for="fb_id" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Facebook Pixel ID</label>
                    <input id="fb_id" bind:value={settings.seo_analytics.facebook_pixel_id} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-emerald-500/50 outline-none transition-colors" placeholder="XXXXXXXXXX" />
                  </div>
                </div>
              </section>
            </div>

          {:else if activeTab === 'maps'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <MapPin size={16} /> Google Maps Config
              </h3>
              <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                <div class="space-y-1">
                  <label for="map_iframe" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Embed Iframe Code</label>
                  <textarea id="map_iframe" bind:value={settings.google_maps.map_iframe} rows="4" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm font-mono focus:border-cyan-500/50 outline-none transition-colors resize-none" placeholder="<iframe src='...' ...></iframe>"></textarea>
                  <p class="text-[9px] text-zinc-600 mt-1 italic">Dán mã nhúng iframe từ Google Maps vào đây.</p>
                </div>
                <div class="space-y-1">
                  <label for="map_key" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Maps API Key (Optional)</label>
                  <input id="map_key" bind:value={settings.google_maps.api_key} type="password" autocomplete="new-password" spellcheck="false" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="AIza..." />
                </div>
              </div>

              {#if settings.google_maps.map_iframe}
                <div class="bg-black border border-white/5 rounded-2xl overflow-hidden h-64 relative grayscale hover:grayscale-0 transition-all duration-700">
                  <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-black to-transparent opacity-40"></div>
                  {@html settings.google_maps.map_iframe.replace(/width="[^"]*"/, 'width="100%"').replace(/height="[^"]*"/, 'height="100%"')}
                </div>
              {/if}
            </div>

          {:else if activeTab === 'maintenance'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-amber-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <Tool size={16} /> Maintenance Mode
              </h3>
              
              <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-8 items-center">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h4 class="text-base font-black text-white uppercase italic tracking-tighter">Emergency Shutdown</h4>
                    <p class="text-[10px] text-zinc-500 font-mono tracking-widest mt-1">IF ACTIVE, VISITORS WILL SEE THE MAINTENANCE PAGE</p>
                  </div>
                  
                  <button 
                    onclick={() => settings.maintenance.is_enabled = !settings.maintenance.is_enabled}
                    aria-label="Toggle Maintenance Mode"
                    class="relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none 
                      {settings.maintenance.is_enabled ? 'bg-red-500' : 'bg-zinc-800'}"
                  >
                    <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-lg transition-transform duration-300
                      {settings.maintenance.is_enabled ? 'translate-x-7' : 'translate-x-0'}">
                    </div>
                  </button>
                </div>

                <div class="space-y-1">
                  <label for="maint_msg" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Lý do bảo trì / Thông điệp</label>
                  <textarea 
                    id="maint_msg"
                    bind:value={settings.maintenance.message} 
                    rows="4" 
                    disabled={!settings.maintenance.is_enabled}
                    autocomplete="off"
                    class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-amber-500/50 outline-none transition-colors resize-none disabled:opacity-40" 
                    placeholder="Thông báo cho khách hàng..."
                  ></textarea>
                </div>
                
                {#if settings.maintenance.is_enabled}
                  <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-4 animate-pulse">
                    <div class="w-2 h-2 rounded-full bg-red-500"></div>
                    <span class="text-[10px] font-black text-red-500 uppercase tracking-[0.2em]">System Isolated: Maintenance Protocol Active</span>
                  </div>
                {/if}
              </div>
            </div>
          {:else if activeTab === 'helen'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <Sparkles size={16} /> Helen AI Configuration
              </h3>
              
              <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-8 items-center">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h4 class="text-base font-black text-white uppercase italic tracking-tighter">Helen AI Control</h4>
                    <p class="text-[10px] text-zinc-500 font-mono tracking-widest mt-1">ENABLE OR DISABLE THE AI SUPPORT BOT GLOBALLY</p>
                  </div>
                  
                  <button 
                    onclick={() => settings.support_bot.helen_enabled = !settings.support_bot.helen_enabled}
                    aria-label="Toggle Helen AI"
                    class="relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none 
                      {settings.support_bot.helen_enabled ? 'bg-cyan-500' : 'bg-zinc-800'}"
                  >
                    <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-lg transition-transform duration-300
                      {settings.support_bot.helen_enabled ? 'translate-x-7' : 'translate-x-0'}">
                    </div>
                  </button>
                </div>

                <div class="space-y-1">
                  <label for="helen_offline_msg" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Thông báo khi Helen OFF</label>
                  <textarea 
                    id="helen_offline_msg"
                    bind:value={settings.support_bot.offline_message} 
                    rows="4" 
                    autocomplete="off"
                    class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors resize-none" 
                    placeholder="Dược sĩ tư vấn sẽ hỗ trợ sếp ngay ạ..."
                  ></textarea>
                </div>
                
                {#if settings.support_bot.helen_enabled}
                  <div class="p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-xl flex items-center gap-4">
                    <div class="w-2 h-2 rounded-full bg-cyan-500 animate-ping"></div>
                    <span class="text-[10px] font-black text-cyan-500 uppercase tracking-[0.2em]">Helen AI is Online & Active</span>
                  </div>
                {:else}
                  <div class="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center gap-4">
                    <div class="w-2 h-2 rounded-full bg-amber-500"></div>
                    <span class="text-[10px] font-black text-amber-500 uppercase tracking-[0.2em]">Manual Support Mode Active</span>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      </section>
    </main>
  {/if}
</div>

<MediaVaultModal
  isOpen={showMediaModal}
  onClose={() => showMediaModal = false}
  onSelect={handleMediaSelect}
/>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  /* Prevent browser autofill from turning background white */
  input:-webkit-autofill,
  input:-webkit-autofill:hover, 
  input:-webkit-autofill:focus, 
  input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 30px #0a0a0a inset !important;
    -webkit-text-fill-color: #f4f4f5 !important;
    transition: background-color 5000s ease-in-out 0s;
  }

  /* Fix OmniCommand looking "white" due to backdrop-filter on light backgrounds */
  :global(.omni-waterdrop) :global(.flex-1.rounded-full) {
    background: rgba(0, 0, 0, 0.8) !important;
    border-color: rgba(0, 255, 255, 0.1) !important;
  }
</style>
