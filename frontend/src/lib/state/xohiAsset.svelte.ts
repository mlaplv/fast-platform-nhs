import { xohiImageStore } from "./xohiImage.svelte";
import { nanobot } from "./nanobot.svelte";
import { vuiController } from "$lib/vui";
import { resolveMediaUrl } from "./utils";
import { untrack, tick } from "svelte";
import type { MediaAsset } from "./types";

export function createAssetController(config: {
    getAssets: () => (MediaAsset | string)[];
    setAssets: (v: (MediaAsset | string)[]) => void;
    getReserveAssets: () => (MediaAsset | string)[];
    setReserveAssets: (v: (MediaAsset | string)[]) => void;
    setSelectedAvatarUrl: (v: string | null) => void;
    setSelectedAssetIndex: (v: number) => void;
    syncAssetChanges: (step: number, newIndex?: number) => void;
}) {
    let showLibrary = $state(false);
    let pendingPurgeAsset = $state<MediaAsset | null>(null);

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

        // CNS V82.5: Efficient sequence check instead of heavy JSON.stringify (Rule R03)
        const isDifferent = storeAssets.length !== currentAssets.length || 
                           storeAssets.some((a, i) => {
                               const ca = currentAssets[i];
                               if (!ca) return true;
                               if (typeof ca === 'string') return a.file_path !== ca && a.url !== ca;
                               return a.id !== ca.id || a.is_primary !== ca.is_primary || a.order_index !== ca.order_index;
                           });

        if (isDifferent) {
            config.setAssets(storeAssets);
            const primaryIdx = storeAssets.findIndex((a) => a.is_primary);
            if (primaryIdx !== -1) {
                config.setSelectedAssetIndex(primaryIdx);
                config.setSelectedAvatarUrl(resolveMediaUrl(
                    storeAssets[primaryIdx].file_path || storeAssets[primaryIdx].url || ''
                ));
            } else if (storeAssets.length === 0) {
                config.setSelectedAssetIndex(0);
                config.setSelectedAvatarUrl(null);
            }
            
            // CNS V82.6: Debounced Sync to prevent "API Storm" during rapid modifications
            if (syncTimer) clearTimeout(syncTimer);
            syncTimer = setTimeout(() => {
                untrack(() => config.syncAssetChanges(2));
            }, 500); // 500ms safety window
        }

        return () => {
            if (syncTimer) clearTimeout(syncTimer);
        };
    });

    async function confirmPurge(asset: MediaAsset) {
        if (!asset.id) return;
        try {
            await xohiImageStore.removeAsset(asset.id, true);
            vuiController.speak("Đã xoá dứt điểm ảnh khỏi hệ thống.");
            pendingPurgeAsset = null;
        } catch (err) {
            console.error("[AssetController] Purge failed", err);
            vuiController.speak("Dạ, có lỗi khi xoá dứt điểm ảnh ạ.");
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
                } catch (err) {
                    console.error("[AssetController] Library sync failed", err);
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

    function addFromReserve(url: string, index: number) {
        vuiController.speak("Đã thêm vào bộ sưu tập.");
        xohiImageStore.addImagesFromUrl(url as string);
        const reserves = config.getReserveAssets().filter((_, idx) => idx !== index);
        config.setReserveAssets(reserves);
    }

    async function removeFromReserve(index: number) {
        const reserves = config.getReserveAssets().filter((_, idx) => idx !== index);
        config.setReserveAssets(reserves);
        await tick();
        config.syncAssetChanges(2);
        vuiController.speak("Đã xóa khỏi kho dự phòng.");
    }

    return {
        get showLibrary() { return showLibrary; },
        set showLibrary(v) { showLibrary = v; },
        get pendingPurgeAsset() { return pendingPurgeAsset; },
        set pendingPurgeAsset(v) { pendingPurgeAsset = v; },
        confirmPurge,
        handleLibrarySelect,
        addFromReserve,
        removeFromReserve
    };
}
