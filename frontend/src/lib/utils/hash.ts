/**
 * Generates a stable 8-character hex hash for error identification.
 * Elite V2.2: Deterministic error hashing (No Mock Data).
 */
export function generateErrorHash(status: number, message: string): string {
    const input = `${status}-${message}-${new Date().toISOString().slice(0, 13)}`; // Hour-stable
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
        const char = input.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash |= 0; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16).padStart(8, '0').slice(0, 8).toUpperCase();
}
