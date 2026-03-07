export function createTrainingState(voice: any) {
  const state = $state({
    isTraining: false,
    trainingType: null as "wake" | "sleep" | null,
    trainingResult: null as string | string[] | null,
  });

  function setTraining(val: boolean, type: "wake" | "sleep" | null = null) {
    state.isTraining = val;
    state.trainingType = type;
    if (val) state.trainingResult = null;
  }

  function completeTraining(result: string | string[]) {
    state.trainingResult = result;
    state.isTraining = false;
    voice.resetVui();
    import("./omni.svelte").then(({ omni }) => omni.stopTrainingRec());
  }

  function cancelTraining() {
    state.isTraining = false;
    state.trainingType = null;
    state.trainingResult = null;
    voice.resetVui();
    import("./omni.svelte").then(({ omni }) => omni.stopTrainingRec());
  }

  return {
    get isTraining() { return state.isTraining; },
    get trainingType() { return state.trainingType; },
    get trainingResult() { return state.trainingResult; },
    setTraining,
    completeTraining,
    cancelTraining
  };
}
