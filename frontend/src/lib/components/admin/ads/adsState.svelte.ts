import { apiClient } from '$lib/utils/apiClient';
import { useNanobot } from "$lib/state/nanobot.svelte";

const API_BASE = 'https://api.osmo.vn/api/v1';
const ADS_API = `${API_BASE}/ads-protection`;

export function createAdsState() {
  const nanobot = useNanobot();

  let summary = $state<any>(null);
  let insights = $state<any[]>([]);
  let reportResult = $state<any>(null);
  let googleMetrics = $state<any[]>([]);
  let campaigns = $state<any[]>([]);
  let selectedCampaign = $state<any>(null);
  let adGroups = $state<any[]>([]);
  let selectedAdGroup = $state<any>(null);
  let ads = $state<any[]>([]);
  let blacklistedIPs = $state<any[]>([]);
  let negativeKeywords = $state<any[]>([]);
  
  let manualIP = $state('');
  let newNegativeKeyword = $state('');
  let isGlobalNegative = $state(true);
  let isGlobalIP = $state(false);
  let selectedHours = $state(24);
  
  let loading = $state(true);
  let reportLoading = $state(false);
  let googleLoading = $state(false);
  let googleError = $state<string | null>(null);
  let campaignLoading = $state(false);
  let adGroupLoading = $state(false);
  let adsLoading = $state(false);
  let aiLoading = $state(false);
  let activeTab = $state('overview');
  let campaignView = $state('list');

  // Computed
  const googleTotalInvalid = $derived(googleMetrics.reduce((s, m) => s + m.invalid_clicks, 0));
  const googleTotalClicks = $derived(googleMetrics.reduce((s, m) => s + m.clicks, 0));
  const googleTotalCost = $derived(googleMetrics.reduce((s, m) => s + m.cost_vnd, 0));
  const googleAvgRate = $derived(googleTotalClicks > 0 ? (googleTotalInvalid / googleTotalClicks * 100) : 0);

  // Actions
  async function fetchAll() {
    try {
      const [s, i, b] = await Promise.all([
        apiClient.get(`${ADS_API}/summary`, { params: { hours: String(selectedHours) } }),
        apiClient.get(`${ADS_API}/insights`),
        apiClient.get(`${ADS_API}/blacklist`)
      ]);
      summary = s; insights = i || []; blacklistedIPs = b || [];
    } finally { loading = false; }
  }

  async function generateReport() {
    reportLoading = true;
    try {
      const res: any = await apiClient.post(`${ADS_API}/generate-investigation-report`, {});
      if (res.status === 'ready') {
        reportResult = res;
        nanobot.showToast('Báo cáo pháp y đã sẵn sàng', 'success');
      } else {
        nanobot.showToast('Không có dữ liệu gian lận cần báo cáo', 'info');
      }
    } catch { nanobot.showToast('Lỗi truy xuất báo cáo', 'error'); }
    finally { reportLoading = false; }
  }

  async function fetchGoogleMetrics() {
    googleLoading = true;
    try {
      const to = new Date(); const from = new Date();
      from.setHours(from.getHours() - selectedHours);
      const fmtD = (d: Date) => d.toISOString().split('T')[0];
      googleMetrics = await apiClient.get(`${ADS_API}/google-metrics`, { params: { date_from: fmtD(from), date_to: fmtD(to) } }) ?? [];
    } catch { googleError = 'Lỗi API Google'; }
    finally { googleLoading = false; }
  }

  async function fetchCampaigns() {
    campaignLoading = true;
    try { campaigns = await apiClient.get(`${ADS_API}/campaigns`) ?? []; }
    finally { campaignLoading = false; }
  }

  async function fetchAdGroups(c: any) {
    selectedCampaign = c; adGroupLoading = true; campaignView = 'ad_groups';
    try {
      const id = c.resource_name.split('/').pop();
      adGroups = await apiClient.get(`${ADS_API}/campaigns/${id}/ad-groups`) ?? [];
    } finally { adGroupLoading = false; }
  }

  async function fetchAds(ag: any) {
    selectedAdGroup = ag; adsLoading = true; campaignView = 'ads';
    try {
      const id = ag.resource_name.split('/').pop();
      ads = await apiClient.get(`${ADS_API}/ad-groups/${id}/ads`) ?? [];
    } finally { adsLoading = false; }
  }

  async function updateCampaignStatus(resource: string, status: string) {
    const id = resource.split('/').pop();
    try {
      const res: any = await apiClient.patch(`${ADS_API}/campaigns/${id}/status`, { status });
      if (res.success) { nanobot.showToast(res.message, 'success'); fetchCampaigns(); }
    } catch { nanobot.showToast('Lỗi cập nhật', 'error'); }
  }

  async function fetchNegativeKeywords() {
    try {
      const id = selectedCampaign?.resource_name.split('/').pop();
      negativeKeywords = await apiClient.get(`${ADS_API}/negative-keywords`) ?? [];
      if (id) {
        const campK = await apiClient.get(`${ADS_API}/campaigns/${id}/negative-keywords`) ?? [];
        negativeKeywords = [...negativeKeywords, ...campK];
      }
    } catch { negativeKeywords = []; }
  }

  async function addNegativeKeyword(text: string) {
    if (!text.trim()) return;
    const keywords = text.split('\n').map(k => k.trim()).filter(Boolean);
    try {
      let res: any;
      if (isGlobalNegative) res = await apiClient.post(`${ADS_API}/negative-keywords`, { keywords });
      else {
        const id = selectedCampaign.resource_name.split('/').pop();
        res = await apiClient.post(`${ADS_API}/campaigns/${id}/negative-keywords`, { keywords });
      }
      if (res.success) { nanobot.showToast(`Đã xuất bản ${keywords.length} từ khóa`, 'success'); fetchNegativeKeywords(); newNegativeKeyword = ''; }
    } catch { nanobot.showToast("Lỗi API", "error"); }
  }

  async function removeNegativeKeyword(resource: string) {
    const id = resource.split('/').pop();
    try {
      const res: any = await apiClient.delete(`${ADS_API}/negative-keywords/${id}`);
      if (res.success) { nanobot.showToast(res.message, 'success'); fetchNegativeKeywords(); }
    } catch { nanobot.showToast('Lỗi xóa', 'error'); }
  }

  async function blockIP(ip: string, reason = 'Phát hiện click fraud') {
    try {
      const id = selectedCampaign?.resource_name.split('/').pop();
      const res: any = await apiClient.post(`${ADS_API}/blacklist`, { ip, reason, campaign_id: id, is_global: isGlobalIP });
      if (res.success) { nanobot.showToast(res.message || 'Đã chặn IP thành công', 'success'); fetchAll(); }
    } catch { nanobot.showToast('Lỗi chặn IP', 'error'); }
  }

  async function unblockIP(ip: string) {
    try {
      const res: any = await apiClient.delete(`${ADS_API}/blacklist/${ip}`);
      if (res.success) { nanobot.showToast(res.message, 'success'); fetchAll(); }
    } catch { nanobot.showToast('Lỗi gỡ chặn', 'error'); }
  }

  async function aiSuggest(task: string, context: string) {
    aiLoading = true;
    try {
      const res: any = await apiClient.post(`${ADS_API}/ai-suggest`, { task, context });
      if (res.success && task === 'NEGATIVE_KEYWORDS' && res.negative_keywords) newNegativeKeyword = res.negative_keywords.join('\n');
      nanobot.showToast(res.message || 'Xohi đã gợi ý xong', 'success');
    } finally { aiLoading = false; }
  }

  const fmt = (n: number) => new Intl.NumberFormat('vi-VN').format(Math.round(n));
  const priorityColor = (p: string) => p === 'HIGH' ? '#ff3e5e' : p === 'MEDIUM' ? '#fbbf24' : '#10b981';
  const isBlacklisted = (ip: string) => blacklistedIPs.some(i => i.ip === ip);

  return {
    get summary() { return summary }, get insights() { return insights }, get reportResult() { return reportResult },
    get googleMetrics() { return googleMetrics }, get campaigns() { return campaigns }, get selectedCampaign() { return selectedCampaign },
    get adGroups() { return adGroups }, get ads() { return ads }, get negativeKeywords() { return negativeKeywords },
    get blacklistedIPs() { return blacklistedIPs },
    get loading() { return loading }, get activeTab() { return activeTab }, set activeTab(v) { activeTab = v },
    get campaignView() { return campaignView }, set campaignView(v) { campaignView = v },
    get isGlobalNegative() { return isGlobalNegative }, set isGlobalNegative(v) { isGlobalNegative = v },
    get newNegativeKeyword() { return newNegativeKeyword }, set newNegativeKeyword(v) { newNegativeKeyword = v },
    get isGlobalIP() { return isGlobalIP }, set isGlobalIP(v) { isGlobalIP = v },
    get manualIP() { return manualIP }, set manualIP(v) { manualIP = v },
    get selectedHours() { return selectedHours }, set selectedHours(v) { selectedHours = v },
    get reportLoading() { return reportLoading }, get googleLoading() { return googleLoading }, get aiLoading() { return aiLoading },
    get googleError() { return googleError }, get googleTotalInvalid() { return googleTotalInvalid }, get googleTotalClicks() { return googleTotalClicks },
    get googleTotalCost() { return googleTotalCost }, get googleAvgRate() { return googleAvgRate },
    fmt, priorityColor, isBlacklisted, fetchAll, generateReport, fetchGoogleMetrics, fetchCampaigns, fetchAdGroups, fetchAds, 
    updateCampaignStatus, fetchNegativeKeywords, addNegativeKeyword, removeNegativeKeyword, blockIP, unblockIP, aiSuggest,
    getDateRange: () => {
      const to = new Date(); const from = new Date();
      from.setHours(from.getHours() - selectedHours);
      const f = (d: Date) => d.toISOString().split('T')[0];
      return { from: f(from), to: f(to) };
    }
  };
}
