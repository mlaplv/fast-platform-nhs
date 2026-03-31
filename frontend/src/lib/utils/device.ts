// Elite V2.2: Centralized Device Detection
export const MOBILE_REGEX = /Mobi|Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i;

export function isMobileDevice(userAgent: string): boolean {
    if (!userAgent) return false;
    
    const isMobileMatch = MOBILE_REGEX.test(userAgent);
    const isIPad = /iPad/i.test(userAgent);
    const isAndroidTablet = /Android/i.test(userAgent) && !/Mobi/i.test(userAgent);
    
    return isMobileMatch && !isIPad && !isAndroidTablet;
}
