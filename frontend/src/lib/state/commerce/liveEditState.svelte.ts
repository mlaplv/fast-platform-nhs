import type { Product } from "$lib/types";

class LightLiveEdit {
  isEditMode = $state(false);
  dirtyProduct = $state<Product | null>(null);
  activePath = $state<string | null>(null);
  openPopoverId = $state<string | null>(null);
}

export const lightLiveEdit = new LightLiveEdit();
