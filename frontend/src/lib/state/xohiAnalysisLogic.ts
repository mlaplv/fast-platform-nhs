/**
 * CNS V88.2: Neural Surgical Stitching (Logic Layer)
 * Ports of backend algorithms for local DOM synchronization.
 * Elite V2.2: Neural Refinement Stitching (Frontend Shim)
 * Mirrors backend stitcher.py logic for consistent ad-hoc fixes.
 */

export function robustNormalize(text: string): string {
    if (!text) return "";
    return text.normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '') // Strip accents
        .replace(/<[^>]+>/g, '') // Strip HTML
        .replace(/[^\p{L}\p{N}]/gu, '') // Keep only letters and numbers
        .toLowerCase();
}

export function refinementStitch(content: string, oldText: string, newText: string): string {
    content = content.normalize('NFC');
    oldText = oldText.normalize('NFC');
    newText = newText.normalize('NFC');

    // Phase 1: Exact Match (Fast Path)
    if (content.includes(oldText)) {
        return content.replace(oldText, newText);
    }

    // Phase 2: Alphanumeric Mapping (HTML-Aware)
    const normOld = robustNormalize(oldText);
    if (normOld.length < 5) return content;

    const parts = content.split(/(<[^>]+>)/);
    let plainBuffer = "";
    const plainToHtmlMap: number[] = [];
    let htmlPos = 0;

    for (const part of parts) {
        if (part.startsWith('<')) {
            htmlPos += part.length;
        } else {
            for (let i = 0; i < part.length; i++) {
                const ch = part[i];
                if (/[\p{L}\p{N}]/u.test(ch)) {
                    plainToHtmlMap.push(htmlPos + i);
                    plainBuffer += ch.toLowerCase();
                }
            }
            htmlPos += part.length;
        }
    }

    const idx = plainBuffer.indexOf(normOld);
    if (idx !== -1) {
        const startHtml = plainToHtmlMap[idx];
        const endHtmlIdx = idx + normOld.length - 1;
        const endHtml = plainToHtmlMap[endHtmlIdx] + 1;
        return content.slice(0, startHtml) + newText + content.slice(endHtml);
    }
    return content;
}
