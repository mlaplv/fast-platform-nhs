<script lang="ts">
  import { 
    Calendar as CalendarIcon, 
    Clock, 
    User, 
    ChevronLeft, 
    ChevronRight, 
    Plus, 
    LayoutDashboard,
    Search,
    Filter,
    MoreVertical,
    RefreshCw,
    ChevronDown
  } from "lucide-svelte";
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";

  let { isWidget = false } = $props<{ isWidget?: boolean }>();

  interface RecurringMetadata {
    monthly_type?: 'day_of_month' | 'day_of_week';
    day_of_month?: number;
    day_of_week?: number;
    week_index?: number;
  }

  interface Appointment {
    id: string;
    title: string;
    description?: string;
    start_time: string;
    end_time: string;
    type: 'STRATEGY' | 'DEPLOYMENT' | 'REVIEW';
    status: 'UPCOMING' | 'ONGOING' | 'COMPLETED';
    recurring_type: 'none' | 'daily' | 'weekly' | 'monthly';
    recurring_metadata: RecurringMetadata;
    metadata_json: Record<string, unknown>;
    created_at: string;
  }

  interface AppointmentListResponse {
    items: Appointment[];
    total: number;
  }

  let selectedDate = $state(new Date());
  let appointments = $state<Appointment[]>([]);
  let isLoading = $state(true);
  let showAddModal = $state(false);
  let newAppt = $state<Partial<Appointment>>({
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    type: 'STRATEGY',
    status: 'UPCOMING',
    recurring_type: 'none',
    recurring_metadata: {
      monthly_type: 'day_of_month',
      day_of_month: new Date().getDate(),
      day_of_week: new Date().getDay(),
      week_index: Math.ceil(new Date().getDate() / 7),
    },
    metadata_json: {}
  });

  let filterStatus = $state<'ALL' | 'UPCOMING' | 'ONGOING' | 'COMPLETED'>('ALL');
  let showDatePicker = $state(false);
  let counts = $derived({
    all: appointments.filter(a => {
      const d = new Date(a.start_time);
      return d.getFullYear() === selectedDate.getFullYear() && d.getMonth() === selectedDate.getMonth() && d.getDate() === selectedDate.getDate();
    }).length,
    upcoming: appointments.filter(a => {
      const d = new Date(a.start_time);
      return a.status === 'UPCOMING' && d.getFullYear() === selectedDate.getFullYear() && d.getMonth() === selectedDate.getMonth() && d.getDate() === selectedDate.getDate();
    }).length,
    ongoing: appointments.filter(a => {
      const d = new Date(a.start_time);
      return a.status === 'ONGOING' && d.getFullYear() === selectedDate.getFullYear() && d.getMonth() === selectedDate.getMonth() && d.getDate() === selectedDate.getDate();
    }).length,
    completed: appointments.filter(a => {
      const d = new Date(a.start_time);
      return a.status === 'COMPLETED' && d.getFullYear() === selectedDate.getFullYear() && d.getMonth() === selectedDate.getMonth() && d.getDate() === selectedDate.getDate();
    }).length,
  });
  let filteredAppointments = $derived(
    appointments.filter(a => {
      const matchStatus = filterStatus === 'ALL' || a.status === filterStatus;
      
      const apptDate = new Date(a.start_time);
      const matchDate = apptDate.getFullYear() === selectedDate.getFullYear() &&
                        apptDate.getMonth() === selectedDate.getMonth() &&
                        apptDate.getDate() === selectedDate.getDate();
                        
      return matchStatus && matchDate;
    })
  );

  onMount(async () => {
    await fetchAppointments();
  });

  async function fetchAppointments() {
    isLoading = true;
    try {
      const response = await apiClient.get<AppointmentListResponse>("/api/v1/appointments/");
      appointments = response?.items || [];
    } catch (e) {
      console.error("Failed to fetch appointments", e);
      nanobot.showToast("Không thể tải danh sách lịch hẹn", "error");
    } finally {
      isLoading = false;
    }
  }

  function prevMonth() {
    selectedDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth() - 1, 1);
  }

  function nextMonth() {
    selectedDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 1);
  }

  function formatMonth(date: Date) {
    return date.toLocaleString('vi-VN', { month: 'long', year: 'numeric' });
  }

  function getDaysInMonth(date: Date) {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  }

  function getFirstDayOfMonth(date: Date) {
    let day = new Date(date.getFullYear(), date.getMonth(), 1).getDay();
    // Chuyển đổi 0 (Chủ nhật) thành 6, 1-6 (Thứ 2-7) thành 0-5
    return day === 0 ? 6 : day - 1;
  }

  async function saveAppointment() {
    if (!newAppt.title || !newAppt.start_time || !newAppt.end_time) {
      nanobot.showToast("Vui lòng điền đầy đủ thông tin", "warning");
      return;
    }

    try {
      const payload = {
        ...newAppt,
        metadata_json: newAppt.metadata_json || {}
      };

      if (newAppt.id) {
        await apiClient.patch(`/api/v1/appointments/${newAppt.id}/`, payload);
        nanobot.showToast("Cập nhật lịch hẹn thành công", "success");
      } else {
        await apiClient.post("/api/v1/appointments/", payload);
        nanobot.showToast("Đã lưu lịch hẹn thành công", "success");
      }
      showAddModal = false;
      await fetchAppointments();
    } catch (e) {
      console.error("Failed to save appointment", e);
      nanobot.showToast("Không thể lưu lịch hẹn", "error");
    }
  }

  function editAppointment(appt: Appointment) {
    newAppt = { ...appt };
    showAddModal = true;
  }

  async function deleteAppointment(id: string) {
    const confirmed = await nanobot.showConfirm({
      title: "Xác nhận xóa",
      message: "Sếp có chắc chắn muốn xóa lịch hẹn này không? Hành động này không thể hoàn tác.",
      confirmLabel: "XÓA NGAY",
      cancelLabel: "HỦY"
    });

    if (confirmed) {
      try {
        await apiClient.delete(`/api/v1/appointments/${id}/`);
        nanobot.showToast("Đã xóa lịch hẹn", "success");
        await fetchAppointments();
      } catch (e) {
        console.error("Failed to delete", e);
        nanobot.showToast("Không thể xóa lịch hẹn", "error");
      }
    }
  }

  let showScout = $state(false);
  let isScouting = $state(false);
  let scoutQuery = $state('');

  async function runScout() {
    if (!scoutQuery) return;
    isScouting = true;
    try {
      // Placeholder for actual scouting logic
      // In a real scenario, this would call a backend scraper
      await new Promise(resolve => setTimeout(resolve, 2000));
      nanobot.showToast("Dữ liệu trinh sát đã được thu thập", "success");
    } finally {
      isScouting = false;
    }
  }
</script>

<div class="{isWidget ? 'p-4' : 'min-h-screen bg-[#010101] p-6 lg:p-10'} text-white font-sans selection:bg-blue-500/30">
  <!-- Header / Command Center Info -->
    <header class="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
      <div class="space-y-1 relative">
        <h1 class="text-xl md:text-2xl font-black tracking-tighter bg-gradient-to-r from-white via-white to-white/30 bg-clip-text text-transparent uppercase">
          Appointment <span class="text-blue-500 italic">Manager</span>
        </h1>
        
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2 bg-white/[0.03] border border-white/5 rounded-2xl px-1.5 py-1 backdrop-blur-md">
            <button 
              onclick={() => showDatePicker = !showDatePicker}
              class="flex items-center gap-2 px-2 py-1 rounded-xl hover:bg-white/5 transition-all group/date-trigger"
            >
              <CalendarIcon size={12} class="text-blue-400" />
              <span class="text-[10px] font-black uppercase tracking-widest text-white/90">{formatMonth(selectedDate)}</span>
              <ChevronDown size={10} class="text-white/20 {showDatePicker ? 'rotate-180' : ''} transition-transform" />
            </button>
            <div class="flex gap-0.5 border-l border-white/10 pl-1">
              <button onclick={prevMonth} class="p-1 rounded-md hover:bg-white/5 transition-all text-white/40 hover:text-white"><ChevronLeft size={12} /></button>
              <button onclick={nextMonth} class="p-1 rounded-md hover:bg-white/5 transition-all text-white/40 hover:text-white"><ChevronRight size={12} /></button>
            </div>
          </div>
          <div class="hidden sm:block h-3 w-px bg-white/10"></div>
          <p class="text-gray-500 text-[9px] font-bold tracking-tight uppercase opacity-60">Neural Elite Registry</p>
        </div>

        {#if showDatePicker}
          <div 
            class="absolute top-full left-0 mt-3 p-4 rounded-3xl bg-black/95 border border-white/10 backdrop-blur-3xl shadow-2xl z-[200] w-full min-w-[260px] animate-in fade-in zoom-in-95 duration-200"
            onmouseleave={() => showDatePicker = false}
          >
            <div class="grid grid-cols-7 gap-1 text-center mb-2">
              {#each ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'] as day}
                <span class="text-[7px] font-black text-white/10 uppercase py-1">{day}</span>
              {/each}
            </div>
            <div class="grid grid-cols-7 gap-1">
              {#each Array(getFirstDayOfMonth(selectedDate)).fill(0) as _}
                <div class="aspect-square"></div>
              {/each}
              {#each Array(getDaysInMonth(selectedDate)).fill(0) as _, i}
                {@const day = i + 1}
                {@const isToday = day === new Date().getDate() && selectedDate.getMonth() === new Date().getMonth() && selectedDate.getFullYear() === new Date().getFullYear()}
                <button 
                  onclick={() => {
                    selectedDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), day);
                    showDatePicker = false;
                    fetchAppointments();
                  }}
                  class="aspect-square rounded-lg flex items-center justify-center text-[10px] font-bold transition-all
                  {isToday ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/20' : 'text-white/30 hover:bg-white/10 hover:text-white'}"
                >
                  {day}
                </button>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div class="flex items-center gap-1 bg-white/[0.03] border border-white/5 rounded-2xl p-1 overflow-x-auto no-scrollbar max-w-full">
          <button 
            onclick={() => filterStatus = 'ALL'}
            class="whitespace-nowrap px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all {filterStatus === 'ALL' ? 'bg-blue-500 text-white' : 'text-white/40 hover:text-white hover:bg-white/5'} flex items-center gap-2"
          >
            All <span class="opacity-40">{counts.all}</span>
          </button>
          <button 
            onclick={() => filterStatus = 'UPCOMING'}
            class="whitespace-nowrap px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all {filterStatus === 'UPCOMING' ? 'bg-blue-500 text-white' : 'text-white/40 hover:text-white hover:bg-white/5'} flex items-center gap-2"
          >
            Upcoming <span class="opacity-40">{counts.upcoming}</span>
          </button>
          <button 
            onclick={() => filterStatus = 'ONGOING'}
            class="whitespace-nowrap px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all {filterStatus === 'ONGOING' ? 'bg-blue-500 text-white' : 'text-white/40 hover:text-white hover:bg-white/5'} flex items-center gap-2"
          >
            Live <span class="opacity-40">{counts.ongoing}</span>
          </button>
          <button 
            onclick={() => filterStatus = 'COMPLETED'}
            class="whitespace-nowrap px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all {filterStatus === 'COMPLETED' ? 'bg-blue-500 text-white' : 'text-white/40 hover:text-white hover:bg-white/5'} flex items-center gap-2"
          >
            Done <span class="opacity-40">{counts.completed}</span>
          </button>
        </div>

        <div class="flex items-center gap-2 w-full sm:w-auto">
          <div class="relative flex-1 sm:flex-none">
            <Search size={12} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
            <input 
              type="text" 
              placeholder="QUÉT DỮ LIỆU..."
              class="w-full sm:w-32 bg-white/[0.03] border border-white/5 rounded-xl pl-9 pr-3 py-2 text-[10px] font-bold focus:outline-none focus:border-blue-500/30 transition-all uppercase placeholder:text-white/10"
            />
          </div>
          <button 
            onclick={() => showAddModal = true}
            class="p-2.5 rounded-xl bg-white text-black hover:scale-105 active:scale-95 transition-all shadow-lg"
          >
            <Plus size={16} strokeWidth={3} />
          </button>
        </div>
      </div>
       <!-- Neural Scout Toggle (Hidden/Disabled by default as per R00) -->
       <button 
         onclick={() => showScout = !showScout}
         class="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 opacity-20 hover:opacity-100 transition-all group/scout"
         title="Neural Scout (Trinh sát đối thủ)"
       >
         <Search size={16} class="group-hover/scout:scale-110 transition-transform" />
       </button>
      <button 
        onclick={() => {
          newAppt = {
            title: '',
            description: '',
            start_time: '',
            end_time: '',
            type: 'STRATEGY',
            status: 'UPCOMING',
            recurring_type: 'none',
            recurring_metadata: {
              monthly_type: 'day_of_month',
              day_of_month: new Date().getDate(),
              day_of_week: new Date().getDay(),
              week_index: Math.ceil(new Date().getDate() / 7),
            }
          };
          showAddModal = true;
        }}
        class="p-2.5 rounded-xl bg-white text-black hover:scale-105 active:scale-95 transition-all shadow-xl shadow-white/5"
      >
        <Plus size={18} strokeWidth={3} />
      </button>
  </header>

  {#if showScout}
    <div class="mb-8 p-8 rounded-[2.5rem] bg-gradient-to-br from-purple-500/10 to-blue-500/5 border border-purple-500/20 shadow-2xl relative overflow-hidden animate-in fade-in slide-in-from-top-10 duration-700">
      <div class="absolute -top-24 -right-24 w-64 h-64 bg-purple-500/20 blur-[100px] rounded-full"></div>
      
      <div class="relative z-10 flex flex-col md:flex-row gap-8">
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-400 border border-purple-500/30">
              <Search size={20} />
            </div>
            <div>
              <h3 class="text-sm font-black uppercase tracking-[0.2em] text-white">Neural Scout <span class="text-purple-400 italic">v2.2</span></h3>
              <p class="text-[9px] text-purple-300/60 font-bold uppercase tracking-widest mt-0.5">Trinh sát & Phân tích nội dung đối thủ</p>
            </div>
          </div>

          <div class="space-y-4">
            <div class="relative group/scout-input">
              <input 
                bind:value={scoutQuery}
                type="text"
                placeholder="Nhập từ khóa hoặc URL đối thủ..."
                class="w-full bg-black/40 border border-white/5 rounded-2xl px-5 py-4 text-xs font-bold focus:outline-none focus:border-purple-500/50 transition-all shadow-inner"
                onkeydown={(e) => e.key === 'Enter' && runScout()}
              />
              <button 
                onclick={runScout}
                disabled={isScouting}
                class="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 rounded-xl bg-purple-500 text-white text-[9px] font-black uppercase tracking-widest hover:scale-105 active:scale-95 transition-all disabled:opacity-50"
              >
                {isScouting ? 'ĐANG QUÉT...' : 'TRINH SÁT'}
              </button>
            </div>

            <div class="flex flex-wrap gap-2 pt-2">
              {#each ['Gợi ý tiêu đề', 'Từ khóa ngách', 'Cấu trúc bài viết', 'Lịch đăng tối ưu'] as tag}
                <button class="px-3 py-1.5 rounded-full bg-white/5 border border-white/5 text-[8px] font-black uppercase tracking-widest text-white/40 hover:text-purple-400 hover:border-purple-500/30 transition-all cursor-default">
                  {tag}
                </button>
              {/each}
            </div>
          </div>
        </div>

        <div class="flex-1 md:border-l md:border-white/5 md:pl-8">
          <div class="h-full flex flex-col justify-center">
            {#if !scoutQuery && !isScouting}
              <div class="text-center opacity-20">
                <LayoutDashboard size={40} class="mx-auto mb-3" />
                <p class="text-[10px] font-black uppercase tracking-widest">Initial System State</p>
                <p class="text-[8px] mt-1 italic tracking-tight">Sẵn sàng thu thập dữ liệu chiến lược.</p>
              </div>
            {:else if isScouting}
              <div class="flex flex-col items-center justify-center space-y-4 py-10">
                <div class="relative w-12 h-12">
                   <div class="absolute inset-0 border-2 border-purple-500/20 rounded-full"></div>
                   <div class="absolute inset-0 border-t-2 border-purple-500 rounded-full animate-spin"></div>
                </div>
                <p class="text-[9px] font-black uppercase tracking-[0.3em] text-purple-400 animate-pulse">Neural Scraper Active</p>
              </div>
            {:else}
               <div class="space-y-4 animate-in fade-in slide-in-from-right-10 duration-700">
                  <div class="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-2">
                    <span class="text-[8px] font-black text-purple-400 uppercase tracking-widest">Tiêu đề Gợi ý</span>
                    <p class="text-[11px] font-bold text-white uppercase leading-tight">Top 5 Chiến lược Marketing AI 2026: Cách đối thủ của Sếp đang thống trị thị trường</p>
                  </div>
                  <div class="flex gap-2">
                    <div class="flex-1 p-3 rounded-2xl bg-white/5 border border-white/5 text-center">
                      <span class="block text-[7px] text-white/20 uppercase mb-1">Độ khó</span>
                      <span class="text-xs font-black text-green-400 uppercase tracking-tighter">Thấp</span>
                    </div>
                    <div class="flex-1 p-3 rounded-2xl bg-white/5 border border-white/5 text-center">
                      <span class="block text-[7px] text-white/20 uppercase mb-1">Traffic Gợi ý</span>
                      <span class="text-xs font-black text-blue-400 uppercase tracking-tighter">1.2k/mo</span>
                    </div>
                  </div>
               </div>
            {/if}
          </div>
        </div>
      </div>

      <button 
        onclick={() => showScout = false}
        class="absolute top-4 right-4 p-2 text-white/10 hover:text-white transition-colors"
      >
        <Plus size={20} class="rotate-45" />
      </button>
    </div>
  {/if}

  <div class="grid grid-cols-1 gap-8">
    <!-- Main Content: Schedule View -->
    <div class="flex flex-col gap-6">
      <div class="flex items-center justify-between px-4">
        <div class="flex items-center gap-4">
          <button class="text-[11px] font-black uppercase tracking-widest border-b-2 border-blue-500 pb-1.5 text-white transition-all">Danh sách</button>
          <button class="text-[11px] font-black uppercase tracking-widest text-white/20 pb-1.5 hover:text-white/60 transition-all">Timeline</button>
        </div>
        <div class="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">Schedules</div>
      </div>

      <div class="space-y-4 pb-20">
        {#if isLoading}
          <div class="flex flex-col items-center justify-center py-20 opacity-40">
            <RefreshCw size={40} class="animate-spin mb-4" />
            <span class="text-[10px] font-black uppercase tracking-widest">Synchronizing Neural Grid...</span>
          </div>
        {:else if filteredAppointments.length > 0}
          {#each filteredAppointments as appt}
            <div class="group/appt relative p-6 rounded-[2rem] bg-gradient-to-br from-white/[0.04] to-transparent border border-white/5 shadow-xl transition-all duration-500 hover:bg-white/[0.08] hover:border-blue-500/20 hover:translate-y-[-2px]">
              <div class="flex flex-col md:flex-row gap-6">
                <!-- Time Column -->
                <div class="flex flex-row md:flex-col items-center md:items-start gap-2 md:gap-1 min-w-[80px]">
                  <span class="text-xl font-black text-white tracking-tighter">
                    {new Date(appt.start_time).getHours()}:{new Date(appt.start_time).getMinutes().toString().padStart(2, '0')}
                  </span>
                  <span class="text-[9px] font-black text-blue-400 uppercase tracking-[0.2em] md:mt-1">
                    {appt.recurring_type !== 'none' ? appt.recurring_type : 'ONE-TIME'}
                  </span>
                  <div class="hidden md:block w-6 h-[1px] bg-white/10 mt-3"></div>
                </div>

                <!-- Content Column -->
                <div class="flex-1 space-y-3">
                  <div class="flex items-start justify-between">
                    <div>
                      <h2 class="text-lg font-black tracking-tight text-white mb-1 leading-tight uppercase">{appt.title}</h2>
                      <div class="flex flex-wrap gap-2">
                        <span class="px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-[8px] font-black text-blue-400 uppercase tracking-widest">
                          {appt.status}
                        </span>
                        {#if appt.recurring_type === 'monthly'}
                           <span class="px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-[8px] font-black text-purple-400 uppercase tracking-widest">
                             Monthly Recurring
                           </span>
                        {/if}
                      </div>
                    </div>
                    <div class="flex items-center gap-1">
                       <button 
                         onclick={() => editAppointment(appt)}
                         class="p-2 text-white/20 hover:text-blue-400 transition-colors" title="Sửa"
                       >
                         <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                       </button>
                       <button 
                         onclick={() => deleteAppointment(appt.id)}
                         class="p-2 text-white/20 hover:text-red-400 transition-colors" title="Xóa"
                       >
                         <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
                       </button>
                    </div>
                  </div>

                  <div class="flex items-center justify-between pt-3 border-t border-white/5">
                    <p class="text-[11px] text-gray-500 font-medium line-clamp-1">{appt.description || 'No description provided.'}</p>
                    <button class="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-[9px] font-black uppercase tracking-widest hover:bg-white hover:text-black transition-all">
                      Details
                    </button>
                  </div>
                </div>
              </div>
            </div>
          {/each}
        {/if}

        <!-- Empty State -->
        {#if !isLoading && filteredAppointments.length === 0}
          <div class="p-12 rounded-[2rem] border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center opacity-20 hover:opacity-40 transition-all duration-700 cursor-pointer">
            <CalendarIcon size={48} strokeWidth={1} class="mb-4" />
            <h3 class="text-sm font-black uppercase tracking-[0.3em]">No more sessions</h3>
            <p class="text-[8px] font-bold mt-2 tracking-widest uppercase">Click (+) to schedule a new Neural Operation</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

<!-- Add Appointment Modal -->
{#if showAddModal}
  <div class="fixed inset-0 z-[3000] flex items-center justify-center p-4">
    <div 
      class="absolute inset-0 bg-black/80 backdrop-blur-xl"
      role="button"
      tabindex="0"
      aria-label="Close modal"
      onclick={() => showAddModal = false}
      onkeydown={(e) => e.key === 'Escape' && (showAddModal = false)}
    ></div>
    
    <div class="relative w-full max-w-xl bg-[#0a0a0a] border border-white/10 rounded-[2.5rem] p-8 lg:p-10 shadow-2xl overflow-y-auto max-h-[90vh] scrollbar-none">
      <div class="flex items-center justify-between mb-8">
        <div>
          <span class="text-[9px] font-black text-blue-500 uppercase tracking-[0.3em]">Initialize</span>
          <h2 class="text-2xl font-black tracking-tighter text-white uppercase">New Appointment</h2>
        </div>
        <button 
          onclick={() => showAddModal = false}
          class="p-2 text-white/20 hover:text-white transition-colors"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      <div class="space-y-6">
        <div>
          <label class="block text-[9px] font-black text-white/40 uppercase tracking-widest mb-2" for="title">Title</label>
          <input 
            id="title"
            bind:value={newAppt.title}
            type="text" 
            placeholder="Neural Sync Meeting..."
            class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-xs focus:outline-none focus:border-blue-500/50 transition-all font-bold tracking-tight"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-[9px] font-black text-white/40 uppercase tracking-widest mb-2" for="start">Start Time</label>
            <input 
              id="start"
              bind:value={newAppt.start_time}
              type="datetime-local" 
              class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-xs focus:outline-none focus:border-blue-500/50 transition-all font-bold"
            />
          </div>
          <div>
            <label class="block text-[9px] font-black text-white/40 uppercase tracking-widest mb-2" for="end">End Time</label>
            <input 
              id="end"
              bind:value={newAppt.end_time}
              type="datetime-local" 
              class="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-xs focus:outline-none focus:border-blue-500/50 transition-all font-bold"
            />
          </div>
        </div>

        <div>
          <div class="text-[9px] font-black text-white/40 uppercase tracking-widest mb-2">Recurring Type</div>
          <div class="flex flex-wrap gap-2">
            {#each ['none', 'daily', 'weekly', 'monthly'] as type}
              <button 
                onclick={() => newAppt.recurring_type = type as 'none' | 'daily' | 'weekly' | 'monthly'}
                class="px-4 py-2 rounded-lg border text-[9px] font-black uppercase tracking-widest transition-all
                {newAppt.recurring_type === type ? 'bg-blue-500 border-blue-500 text-white shadow-lg shadow-blue-500/20' : 'bg-white/5 border-white/5 text-white/40 hover:bg-white/10'}"
              >
                {type}
              </button>
            {/each}
          </div>
        </div>

        <div>
           <div class="text-[9px] font-black text-white/40 uppercase tracking-widest mb-2">Operation Type</div>
           <div class="flex flex-wrap gap-2">
             {#each ['STRATEGY', 'DEPLOYMENT', 'REVIEW'] as type}
               <button 
                 onclick={() => newAppt.type = type as 'STRATEGY' | 'DEPLOYMENT' | 'REVIEW'}
                 class="px-4 py-2 rounded-lg border text-[9px] font-black uppercase tracking-widest transition-all
                 {newAppt.type === type ? 'bg-purple-500 border-purple-500 text-white shadow-lg shadow-purple-500/20' : 'bg-white/5 border-white/5 text-white/40 hover:bg-white/10'}"
               >
                 {type}
               </button>
             {/each}
           </div>
        </div>

        <div>
           <div class="text-[9px] font-black text-white/40 uppercase tracking-widest mb-2">Stage Status</div>
           <div class="flex flex-wrap gap-2">
             {#each ['UPCOMING', 'ONGOING', 'COMPLETED'] as status}
               <button 
                 onclick={() => newAppt.status = status as 'UPCOMING' | 'ONGOING' | 'COMPLETED'}
                 class="px-4 py-2 rounded-lg border text-[9px] font-black uppercase tracking-widest transition-all
                 {newAppt.status === status ? 'bg-green-500 border-green-500 text-white shadow-lg shadow-green-500/20' : 'bg-white/5 border-white/5 text-white/40 hover:bg-white/10'}"
               >
                 {status}
               </button>
             {/each}
           </div>
        </div>

        {#if newAppt.recurring_type === 'monthly'}
          <div class="p-5 rounded-2xl bg-blue-500/5 border border-blue-500/10 space-y-4">
            <h4 class="text-[9px] font-black text-blue-400 uppercase tracking-[0.2em]">Monthly Configuration</h4>
            
            <div class="flex gap-2">
               <button 
                 onclick={() => newAppt.recurring_metadata.monthly_type = 'day_of_month'}
                 class="flex-1 py-2 rounded-xl border text-[9px] font-black uppercase tracking-widest transition-all
                 {newAppt.recurring_metadata.monthly_type === 'day_of_month' ? 'bg-blue-500/20 border-blue-500/40 text-blue-400' : 'bg-white/5 border-white/5 text-white/40'}"
               >
                 Theo Ngày (1-31)
               </button>
               <button 
                 onclick={() => newAppt.recurring_metadata.monthly_type = 'day_of_week'}
                 class="flex-1 py-2 rounded-xl border text-[9px] font-black uppercase tracking-widest transition-all
                 {newAppt.recurring_metadata.monthly_type === 'day_of_week' ? 'bg-blue-500/20 border-blue-500/40 text-blue-400' : 'bg-white/5 border-white/5 text-white/40'}"
               >
                 Theo Thứ
               </button>
            </div>

            {#if newAppt.recurring_metadata.monthly_type === 'day_of_month'}
               <div>
                 <input 
                   type="number" min="1" max="31"
                   bind:value={newAppt.recurring_metadata.day_of_month}
                   class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs focus:outline-none"
                 />
               </div>
            {:else}
              <div class="grid grid-cols-2 gap-2">
                  <select 
                    bind:value={newAppt.recurring_metadata.week_index}
                    class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs focus:outline-none appearance-none"
                  >
                    <option value={1} class="bg-[#0a0a0a]">Tuần 1</option>
                    <option value={2} class="bg-[#0a0a0a]">Tuần 2</option>
                    <option value={3} class="bg-[#0a0a0a]">Tuần 3</option>
                    <option value={4} class="bg-[#0a0a0a]">Tuần 4</option>
                    <option value={-1} class="bg-[#0a0a0a]">Tuần Cuối</option>
                  </select>
                  <select 
                    bind:value={newAppt.recurring_metadata.day_of_week}
                    class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs focus:outline-none appearance-none"
                  >
                    {#each ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'] as day, i}
                      <option value={i} class="bg-[#0a0a0a]">{day}</option>
                    {/each}
                  </select>
              </div>
            {/if}
          </div>
        {/if}

        <div class="pt-4">
          <button 
            onclick={saveAppointment}
            class="w-full py-4 rounded-2xl bg-white text-black text-xs font-black uppercase tracking-[0.2em] hover:bg-blue-500 hover:text-white transition-all shadow-xl shadow-white/5 active:scale-[0.98]"
          >
            Lưu Lịch Hẹn
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .scrollbar-none::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-none {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
