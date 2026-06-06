import { dev } from "$app/environment";

// Central logger to govern client-side diagnostic outputs.
// Rules:
// 1. Info / Debug / Log: Completely silent in production. In development, only printed if enabled (via localStorage flag).
// 2. Warn / Error: Always logged in development. In production, logged using a professional, sanitized format that protects PII/raw details but provides system context.
class SecureLogger {
  // Can be enabled locally via localStorage 'osmo:logger:debug' for active debugging in dev
  private isEnabled(): boolean {
    if (!dev) return false;
    if (typeof window !== "undefined") {
      try {
        return localStorage.getItem("osmo:logger:debug") === "true";
      } catch (e) {
        return false;
      }
    }
    return false;
  }

  public log(message: any, ...optionalParams: any[]) {
    if (this.isEnabled()) {
      console.log(message, ...optionalParams);
    }
  }

  public debug(message: any, ...optionalParams: any[]) {
    if (this.isEnabled()) {
      console.debug(message, ...optionalParams);
    }
  }

  /**
   * Warn: System indicators that need developer/admin attention.
   * In Dev: Always print.
   * In Prod: Print with sanitized prefix, stripping any potential payload data.
   */
  public warn(message: any, ...optionalParams: any[]) {
    if (dev) {
      console.warn(message, ...optionalParams);
    } else {
      // Production: Clean, sanitized warnings only showing structure
      const sanitizedMsg = this.sanitizeMessage(message);
      console.warn(`[System Warning] ${sanitizedMsg}`);
    }
  }

  /**
   * Error: Critical execution failure.
   * In Dev: Always print full details.
   * In Prod: Print clean system message and sanitized context to support operation monitoring.
   */
  public error(message: any, ...optionalParams: any[]) {
    if (dev) {
      console.error(message, ...optionalParams);
    } else {
      // Production: Professional logical error presentation
      const sanitizedMsg = this.sanitizeMessage(message);
      
      // Extract basic error summary (status codes or error types) from optionalParams
      let summary = "";
      if (optionalParams && optionalParams.length > 0) {
        const firstParam = optionalParams[0];
        if (firstParam instanceof Error) {
          summary = ` (${firstParam.name})`;
        } else if (typeof firstParam === "object" && firstParam !== null) {
          // If it's an API error response, extract status code/type safely without leaking response data
          if ("status" in firstParam) {
            summary = ` (Status: ${firstParam.status})`;
          } else if ("code" in firstParam) {
            summary = ` (Code: ${firstParam.code})`;
          }
        }
      }
      
      console.error(`[System Error] ${sanitizedMsg}${summary}`);
    }
  }

  /**
   * Helper to ensure no sensitive raw text (tokens, user names, phone numbers) are outputted.
   * Replaces common PII formats or structures.
   */
  private sanitizeMessage(msg: any): string {
    if (typeof msg !== "string") {
      try {
        return JSON.stringify(msg).substring(0, 100);
      } catch (e) {
        return "[Non-serializable Object]";
      }
    }

    // Mask phone numbers (e.g. 09xxxxxxxx, +84xxxxxxx)
    let sanitized = msg.replace(/(?:\+84|0[3|5|7|8|9])([0-9]{8})\b/g, "$1******");
    
    // Mask tokens / Bearer auth
    sanitized = sanitized.replace(/Bearer\s+[a-zA-Z0-9_\-\.]+/gi, "Bearer [MASKED]");
    
    // Shorten long error dumps
    if (sanitized.length > 200) {
      sanitized = sanitized.substring(0, 200) + "...";
    }
    
    return sanitized;
  }
}

export const logger = new SecureLogger();
