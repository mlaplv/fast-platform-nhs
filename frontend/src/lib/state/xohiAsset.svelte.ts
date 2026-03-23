import { xohiImageStore } from "./xohiImage.svelte";
import { nanobot } from "./nanobot.svelte";
import { resolveMediaUrl } from "./utils";
import { untrack, tick } from "svelte";
import type { MediaAsset } from "./types";
import { vuiController } from "../vui";

export function createAssetController(config: {
    get id(): string;
    getAssets: () => (MediaAsset | string)[];
    setAssets: (v: (MediaAsset | string)[]) => void;
    getReserveAssets: () => (MediaAsset | string)[];
    setReserveAssets: (v: (MediaAsset | string)[]) => void;
    getIsProcessing: () => boolean;
    setSelectedAvatarUrl: (v: string | null) => void;
    setSelectedAssetIndex: (v: number) => void;
    syncAssetChanges: () => (step: number, newIndex?: number) => void;
}) {
    let showLibrary = $state(false);
    let pendingPurgeAsset = $state<MediaAsset | null>(null);
    let hasAutoRescued = $state(false);
    let blockPropSync = false; // CNS V82.17: Bridge-lock to prevent ping-pong loop

    // Phase 15.5: Rescue Mechanism (Auto-promote from reserve)
    $effect(() => {
        const isProcessing = config.getIsProcessing();
        if (isProcessing) {
            if (hasAutoRescued) hasAutoRescued = false;
            return;
        }

        if (hasAutoRescued) return;

        const storeAssets = xohiImageStore.assets;
        const reserveAssets = config.getReserveAssets();
        const propAssets = config.getAssets(); // CNS V82.37: Check prop assets too

        // Only rescue if BOTH store and prop are empty, but we have reserves
        if (storeAssets.length === 0 && propAssets.length === 0 && reserveAssets.length > 0) {
            hasAutoRescued = true;
            untrack(() => {
                const first = reserveAssets[0];
                const url = typeof first === 'string' ? first : (first.file_path || first.url || '');
                if (url && (url.startsWith('http') || url.startsWith('/storage'))) {
                    vuiController.speak("Đã tự động lấy hình dự phòng cho Sếp.");
                    xohiImageStore.addImagesFromUrl(url);
                    const nextReserves = reserveAssets.filter((_: MediaAsset | string, i: number) => i !== 0);
                    config.setReserveAssets(nextReserves);
                    config.syncAssetChanges()(2);
                }
            });
        }
    });

    // Phase 15.6: Reactive Prop Sync (Bridge Prop -> Store)
    $effect(() => {
        const propAssets = config.getAssets();
        const propId = config.id;
        
        untrack(() => {
            // CNS V82.37: Only sync pulse data into store if store is empty or bridge is unlocked
            // This prevents the "empty store overwriting valid prop" race condition
            if (propAssets && propAssets.length > 0 && !blockPropSync) {
                if (xohiImageStore.assets.length === 0 || xohiImageStore.campaignId !== propId) {
                    xohiImageStore.initAssets(propAssets, propId);
                }
            }
        });
    });

    // V22: Voice Mutation Injection - Asset Management
    $effect(() => {
        const action = nanobot.commandAction;
        if (!action || action.consumed) return;

        if (action.entity === "media") {
            // 1. Giao thức Thêm ảnh (Create)
            if (action.verb === "create" && action.args) {
                if (nanobot.consumeCommand(action.verb, action.entity)) {
                    xohiImageStore.addImagesFromUrl(action.args);
                    vuiController.speak("Dạ, em đã thêm ảnh theo yêu cầu của Sếp rồi ạ.");
                }
            }

            // 2. Giao thức Cắt ảnh AI (Edit/Smart Crop)
            if (action.verb === "edit" && action.args) {
                if (nanobot.consumeCommand(action.verb, action.entity)) {
                    const parts = action.args.split(" ");
                    const index = parseInt(parts[0]) - 1;
                    const preset = (parts[1] || "square") as "square" | "banner" | "story" | "feed";

                    const targetAsset = xohiImageStore.assets[index];
                    if (targetAsset) {
                        vuiController.speak(`Dạ, em đang cắt ảnh số ${index + 1} theo khung ${preset} cho Sếp đây ạ.`);
                        xohiImageStore.smartCrop(targetAsset.id, preset);
                    } else {
                        vuiController.speak("Dạ Sếp ơi, em không tìm thấy ảnh đó để cắt ạ.");
                    }
                }
            }

            // 3. Giao thức Xóa ảnh (Delete)
            if (action.verb === "delete" && action.args) {
                if (nanobot.consumeCommand(action.verb, action.entity)) {
                    const index = parseInt(action.args) - 1;
                    const targetAsset = xohiImageStore.assets[index];
                    if (targetAsset) {
                        xohiImageStore.removeAsset(targetAsset.id);
                        vuiController.speak(`Dạ, em đã xóa ảnh số ${index + 1} rồi ạ.`);
                    }
                }
            }
        }
    });

    // Phase 15.3: Đồng bộ ngược lại khi Store thay đổi (Optimistic Sync)
    let syncTimer: ReturnType<typeof setTimeout> | null = null;
    $effect(() => {
        const storeAssets = xohiImageStore.assets;
        const currentAssets = untrack(() => config.getAssets());

        // CNS V82.5: Stable comparison logic
        const isDifferent = storeAssets.length !== currentAssets.length || 
                           storeAssets.some((a, i) => {
                               const ca = currentAssets[i];
                               if (!ca) return true;
                               const isCaString = typeof ca === 'string';
                               const caId = isCaString ? `stbl_${ca.split('/').pop()?.split('?')[0]}` : ca.id;
                               const caIsPrimary = isCaString ? false : (ca as MediaAsset).is_primary;
                               return a.id !== caId || a.is_primary !== caIsPrimary;
                           });

        if (isDifferent) {
            blockPropSync = true;
            config.setAssets([...storeAssets]);
            // Re-enable sync after a tick to allow the prop change to propagate
            tick().then(() => { blockPropSync = false; });
            
            const primaryIdx = storeAssets.findIndex((a) => a.is_primary);
            if (primaryIdx !== -1) {
                config.setSelectedAssetIndex(primaryIdx);
                config.setSelectedAvatarUrl(resolveMediaUrl(
                    storeAssets[primaryIdx].file_path || storeAssets[primaryIdx].url || ''
                ));
            }

            if (syncTimer) clearTimeout(syncTimer);
            syncTimer = setTimeout(() => {
                untrack(() => config.syncAssetChanges()(2));
            }, 1000); // Increased debounce to 1s for stability
        }

        return () => { if (syncTimer) clearTimeout(syncTimer); };
    });

    async function confirmPurge(asset: MediaAsset) {
        if (!asset.id) return;
        try {
            await xohiImageStore.removeAsset(asset.id, true);
            vuiController.speak("Đã xoá dứt điểm ảnh khỏi hệ thống.");
            pendingPurgeAsset = null;
        } catch (err: unknown) {
            vuiController.speak(`Dạ, có lỗi khi xoá dứt điểm ảnh ạ: ${err instanceof Error ? err.message : String(err)}`);
        }
    }

    async function handleLibrarySelect(selectedAssets: MediaAsset[]) {
        let addCount = 0;
        for (const asset of selectedAssets) {
            if (!xohiImageStore.assets.find(a => a.id === asset.id)) {
                try {
                    const assetUrl = asset.file_path || asset.url;
                    if (assetUrl) {
                        await xohiImageStore.addImagesFromUrl(assetUrl);
                        addCount++;
                    }
                } catch (err: unknown) {
                    // Fail silently for bulk sync
                }
            }
        }
        showLibrary = false;
        if (addCount > 0) {
            vuiController.speak(`Dạ, em đã lấy ${addCount} ảnh từ thư viện cho Sếp rồi ạ.`);
        } else {
            vuiController.speak("Dạ, các ảnh này đã có sẵn trong dự án rồi ạ.");
        }
    }

    async function addFromReserve(url: string) {
        try {
            vuiController.speak("Đã thêm vào bộ sưu tập.");
            await xohiImageStore.addImagesFromUrl(url);
            // CNS V82.20: Remove from reserve after successful store addition
            const reserve = untrack(() => config.getReserveAssets());
            config.setReserveAssets(reserve.filter((_: MediaAsset | string, idx: number) => (typeof reserve[idx] === 'string' ? reserve[idx] : (reserve[idx] as MediaAsset).url) !== url));
            config.syncAssetChanges()(2);
        } catch (err: unknown) {
            vuiController.speak(`Dạ Sếp ơi, có biến khi lấy ảnh từ kho: ${err instanceof Error ? err.message : String(err)}`);
        }
    }

    async function removeFromReserve(index: number) {
        try {
            const reserves = config.getReserveAssets().filter((_: MediaAsset | string, idx: number) => idx !== index);
            config.setReserveAssets(reserves);
            await tick();
            config.syncAssetChanges()(2);
            vuiController.speak("Đã xóa khỏi kho dự phòng.");
        } catch (error: unknown) {
            vuiController.speak(`Lỗi khi xóa ảnh dự phòng: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    function handleDndConsider(e: { detail: { items: (MediaAsset | string)[] } }) {
        config.setAssets(e.detail.items);
    }
    function handleDndFinalize(e: { detail: { items: (MediaAsset | string)[] } }) {
        config.setAssets(e.detail.items);
        config.syncAssetChanges()(2);
    }

    return {
        get showLibrary() { return showLibrary; },
        set showLibrary(v) { showLibrary = v; },
        get pendingPurgeAsset() { return pendingPurgeAsset; },
        set pendingPurgeAsset(v) { pendingPurgeAsset = v; },
        confirmPurge,
        handleLibrarySelect,
        addFromReserve,
        removeFromReserve,
        syncFromProp: () => {
            // CNS V82.17: Force sync without logs
            config.syncAssetChanges()(2);
            const propAssets = config.getAssets();
            if (propAssets) xohiImageStore.initAssets(propAssets, config.id);
        }
    };
}
