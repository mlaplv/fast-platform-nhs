import { nanobot } from "./nanobot.svelte";
import { apiClient } from "$lib/utils/apiClient";

export class OmniController {
  cmd = $state("");
  menu = $state(false);
  wasVoice = false;
  rec = $state(false);
  exec = $state(false);
  vol = $state(0);
  liveTrans = $state("");
  isGhostSpeaking = $state(false);
  audioElement: HTMLAudioElement | null = null;
  audioUrl = $state("");
  isPlaying = $state(false);
  dText = $state("");

  private myStream: MediaStream | null = null;
  private myRec: MediaRecorder | null = null;
  private ws: WebSocket | null = null;
  private sr: any = null;
  private actx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private dataArr: Uint8Array | null = null;
  private silStart: number | null = null;
  private maxTimer: any = null;
  private animFrame: number | null = null;

  // Training-dedicated SpeechRecognition (completely separate from mic pipeline)
  private trainingSR: any = null;
  isTrainingRec = $state(false);

  orbElement: HTMLDivElement | null = null;
  private targetScale = 1;
  private currentScale = 1;

  get vuiState() {
    if (nanobot.vuiResponse) return "speaking";
    if (nanobot.nanoBotStatus === "THINKING") return "thinking";
    if (this.rec) return "listening";
    return "greeting";
  }

  get ghostAura() {
    if (this.isGhostSpeaking)
      return "radial-gradient(circle, rgba(139,92,246,0.3) 0%, transparent 70%)";
    if (this.rec)
      return "radial-gradient(circle, rgba(34,211,238,0.2) 0%, transparent 70%)";
    return "none";
  }

  constructor() {}

  initialize() {
    // RAF loop starting
    this.drawVol();
  }

  destroy() {
    this.stopRec();
    this.stopAudio();
    if (this.animFrame) cancelAnimationFrame(this.animFrame);
    this.actx?.close().catch(() => {});
  }

  private drawVol = () => {
    if (!this.analyser || !this.dataArr) {
      this.animFrame = requestAnimationFrame(this.drawVol);
      return;
    }

    this.analyser.getByteFrequencyData(this.dataArr as any);
    let avg = this.dataArr.reduce((a, b) => a + b, 0) / this.dataArr.length;

    if (this.isGhostSpeaking) avg = Math.max(avg, 40 + Math.random() * 60);

    this.vol = Math.max(0, (avg - 30) / 225);
    this.targetScale = 1 + (avg / 100) * 1.2;
    this.currentScale += (this.targetScale - this.currentScale) * 0.15;

    if (this.orbElement) {
      this.orbElement.style.transform = `scale(${this.currentScale})`;
    }

    // THE SELF-INTERRUPTION FIX: Chặn việc Xohi tự ngắt lời mình do âm lượng ảo từ hiệu ứng hào quang
    if (this.vol > 0.15 && this.isPlaying && !this.isGhostSpeaking)
      this.interrupt();

    if (this.rec) {
      if (this.vol < 0.1) {
        this.silStart = this.silStart || Date.now();
        // AUTO-CLOSE: 3s silence when VUI is active but not speaking/thinking
        if (
          nanobot.isVuiActive &&
          !this.isGhostSpeaking &&
          nanobot.nanoBotStatus !== "THINKING" &&
          Date.now() - this.silStart > 3000
        ) {
          this.stopRec();
          nanobot.resetVui();
          this.silStart = null;
        }
        // Auto-stop recording if silent for 2s (standard segmenting)
        else if (Date.now() - this.silStart > 2000) {
          this.stopRec();
          this.silStart = null;
        }
      } else this.silStart = null;
    } else if (
      nanobot.isVuiActive &&
      !this.isGhostSpeaking &&
      nanobot.nanoBotStatus !== "THINKING"
    ) {
      // Handle silence when mic is NOT active (e.g. after speaking finished)
      this.silStart = this.silStart || Date.now();
      if (Date.now() - this.silStart > 3000) {
        nanobot.resetVui();
        this.silStart = null;
      }
    } else {
      this.silStart = null;
    }
    this.animFrame = requestAnimationFrame(this.drawVol);
  };

  async startRec() {
    if (this.rec || this.exec) return;
    this.stopAudio();
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error(
          "Microphone access is not available (secure context required).",
        );
      }
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      };
      try {
        this.myStream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (e) {
        this.myStream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
      }
    } catch (e: any) {
      console.error("Mic Error:", e);
      nanobot.addLog(`Mic Fatal: ${e.name}`, "Err");
      return;
    }

    // 2026 Polish: Proactive check for STT support to prevent UI jitter
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SR && !this.ws) {
      // Only fallback if WebSocket isn't already active/connecting
      // We'll let initSpeechRecognition handle the actual logic,
      // but this pre-check helps us know if we should even continue.
    }

    this.cmd = "";
    this.wasVoice = true;
    this.liveTrans = "";
    this.dText = ""; // Clear previous response text
    nanobot.setVuiActive(true);
    nanobot.setModality("voice");
    nanobot.clearVuiResponse();

    const mime =
      ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find((t) =>
        MediaRecorder.isTypeSupported(t),
      ) || "";
    this.myRec = new MediaRecorder(this.myStream, { mimeType: mime });
    this.myRec.ondataavailable = (e) => {
      if (
        e.data.size > 0 &&
        this.ws?.readyState === WebSocket.OPEN &&
        this.vol > 0.05
      ) {
        this.ws.send(e.data);
      }
    };
    this.myRec.onstop = () => {
      nanobot.processCommand(this.liveTrans || "", "voice");
    };
    this.myRec.start(250);
    this.rec = true;

    this.initSpeechRecognition();

    if (!this.actx)
      this.actx = new (
        window.AudioContext || (window as any).webkitAudioContext
      )();
    if (this.actx.state === "suspended") await this.actx.resume();

    this.analyser = this.actx.createAnalyser();
    this.analyser.fftSize = 64;
    const source = this.actx.createMediaStreamSource(this.myStream);
    source.connect(this.analyser);
    this.dataArr = new Uint8Array(this.analyser.frequencyBinCount);

    this.maxTimer = setTimeout(() => this.rec && this.stopRec(), 30000);
  }

  private isFallbackActive = false;

  private initSpeechRecognition() {
    this.isFallbackActive = false;
    // 2026 Pipeline: WebSocket → Backend → Groq Whisper v3 (95% Vietnamese accuracy)
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProto}//${window.location.host}/ws/stt`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.info("[STT] Groq Whisper WebSocket connected");
      };

      this.ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.event === "final" && msg.text) {
            this.liveTrans = msg.text;
            this.stopRec();
          } else if (msg.event === "timeout") {
            this.stopRec();
          }
        } catch {}
      };

      this.ws.onerror = () => {
        console.warn("[STT] WebSocket failed, falling back to Web Speech API");
        this.ws = null;
        if (!this.isFallbackActive) this._initWebSpeechFallback();
      };

      this.ws.onclose = () => {
        if (this.rec && !this.liveTrans && !this.isFallbackActive) {
          this._initWebSpeechFallback();
        }
      };
    } catch {
      if (!this.isFallbackActive) this._initWebSpeechFallback();
    }
  }

  private _sttErrorState = false;

  /**
   * Fallback: Web Speech API for browsers where WebSocket STT fails.
   */
  private _initWebSpeechFallback() {
    this.isFallbackActive = true;
    try {
      const SR =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;

      if (!SR) {
        console.warn("[STT] Fallback failed: SpeechRecognition not supported.");

        // V26: SMOOTH TRANSITION — Keep modal open but set state to error/IDLE
        this._sttErrorState = true;

        const politeMsg =
          "Dạ thưa sếp, trình duyệt hiện tại chưa hỗ trợ nhận dạng giọng nói ạ. Sếp vui lòng chuyển sang Chrome hoặc Safari để em được phục vụ tốt nhất nhé.";

        setTimeout(() => {
          this.stopRec();
          nanobot.setVoiceResult("", politeMsg, "", {}, "voice");
          this.speak(politeMsg);
        }, 200);
        return;
      }

      this.sr = new SR();
      this.sr.lang = "vi-VN";
      this.sr.interimResults = true;
      this.sr.continuous = true;
      this.sr.onresult = (e: any) => {
        if (this.isGhostSpeaking) return;
        this.liveTrans = Array.from(e.results).reduce(
          (acc: string, r: any) => acc + r[0].transcript,
          "",
        );
        if (
          this.liveTrans.length > 50 ||
          (this.liveTrans.endsWith(" ") && this.liveTrans.length > 5)
        ) {
          this.stopRec();
        }
      };
      this.sr.start();
    } catch (e) {
      this.isFallbackActive = false;
    }
  }

  stopRec() {
    clearTimeout(this.maxTimer);
    this.rec = false;
    try {
      this.sr?.stop();
    } catch (e) {}
    this.sr = null;
    this.isFallbackActive = false; // Reset fallback lock
    if (this.ws) {
      // Signal backend to transcribe buffered audio before closing
      if (this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send("STOP");
        } catch {}
      }
      // Delay close to allow final transcript to arrive
      setTimeout(() => {
        try {
          this.ws?.close();
        } catch {}
        this.ws = null;
      }, 1500);
    } else {
      this.ws = null;
    }
    try {
      this.myRec?.stop();
    } catch (e) {}
    this.myStream?.getTracks().forEach((t) => t.stop());
    this.myStream = null;
    // R45: Close AudioContext to prevent RAM leak on VPS 2GB
    this.actx?.close().catch(() => {});
    this.actx = null;
    this.analyser = null;
    this.dataArr = null;
    this.vol = 0;
  }

  // ═══ TRAINING PIPELINE (Completely separate from normal mic) ═══
  startTrainingRec() {
    this.stopTrainingRec(); // Clean up any previous session
    try {
      const SR =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;
      if (!SR) {
        nanobot.addLog(
          "Trình duyệt không hỗ trợ bắt giọng nói (SpeechRecognition). Vui lòng dùng Chrome/Edge/Safari.",
          "ERR",
          "error",
        );
        alert(
          "Trình duyệt của bạn (VD: Firefox) không hỗ trợ nhận diện giọng nói gốc. Vui lòng sử dụng Google Chrome, Microsoft Edge hoặc Safari để huấn luyện dữ liệu.",
        );
        return;
      }
      this.trainingSR = new SR();
      this.trainingSR.lang = "vi-VN";
      this.trainingSR.interimResults = true;
      this.trainingSR.continuous = true;
      this.isTrainingRec = true;

      this.trainingSR.onresult = (e: any) => {
        // Update live transcript for UI preview
        const transcript = Array.from(e.results).reduce(
          (acc: string, r: any) => acc + r[0].transcript,
          "",
        );
        this.liveTrans = transcript;
        nanobot.voice.setVuiUserQuery(transcript);
      };

      this.trainingSR.onerror = (e: any) => {
        console.warn("[Training SR] Error:", e.error);
        // Auto-restart on non-fatal errors
        if (e.error !== "aborted" && nanobot.isTraining) {
          setTimeout(() => this.trainingSR?.start(), 300);
        }
      };

      this.trainingSR.onend = () => {
        // Auto-restart if still in training mode (SR times out after ~60s)
        if (nanobot.isTraining && this.isTrainingRec) {
          setTimeout(() => {
            try {
              this.trainingSR?.start();
            } catch {}
          }, 200);
        }
      };

      this.trainingSR.start();
      nanobot.addLog("Neural Capture: Mic active", "SYS");
    } catch (e: any) {
      console.error("[Training] SR init failed:", e);
      nanobot.addLog(`Training Mic Error: ${e.message}`, "ERR", "error");
    }
  }

  stopTrainingRec() {
    this.isTrainingRec = false;
    try {
      this.trainingSR?.stop();
    } catch (e) {}
    this.trainingSR = null;
    this.liveTrans = "";
  }

  playNext = async () => {
    // Native autoplay handles playback now.
  };

  interrupt() {
    this.audioUrl = "";
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.src = "";
      this.audioElement.onended = null;
      this.audioElement = null;
    }
    this.isPlaying = false;
    this.isGhostSpeaking = false;
    nanobot.setProcessingSpeech(false);
  }

  onAudioEnd() {
    this.interrupt();
    // BƯỚC 3: THE ANTI-ECHO SHIELD (Mở lại Mic sau khi phát xong)
    this.myStream?.getAudioTracks().forEach((t) => (t.enabled = true));

    // V26: Graceful close if we were just speaking an error message
    if (this._sttErrorState) {
      this._sttErrorState = false;
      nanobot.setVuiActive(false);
      return;
    }

    // RE-ENABLE MULTI-TURN: Restart recording after Xohi finishes speaking
    if (nanobot.isVuiActive) {
      this.startRec();
    }
  }

  stopAudio() {
    this.interrupt();
  }

  speak(text: string): Promise<void> {
    return new Promise((resolve) => {
      if (!text) return resolve();

      this.isPlaying = true;
      this.isGhostSpeaking = true;
      nanobot.setProcessingSpeech(true);

      // Khóa Mic KHẨN CẤP trước khi phát âm thanh
      this.myStream?.getAudioTracks().forEach((t) => (t.enabled = false));

      const ttsUrl = `/api/v1/tts/stream?text=${encodeURIComponent(text)}`;
      // VUI Speak triggered
      this.audioUrl = ttsUrl;

      if (this.audioElement) {
        this.audioElement.pause();
        this.audioElement.src = "";
      }

      const audio = new Audio(ttsUrl);
      this.audioElement = audio;

      audio.onended = () => {
        // Speech finished — trigger onAudioEnd
        this.onAudioEnd();
        resolve();
      };

      try {
        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              /* Playback OK */
            })
            .catch((e) => {
              if (e.name === "AbortError") {
                console.warn(
                  "[VUI] Playback interrupted by new speech session.",
                );
                resolve();
              } else {
                console.warn(
                  "[VUI] Audio blocked, falling back to speechSynthesis:",
                  e.name,
                );
                // Fallback: use Web Speech API when browser blocks Audio autoplay
                if (typeof speechSynthesis !== "undefined") {
                  const utt = new SpeechSynthesisUtterance(text);
                  utt.lang = "vi-VN";
                  utt.rate = 1.1;
                  utt.onend = () => {
                    this.onAudioEnd();
                    resolve();
                  };
                  utt.onerror = () => resolve();
                  speechSynthesis.speak(utt);
                } else {
                  this.onAudioEnd(); // Clean up VUI state
                  resolve();
                }
              }
            });
        } else {
          // In case play() doesn't return a promise in very old browsers
          // The onended callback will handle the resolution
        }
      } catch (err: any) {
        console.error("[VUI] Speech Setup Error:", err);
        resolve();
      }
    });
  }

  private getVisibleDataIds(): string[] {
    const ids: string[] = [];
    // Extract ID from route params (e.g. /admin/products/123)
    const pathParts = window.location.pathname.split("/");
    const lastPart = pathParts[pathParts.length - 1];
    if (lastPart && /^\d+$/.test(lastPart)) ids.push(lastPart);
    // Extract IDs from currentData if available
    const data = nanobot.currentData;
    if (data) {
      if (data.id) ids.push(String(data.id));
      if (Array.isArray(data.items)) {
        for (const item of data.items) {
          if (item && typeof item === "object" && "id" in item)
            ids.push(String(item.id));
        }
      }
    }
    return [...new Set(ids)];
  }

  async processGhost(text: string, source: "text" | "voice" = "voice") {
    // Note: We bypass this.exec check here because wrappers like execCmd or startRec might manage it.
    // Instead, we rely on nanobot.nanoBotStatus or the caller's lock.
    nanobot.setThinking(true);
    this.interrupt();
    try {
      const payload = {
        query: text || "",
        modality: source,
        session_id: localStorage.getItem("chat_session_id"),
        screen_context: {
          current_route: window.location.pathname,
          active_widget: nanobot.activeWidget,
          visible_data_ids: this.getVisibleDataIds(),
        },
        system_context: {
          domain: window.location.hostname,
          role: window.location.hostname.includes("admin") ? "E-commerce ERP Admin Dashboard" : "E-commerce Storefront",
          database_schema: [
            "User (Tài khoản, Khách hàng, Admin)",
            "Product (Sản phẩm, Hàng hóa, Tồn kho)",
            "Category (Danh mục sản phẩm)",
            "Order (Đơn hàng, Doanh thu, Doanh số, Giao dịch)",
            "News (Tin tức, Bài viết, Blog)",
            "Notification (Thông báo hệ thống)",
          ],
        },
      };

      // ═══ SSE STREAMING — Real-time phased response ═══
      const r = await this._fetchSSE(payload);

      // ═══ KIỂM TRA LỖI TỪ BACKEND (HTTP 200 NHƯNG CÓ LỖI) ═══
      if (r.status === "error") {
        const errorText =
          r.message || "Lõi nhận thức đang gián đoạn. Sếp thử lại sau ạ.";
        this.dText = errorText;
        nanobot.setVoiceResult(text, errorText, "", {}, source);
        if (source === "voice") await this.speak(errorText);
        return;
      }

      const replyText = r.message || r.reply_text || "Hệ thống đang xử lý.";
      const uiAction = (r.data && r.data.ui_action) || r.ui_action || "";
      const actionData = r.data || {};
      const requiresConfirmation = r.requires_confirmation === true;
      const isRestricted = actionData.restricted === true;

      // ═══ SKILL GUARD: Professional capability-disabled message ═══
      if (isRestricted) {
        const ACTION_VI: Record<string, string> = {
          READ: "Phân tích Dữ liệu",
          MUTATE: "Thay đổi Hệ thống",
          ANALYZE: "Suy luận Chuyên sâu",
        };
        const actionName = (actionData.action as string) || "";
        const viName = ACTION_VI[actionName] || actionName;
        const restrictedMsg = `Dạ, năng lực "${viName}" đang tạm khóa trong Ma trận Nhận thức. Sếp bật lại trong Cài đặt Giọng nói → Cognitive Capability Matrix để em hỗ trợ ạ.`;
        this.dText = restrictedMsg;
        nanobot.setVoiceResult(text, restrictedMsg, "", actionData, source);
        if (source === "voice") await this.speak(restrictedMsg);
        return;
      }

      this.dText = replyText;

      // V21.0 SAFETY NET: Smart Mini-Forms for MUTATE
      if (requiresConfirmation) {
        const target = (actionData.target as string) || "";
        const verb = (actionData.verb as string) || "create";
        const entities = (actionData.entities as Record<string, string>) || {};

        // 🚀 2026 PARADIGM: Bypass Modal for News Management
        if (target === "news") {
          this.dText =
            "Dạ em đã mở khu vực soạn thảo Bài Viết 2026 cho Sếp rồi ạ.";
          nanobot.setVoiceResult(
            text,
            this.dText,
            "show_news_management",
            { ...actionData, intent_type: "MUTATE" },
            source,
          );
          if (source === "voice") await this.speak(this.dText);
          return;
        }

        // Import schema + executor lazily
        const { getMutationSchema } =
          await import("$lib/utils/mutationSchemas");
        const { executeMutation } = await import("$lib/utils/mutationExecutor");

        const schema = await getMutationSchema(target, verb, entities);

        if (schema && schema.fields.length > 0) {
          // ═══ SMART FORM: multi-field form ═══
          const formData = await nanobot.showConfirm({
            title: schema.title,
            message: schema.message,
            confirmLabel: schema.confirmLabel,
            cancelLabel: "HỦY",
            fields: schema.fields,
          });

          if (!formData || typeof formData !== "object") {
            nanobot.setVoiceResult(text, "Đã hủy thao tác.", "", {}, source);
            return;
          }

          // Execute the mutation
          nanobot.addLog("Đang thực thi thao tác...", "SYS");
          const result = await executeMutation(
            target,
            verb,
            formData as Record<string, string>,
            entities.id,
          );

          this.dText = result.message;
          nanobot.setVoiceResult(
            text,
            result.message,
            "",
            result.data || {},
            source,
          );
          if (source === "voice") await this.speak(result.message);

          if (result.success) {
            nanobot.showToast(result.message, "success");
          } else {
            nanobot.showToast(result.message, "error");
          }
          return;
        } else if (schema && schema.fields.length === 0) {
          // ═══ DELETE CONFIRM: Yes/No only ═══
          const confirmed = await nanobot.showConfirm({
            title: schema.title,
            message: schema.message,
            confirmLabel: schema.confirmLabel,
            cancelLabel: "HỦY",
          });

          if (!confirmed) {
            nanobot.setVoiceResult(text, "Đã hủy thao tác.", "", {}, source);
            return;
          }

          nanobot.addLog("Đang thực thi thao tác...", "SYS");
          const result = await executeMutation(target, verb, {}, entities.id);

          this.dText = result.message;
          nanobot.setVoiceResult(
            text,
            result.message,
            "",
            result.data || {},
            source,
          );
          if (source === "voice") await this.speak(result.message);

          nanobot.showToast(
            result.message,
            result.success ? "success" : "error",
          );
          return;
        } else {
          // ═══ FALLBACK: generic confirmation (unknown target) ═══
          const confirmed = await nanobot.showConfirm({
            title: "⚠️ XÁC NHẬN THAO TÁC",
            message: replyText,
            confirmLabel: "XÁC NHẬN",
            cancelLabel: "HỦY",
          });

          if (!confirmed) {
            nanobot.setVoiceResult(text, "Đã hủy thao tác.", "", {}, source);
            return;
          }
        }
      }

      nanobot.setVoiceResult(
        text,
        replyText,
        uiAction,
        actionData,
        source,
        r.router_tier,
      );

      // ═══ SESSION CONTROL ACTIONS ═══
      let isSleeping = false;
      if (actionData.category === "SESSION_CTRL") {
        if (actionData.action === "HARDWARE_SLEEP") {
          // V58.2: Set flag and disable VUI immediately to prevent mic restart,
          // but WAIT for the speech to finish before releasing the hardware lock.
          isSleeping = true;
          nanobot.voice.setVuiActive(false);
        } else if (actionData.action === "WAKE_ROUTINE") {
          // Wake routine is already handled by setVoiceResult and speak
        }
      }

      if (source === "voice") {
        await this.speak(replyText);
      }

      if (isSleeping) {
        nanobot.voice.hard_sleep();
      }
    } catch (e: any) {
      // ═══ PROFESSIONAL ERROR CATEGORIZATION ═══
      const status = e?.status || e?.response?.status;
      const errMsg = e?.message || "";
      let errorText: string;

      if (
        errMsg.includes("Failed to fetch") ||
        errMsg.includes("NetworkError") ||
        errMsg.includes("ECONNREFUSED")
      ) {
        errorText =
          "Dạ, kết nối đến Trinity Core đang gián đoạn. Sếp kiểm tra kết nối mạng hoặc thử lại sau ạ.";
      } else if (status === 403) {
        errorText =
          "Dạ, yêu cầu đã bị chặn bởi Semantic Shield. Sếp thử diễn đạt lại ạ.";
      } else if (status === 402) {
        errorText =
          "Dạ, ngân sách LLM hôm nay đã hết. Hệ thống sẽ hoạt động lại vào ngày mai ạ.";
      } else if (status === 429) {
        errorText = "Dạ, hệ thống đang quá tải. Sếp thử lại sau vài giây ạ.";
      } else if (status >= 500) {
        errorText = "Dạ, hệ thống đang gặp lỗi nội bộ. Sếp thử lại sau ạ.";
      } else {
        errorText =
          "Dạ, Trinity Core đang tạm gián đoạn xử lý. Sếp thử lại sau ạ.";
      }

      console.error("[Xohi] processGhost error:", {
        status,
        errMsg,
        fullError: e,
        data: e?.data,
      });
      this.dText = errorText;
      nanobot.setVoiceResult(text, errorText, "", {});
      if (source === "voice") await this.speak(errorText);
    } finally {
      // exec flag is cleared by the caller (execCmd/startRec) or finally block here if not using wrapper
    }
  }

  /**
   * SSE Streaming — fetch /api/v1/intent/stream and read events.
   * Shows real-time progress, falls back to old endpoint on failure.
   */
  private async _fetchSSE(payload: Record<string, any>): Promise<any> {
    try {
      const resp = await fetch("/api/v1/intent/stream", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "x-tenant":
            typeof window !== "undefined"
              ? (() => {
                  const parts = window.location.hostname.split(".");
                  const sys = new Set(["admin", "api", "www", "portal"]);
                  const rel = parts.filter((p) => !sys.has(p));
                  return rel[0] || "default";
                })()
              : "default",
        },
        body: JSON.stringify(payload),
      });

      if (!resp.ok || !resp.body) {
        // Fallback to old endpoint
        return await apiClient.post<any>("/api/v1/intent/", payload);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalResponse: any = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));

            if (event.phase === "classify" && event.status === "thinking") {
              this.dText = "Đang phân tích...";
            } else if (event.phase === "classify" && event.status === "done") {
              const tierLabel =
                event.tier === "1"
                  ? "T1 Heuristic"
                  : event.tier === "2"
                    ? "T2 LLM"
                    : `T${event.tier}`;
              this.dText = `Phân tích xong (${tierLabel})...`;
            } else if (event.phase === "execute") {
              this.dText = "Đang lấy dữ liệu...";
            } else if (event.phase === "error") {
              finalResponse = {
                status: "error",
                message: event.message,
                data: { restricted: event.restricted, action: event.action },
              };
            } else if (event.phase === "done") {
              finalResponse = {
                status: event.status,
                message: event.message,
                data: event.data,
                ui_action: event.ui_action,
                router_tier: event.router_tier,
                cost_tokens: event.cost_tokens,
                requires_confirmation: event.requires_confirmation,
              };
            }
          } catch {
            // Ignore malformed SSE lines
          }
        }
      }

      if (finalResponse) return finalResponse;

      // If stream ended without 'done', fallback
      return await apiClient.post<any>("/api/v1/intent/", payload);
    } catch (e) {
      // SSE failed entirely — fallback to standard endpoint
      console.warn("[SSE] Streaming failed, falling back:", e);
      return await apiClient.post<any>("/api/v1/intent/", payload);
    }
  }

  async toggleVoice() {
    this.rec ? this.stopRec() : await this.startRec();
  }

  async execCmd() {
    if (
      !this.cmd.trim() ||
      this.exec ||
      ["THINKING", "PROCESSING"].includes(nanobot.nanoBotStatus)
    )
      return;
    const c = this.cmd;
    this.cmd = "";
    this.exec = true;
    const wv = this.wasVoice;
    this.wasVoice = false;
    nanobot.setModality("text");
    try {
      await nanobot.processCommand(c, "text");
    } finally {
      this.exec = false;
    }
  }
}

export const omni = new OmniController();
