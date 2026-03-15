export class WebSocketStream {
  private ws: WebSocket | null = null;
  private endpointPath: string;

  constructor(endpointPath: string) {
    this.endpointPath = endpointPath;
  }

  private getEndpoint(): string {
    if (typeof window === 'undefined') return this.endpointPath;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}${this.endpointPath}`;
  }

  /**
   * Mở cầu WebSocket /ws/stt
   */
  connect(
    onMessage: (data: Record<string, unknown>) => void,
    onOpen?: () => void,
    onClose?: () => void,
    onError?: (err: Event) => void
  ): Promise<void> {
    this.disconnect(); // Đảm bảo đóng kết nối cũ
    
    return new Promise((resolve, reject) => {
      try {
        if (typeof window === 'undefined') {
          resolve();
          return;
        }
        this.ws = new WebSocket(this.getEndpoint());

        this.ws.onopen = () => {
          onOpen?.();
          resolve();
        };

        this.ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            onMessage(data);
          } catch (err) {
            console.error("[WS] Parse error", err);
          }
        };

        this.ws.onerror = (e) => {
          onError?.(e);
          reject(e);
        };

        this.ws.onclose = () => {
          onClose?.();
        };

      } catch (err) {
        reject(err);
      }
    });
  }

  /**
   * Góp chunk âm thanh WebM gửi lên Server
   */
  sendBinary(chunk: Blob) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      if (chunk.size > 0) {
        console.debug(`[WS] Sending binary chunk: ${chunk.size} bytes`);
        this.ws.send(chunk);
      }
    } else if (this.ws) {
      console.warn(`[WS] Cannot send chunk, state: ${this.ws.readyState}`);
    }
  }

  /**
   * Lệnh Text "STOP" báo Server rằng người dùng đã nói xong -> Xử lý AI
   */
  sendStopSignal() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send("STOP");
      } catch (e) {
        console.error("[WS] Failed to send STOP signal", e);
      }
    } else {
      console.warn(`[WS] Cannot send STOP, state: ${this.ws?.readyState}`);
    }
  }

  /**
   * Hủy diệt WebSocket tức thì (Singleton-safe)
   */
  disconnect() {
    if (this.ws) {
      const ref = this.ws;
      this.ws = null;
      try {
        if (ref.readyState === WebSocket.OPEN || ref.readyState === WebSocket.CONNECTING) {
          ref.close();
        }
      } catch (e) {}
    }
  }
}
