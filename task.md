# Task: Elite V3.0 Agentic Fraud Stabilization

- [x] **AI-Guard Initialization**: Implement global asset hardening in `hooks.client.ts` (Replaced by In-situ Injection).
- [x] **WASM Gateway**: Host `onnxruntime-web` binaries on API Gateway (`api.osmo.vn/wasm`).
- [x] **VAD Gateway**: Host Silero VAD assets on API Gateway (`api.osmo.vn/vad`).
- [x] **Universal AI Core**: Use global `window.ort` via `<script>` tag to bypass Vite's module bugs.
- [x] **SSR Stealth**: Implement dynamic imports and browser guards in `BehaviorEngine` and `VuiVadEngine`.
- [x] **Backend Optimization**: Switch to `create_static_files_router` and fix `copy_scope` warnings.
- [x] **Model Hardening**: Implement absolute URL resolution for `.onnx` models via API Gateway.
- [x] **Rule-based Fallback**: Implement graceful fallback in `BehaviorEngine` for missing models (User-assisted).
- [x] **Verification**: Verify zero console errors for WASM/VAD assets.
- [x] **Evidence**: Create `walkthrough.md` with forensic proof.
