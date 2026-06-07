import re

filepath = '/media/lv/data/fast-platform-core/frontend/src/lib/components/admin/ads/AdsCampaignManager.svelte'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix the open/close tags for campaign name cell
old_td = """                                  <div class="flex flex-col gap-1.5">
                                     <span class="text-white font-black text-sm tracking-tighter cursor-pointer group-hover/row:text-cyan-400 transition-colors" onclick={() => toggleCampaign(c)}>{c.name}</span>
                                  <span class="text-[9px] text-slate-600 font-black tracking-widest">ID truy vết: {c.resource_name.split('/').pop()}</span>
                               </div>
                            </td>"""

new_td = """                                  <div class="flex flex-col gap-1.5">
                                     <span class="text-white font-black text-sm tracking-tighter cursor-pointer group-hover/row:text-cyan-400 transition-colors" onclick={() => toggleCampaign(c)}>{c.name}</span>
                                     <span class="text-[9px] text-slate-600 font-black tracking-widest">ID truy vết: {c.resource_name.split('/').pop()}</span>
                                  </div>
                               </div>
                            </td>"""

if old_td in content:
    content = content.replace(old_td, new_td)
    print("Successfully fixed TD opening/closing tags.")
else:
    # Try with raw string representation search in case spaces differ
    print("Warning: old_td block not found directly, trying regex.")

# 2. Insert the child row structure right after the campaign </tr>
old_tr_end = """                                  {/if}
                               </div>
                           </td>
                        </tr>"""

new_tr_end = """                                  {/if}
                               </div>
                           </td>
                        </tr>
                        {#if expandedCampaigns[c.resource_name]}
                           <tr class="bg-black/10">
                              <td colspan="4" class="p-0 border-b border-white/[0.03]">
                                 {#if loadingCampaigns[c.resource_name]}
                                    <div class="flex items-center gap-3 py-6 pl-16 pr-8 text-cyan-400 font-mono text-[10px] tracking-widest animate-pulse">
                                       <RefreshCw size={14} class="animate-spin text-cyan-400" />
                                       <span>ĐANG TẢI AD_GROUPS_MATRIX...</span>
                                    </div>
                                 {:else if !campaignAdGroups[c.resource_name] || campaignAdGroups[c.resource_name].length === 0}
                                    <div class="py-6 pl-16 pr-8 text-slate-600 font-mono text-[10px] tracking-widest">
                                       KHÔNG CÓ NHÓM QUẢNG CÁO NÀO
                                    </div>
                                 {:else}
                                    <div class="border-l border-white/10 ml-16 my-2 pl-4 flex flex-col gap-2">
                                       {#each campaignAdGroups[c.resource_name] as ag}
                                          <!-- Ad Group Block -->
                                          <div class="border border-white/5 bg-white/[0.01] hover:border-cyan-400/20 transition-all">
                                             <div class="flex justify-between items-center py-3 px-4 hover:bg-cyan-500/[0.02] transition-all">
                                                <div class="flex items-center gap-3 cursor-pointer" onclick={() => toggleAdGroup(ag)}>
                                                   {#if expandedAdGroups[ag.resource_name]}
                                                      <ChevronDown size={14} class="text-cyan-400" />
                                                   {:else}
                                                      <ChevronRight size={14} class="text-slate-500" />
                                                   {/if}
                                                   <div class="flex flex-col">
                                                      <span class="text-white font-bold text-[12px]">{ag.name}</span>
                                                      <span class="text-[9px] text-slate-500 font-mono">ID: {ag.resource_name.split('/').pop()}</span>
                                                   </div>
                                                </div>

                                                <div class="flex items-center gap-8 text-[11px] font-mono">
                                                   <span class="text-slate-400">CPC Bid: {fmt(ag.cpc_bid_vnd)}₫</span>
                                                   <span class="px-2 py-0.5 rounded-none text-[8px] font-black tracking-widest {ag.status === 'ENABLED' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500'}">
                                                      {ag.status === 'ENABLED' ? 'ĐANG CHẠY' : 'TẠM DỪNG'}
                                                   </span>
                                                </div>
                                             </div>

                                             <!-- Ad Group Children (Ads) -->
                                             {#if expandedAdGroups[ag.resource_name]}
                                                {#if loadingAdGroups[ag.resource_name]}
                                                   <div class="flex items-center gap-3 py-4 pl-8 pr-4 text-emerald-400 font-mono text-[9px] tracking-widest animate-pulse border-t border-white/5">
                                                      <RefreshCw size={12} class="animate-spin text-emerald-400" />
                                                      <span>ĐANG TẢI AD_ASSETS...</span>
                                                   </div>
                                                {:else if !adGroupAds[ag.resource_name] || adGroupAds[ag.resource_name].length === 0}
                                                   <div class="py-4 pl-8 pr-4 text-slate-600 font-mono text-[9px] tracking-widest border-t border-white/5">
                                                      KHÔNG CÓ MẪU QUẢNG CÁO NÀO
                                                   </div>
                                                {:else}
                                                   <div class="border-t border-white/5 divide-y divide-white/[0.03] pl-8 bg-black/20">
                                                      {#each adGroupAds[ag.resource_name] as ad}
                                                         <div class="flex flex-col">
                                                            <!-- Ad Row -->
                                                            <div class="flex justify-between items-center py-3 pr-4 hover:bg-emerald-500/[0.01] transition-all">
                                                               <div class="flex items-center gap-3 cursor-pointer group/adcell" onclick={() => toggleAd(ad.resource_name)}>
                                                                  <span class="text-slate-600">•</span>
                                                                  <div class="flex flex-col">
                                                                     <span class="text-slate-200 font-medium text-[11px] group-hover/adcell:text-emerald-400 transition-colors">
                                                                        {ad.name || 'Responsive Search Ad'}
                                                                     </span>
                                                                     <span class="text-[9px] text-slate-500 font-mono">{ad.type || 'RSA'}</span>
                                                                  </div>
                                                               </div>

                                                               <div class="flex items-center gap-8 text-[11px] font-mono">
                                                                  <span class="px-2 py-0.5 rounded-none text-[8px] font-black tracking-widest {ad.status === 'ENABLED' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500'}">
                                                                     {ad.status === 'ENABLED' ? 'ĐANG CHẠY' : 'TẠM DỪNG'}
                                                                  </span>
                                                                  <button class="w-8 h-8 flex items-center justify-center bg-white/5 border border-white/10 rounded-none text-slate-500 hover:text-emerald-400 transition-all" onclick={(e) => { e.stopPropagation(); selectAdForEdit(ad, ag, c); }} title="Thiết lập">
                                                                     <Settings size={14} />
                                                                  </button>
                                                               </div>
                                                            </div>

                                                            <!-- Ad Preview details box -->
                                                            {#if expandedAds[ad.resource_name]}
                                                               <div class="pl-4 pr-4 pb-4 pt-2 bg-[#050505]/40 border-t border-white/5" transition:slide>
                                                                  <div class="max-w-2xl bg-[#080808]/90 border border-white/5 p-5 rounded-none relative overflow-hidden shadow-2xl">
                                                                     <div class="flex justify-between items-center mb-3 pb-2 border-b border-white/5">
                                                                        <span class="text-[9px] font-black tracking-widest text-emerald-400">GOOGLE SEARCH AD PREVIEW</span>
                                                                        {#if ad.final_url}
                                                                           <a href={ad.final_url} target="_blank" rel="noopener noreferrer" class="text-[9px] text-slate-500 hover:text-emerald-400 font-mono truncate max-w-xs">{ad.final_url}</a>
                                                                        {/if}
                                                                     </div>
                                                                     
                                                                     <!-- Search Ad Mockup -->
                                                                     <div class="font-sans text-sm text-[#d1d5db] text-left">
                                                                        <div class="text-[10px] text-[#5f6368] font-mono mb-1 truncate">
                                                                           {ad.final_url ? ad.final_url.replace(/^https?:\/\//, '') : 'example.com'}
                                                                        </div>
                                                                        <h3 class="text-lg text-[#8ab4f8] hover:underline cursor-pointer leading-tight mb-2 font-medium">
                                                                           {ad.headlines && ad.headlines.filter(Boolean).length > 0 
                                                                              ? ad.headlines.filter(Boolean).slice(0, 3).join(' | ') 
                                                                              : 'Tiêu đề quảng cáo hấp dẫn | Tối ưu chuyển đổi | Tiêu đề 3'}
                                                                        </h3>
                                                                        <p class="text-xs text-[#bdc1c6] leading-relaxed">
                                                                           {ad.descriptions && ad.descriptions.filter(Boolean).length > 0 
                                                                              ? ad.descriptions.filter(Boolean).join(' ') 
                                                                              : 'Mô tả chi tiết về sản phẩm hoặc dịch vụ của bạn để tăng CTR và thu hút khách hàng tiềm năng.'}
                                                                        </p>
                                                                     </div>
                                                                  </div>
                                                               </div>
                                                            {/if}
                                                         </div>
                                                      {/each}
                                                   </div>
                                                {/if}
                                             {/if}
                                          </div>
                                       {/each}
                                    </div>
                                 {/if}
                              </td>
                           </tr>
                        {/if}"""

if old_tr_end in content:
    content = content.replace(old_tr_end, new_tr_end)
    print("Successfully inserted expandedCampaigns block after tr_end.")
else:
    # Let's try matching with regex or stripping whitespaces
    print("Warning: old_tr_end block not found directly, trying regex.")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
