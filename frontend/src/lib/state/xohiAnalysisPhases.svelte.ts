import { onDestroy } from "svelte";

export const PHASES = {
    copyright: [
        { icon: '🧬', label: '[NFC] Chuẩn hóa Unicode & Content', duration: 1500 },
        { icon: '📡', label: '[RECON] Trinh sát Google & Đối thủ', duration: 4500 },
        { icon: '🧠', label: '[SEMANTIC] Gemini phân tích ngữ nghĩa', duration: 3500 },
        { icon: '📊', label: '[QUANTUM] Tổng hợp rủi ro bản quyền', duration: 2000 },
    ],
    seo: [
        { icon: '🔍', label: '[SCAN] Phân tích Ranking Signals', duration: 1500 },
        { icon: '📡', label: '[RECON] So đối thủ & Intent', duration: 4000 },
        { icon: '🧠', label: '[JUDGE] Chấm điểm Semantic SEO', duration: 3500 },
        { icon: '✨', label: '[QUANTUM] Hoàn tất bộ lọc SEO', duration: 2000 },
    ],
    ai: [
        { icon: '📝', label: '[GEO] Structural Scan bài viết', duration: 1500 },
        { icon: '⚡', label: '[SURGEON] Phân tích NLP Entity', duration: 3500 },
        { icon: '🌟', label: '[JUDGE] Đánh giá AI Readiness', duration: 3000 },
        { icon: '📊', label: '[QUANTUM] Xuất báo cáo Viral Edge', duration: 2000 },
    ],
    enrich: [
        { icon: '🔍', label: 'Thu thập số liệu từ Google', duration: 3000 },
        { icon: '🧠', label: 'Phân tích insight đối thủ', duration: 2500 },
        { icon: '✍️', label: 'Tổng hợp expert quotes', duration: 3500 },
        { icon: '📋', label: 'Tạo bảng so sánh tính năng', duration: 3000 },
        { icon: '🚀', label: 'Inject & polish content', duration: 3000 },
    ],
    rewrite: [
        { icon: '🚀', label: '[SCAN] Khởi động Neural Rewrite', duration: 1500 },
        { icon: '🧠', label: '[FACTS] Nạp bối cảnh & Dữ liệu thực', duration: 2500 },
        { icon: '🖋️', label: '[CREATIVE] Gemini đang múa bút...', duration: 5500 },
        { icon: '✨', label: '[QUANTUM] Phẫu thuật sáng tạo hoàn tất', duration: 2000 },
    ],
};

export function createPhaseController() {
    let phaseIndex = $state(0);
    let phaseProgress = $state(0);
    let phaseTimer: ReturnType<typeof setTimeout> | null = null;
    let progressTimer: ReturnType<typeof setInterval> | null = null;

    function clearTimers() {
        if (phaseTimer) { clearTimeout(phaseTimer); phaseTimer = null; }
        if (progressTimer) { clearInterval(progressTimer); progressTimer = null; }
    }

    function startPhaseEngine(type: keyof typeof PHASES) {
        clearTimers();
        phaseIndex = 0;
        phaseProgress = 0;
        const phases = PHASES[type];

        function runPhase(idx: number) {
            if (idx >= phases.length) return;
            phaseIndex = idx;
            phaseProgress = 0;
            const dur = phases[idx].duration;
            const step = 16;
            progressTimer = setInterval(() => {
                phaseProgress = Math.min(phaseProgress + (step / dur) * 100, 95);
            }, step);
            phaseTimer = setTimeout(() => {
                if (progressTimer) clearInterval(progressTimer);
                phaseProgress = 100;
                // Capture the next phase timeout to prevent leak
                phaseTimer = setTimeout(() => runPhase(idx + 1), 150);
            }, dur);
        }
        runPhase(0);
    }

    function jumpToPhase(idx: number, type: keyof typeof PHASES) {
        const phases = PHASES[type];
        // Guard: stop recursion when idx is out of bounds (all phases complete)
        if (idx >= phases.length) {
            phaseProgress = 100;
            return;
        }
        if (idx === phaseIndex) return;
        clearTimers();
        phaseIndex = idx;
        phaseProgress = 0;
        
        const dur = phases[idx].duration;
        const step = 16;
        
        progressTimer = setInterval(() => {
            phaseProgress = Math.min(phaseProgress + (step / dur) * 100, 98);
        }, step);
        
        phaseTimer = setTimeout(() => {
            if (progressTimer) clearInterval(progressTimer);
            phaseProgress = 100;
            phaseTimer = setTimeout(() => jumpToPhase(idx + 1, type), 150);
        }, dur);
    }

    function syncWithLogs(logs: string[], type: keyof typeof PHASES) {
        if (!logs || logs.length === 0) return;
        const phases = PHASES[type];
        const lastLog = logs[logs.length - 1];
        
        // Find the highest phase index that matches the logs
        let targetIdx = -1;
        for (let i = 0; i < phases.length; i++) {
            const label = phases[i].label;
            // Extract the [TAG] from the label, e.g. "[RECON]"
            const tagMatch = label.match(/\[(.*?)\]/);
            if (tagMatch && lastLog.includes(tagMatch[0])) {
                targetIdx = i;
            }
        }
        
        if (targetIdx !== -1 && targetIdx > phaseIndex) {
            jumpToPhase(targetIdx, type);
        }
    }

    return {
        get phaseIndex() { return phaseIndex; },
        get phaseProgress() { return phaseProgress; },
        startPhaseEngine,
        syncWithLogs,
        clearTimers
    };
}
