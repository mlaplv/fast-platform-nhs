// [Elite V3.0] Global AI Core: Using the pre-loaded window.ort
declare global {
    interface Window { ort: any; }
}

export class BehaviorEngine {
    private session: any = null;
    private initialized = false;

    async init(modelPath?: string) {
        if (this.initialized) return;
        
        // [Elite V3.0] SSR Stealth: Guarding against server-side execution
        if (typeof window === 'undefined') return;

        // [Elite V2.2] Lazy Load AI Core (ort.min.js)
        if (!window.ort) {
            console.log("🛡️ [BehaviorEngine] Loading AI Core (ort.min.js) dynamically...");
            try {
                await new Promise<void>((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = '/wasm/ort.min.js';
                    script.async = true;
                    script.onload = () => {
                        console.log("🛡️ [BehaviorEngine] AI Core loaded successfully!");
                        resolve();
                    };
                    script.onerror = (e) => {
                        reject(new Error("Failed to load script"));
                    };
                    document.head.appendChild(script);
                });
            } catch (err) {
                console.warn("🛡️ [BehaviorEngine] Failed to load dynamic AI Core. Falling back to rules.", err);
                this.initialized = true;
                return;
            }
        }
        
        const ort = window.ort;
        if (!ort) return;

        // [Elite V3.0] Rule-based Fallback if no model is provided
        if (!modelPath) {
            console.log("🛡️ [BehaviorEngine] Operating in Rule-based mode (No model specified).");
            this.initialized = true;
            return;
        }

        // [Elite V3.0] In-situ Asset Injection & Model Hardening
        const apiBase = `${window.location.protocol}//api.${window.location.hostname.split('.').slice(-2).join('.')}`;
        
        // Harden model path if it's relative
        const hardenedModelPath = modelPath.startsWith('/') 
            ? `${apiBase}${modelPath}` 
            : modelPath;

        try {
            const wasmBase = `${apiBase}/wasm`;
            
            ort.env.wasm.wasmPaths = {
                'ort-wasm-simd-threaded.wasm': `${wasmBase}/ort-wasm-simd-threaded.wasm`,
                'ort-wasm-simd-threaded.jsep.wasm': `${wasmBase}/ort-wasm-simd-threaded.jsep.wasm`,
                'ort-wasm-simd.wasm': `${wasmBase}/ort-wasm-simd.wasm`,
                'ort-wasm.wasm': `${wasmBase}/ort-wasm.wasm`,
                'ort-wasm-simd-threaded.jsep.mjs': `${wasmBase}/ort-wasm-simd-threaded.jsep.mjs`,
                'ort-wasm-simd-threaded.mjs': `${wasmBase}/ort-wasm-simd-threaded.mjs`,
            };
            ort.env.wasm.numThreads = 1;
            ort.env.wasm.proxy = false;

            this.session = await ort.InferenceSession.create(hardenedModelPath, {
                executionProviders: ['wasm'], 
                graphOptimizationLevel: 'all'
            });
            
            this.initialized = true;
            console.log("🛡️ [BehaviorEngine] Engine Active via API Gateway.");
        } catch (e) {
            console.info("ℹ️ [BehaviorEngine] Model load skipped or failed. Using Rule-based Edge Detection.", e);
            this.initialized = true; // Mark as initialized to use fallback logic in predict
        }
    }

    async predict(features: number[]): Promise<number> {
        if (!this.session) {
            // [Elite V3.0] Rule-based Fallback Heuristics
            const eventDensity = features.reduce((a, b) => a + b, 0) / features.length;
            if (eventDensity > 50) return 0.8; // Quá nhiều sự kiện trong thời gian ngắn
            if (eventDensity < 1) return 0.9;  // Không có tương tác
            return 0.2; // Bình thường
        }

        try {
            // Prepare input tensor (ví dụ: behavior sequences)
            const data = Float32Array.from(features);
            const tensor = new ort.Tensor('float32', data, [1, features.length]);
            
            // Run inference
            const feeds: Record<string, ort.Tensor> = {};
            feeds[this.session.inputNames[0]] = tensor;
            
            const results = await this.session.run(feeds);
            const output = results[this.session.outputNames[0]];
            
            return (output.data as Float32Array)[0];
        } catch (e) {
            console.error("❌ [BehaviorEngine] Prediction error:", e);
            return 0;
        }
    }

    /**
     * [Elite V3.0] Bảo hiểm Chuyển đổi (Conversion Insurance)
     * Ưu tiên Doanh thu > Chặn Bot. Nếu phát hiện hành vi mua hàng, bypass mọi fraud score.
     */
    static detectHighIntent(url: string, lastElementClicked: string): boolean {
        const highIntentPatterns = ['checkout', 'pricing', 'cart', 'order', 'booking', 'contact'];
        const isHighIntent = highIntentPatterns.some(p => url.toLowerCase().includes(p)) || 
                           highIntentPatterns.some(p => lastElementClicked.toLowerCase().includes(p));
        
        if (isHighIntent) {
            console.log("💎 [BehaviorEngine] High-intent detected. Activating Conversion Insurance.");
            return true;
        }
        return false;
    }

    /**
     * Thu thập dữ liệu hành vi cơ bản để đưa vào model.
     */
    static collectFeatures(events: any[]): number[] {
        // ... (existing logic)
        return events.map(e => Number(e.value) || 0);
    }
}

export const behaviorEngine = new BehaviorEngine();
