"use client";

import { useState, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

type Message = {
  role: "user" | "assistant";
  text: string;
  audioUrl?: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState("Ready — tap the mic to speak");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks to release microphone
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        await sendAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setStatus("🎙️ Listening... tap again to stop");
    } catch (err) {
      setStatus("❌ Microphone access denied. Please allow microphone access.");
      console.error("Microphone error:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus("⏳ Processing your voice...");
    }
  };

  const sendAudio = async (audioBlob: Blob) => {
    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");

      // Call the full voice conversation endpoint
      const response = await fetch(`${API_URL}/api/v1/voice/converse`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      // Get transcription and AI reply from headers (URL-encoded)
      const userText = decodeURIComponent(
        response.headers.get("X-User-Text") || "(could not transcribe)"
      );
      const aiReply = decodeURIComponent(
        response.headers.get("X-AI-Reply") || "(no response text)"
      );

      // Get audio response
      const audioResponseBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioResponseBlob);

      // Add messages to chat
      setMessages((prev) => [
        ...prev,
        { role: "user", text: userText },
        { role: "assistant", text: aiReply, audioUrl },
      ]);

      // Auto-play the response
      const audio = new Audio(audioUrl);
      audio.play().catch(() => {
        // Autoplay might be blocked by browser
        setStatus("🔊 Tap the play button to hear the response");
      });

      setStatus("Ready — tap the mic to speak");
    } catch (err) {
      setStatus(`❌ Error: ${err instanceof Error ? err.message : "Unknown error"}`);
      console.error("API error:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else if (!isProcessing) {
      startRecording();
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>🎤 AI Voice Platform</h1>
        <p style={styles.subtitle}>Speak and get AI-powered voice responses</p>
      </header>

      {/* Chat Messages */}
      <div style={styles.chatArea}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <p style={{ fontSize: "3rem", margin: 0 }}>🎙️</p>
            <p style={{ color: "#888" }}>
              Tap the microphone button below to start a conversation
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              ...styles.message,
              ...(msg.role === "user" ? styles.userMessage : styles.aiMessage),
            }}
          >
            <div style={styles.messageRole}>
              {msg.role === "user" ? "🧑 You" : "🤖 AI"}
            </div>
            <div>{msg.text}</div>
            {msg.audioUrl && (
              <audio controls src={msg.audioUrl} style={styles.audio} />
            )}
          </div>
        ))}
      </div>

      {/* Status Bar */}
      <div style={styles.statusBar}>{status}</div>

      {/* Mic Button */}
      <div style={styles.controls}>
        <button
          onClick={handleMicClick}
          disabled={isProcessing}
          style={{
            ...styles.micButton,
            ...(isRecording ? styles.micRecording : {}),
            ...(isProcessing ? styles.micDisabled : {}),
          }}
        >
          {isProcessing ? "⏳" : isRecording ? "⏹️" : "🎙️"}
        </button>
      </div>
    </div>
  );
}

// Inline styles (no CSS dependencies needed)
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    maxWidth: "600px",
    margin: "0 auto",
    backgroundColor: "#f8f9fa",
  },
  header: {
    textAlign: "center",
    padding: "1.5rem 1rem 0.5rem",
    borderBottom: "1px solid #e0e0e0",
    backgroundColor: "#fff",
  },
  title: {
    margin: 0,
    fontSize: "1.5rem",
  },
  subtitle: {
    margin: "0.25rem 0 0",
    color: "#666",
    fontSize: "0.9rem",
  },
  chatArea: {
    flex: 1,
    overflowY: "auto",
    padding: "1rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },
  emptyState: {
    textAlign: "center",
    marginTop: "4rem",
  },
  message: {
    padding: "0.75rem 1rem",
    borderRadius: "12px",
    maxWidth: "85%",
    lineHeight: 1.5,
  },
  userMessage: {
    alignSelf: "flex-end",
    backgroundColor: "#007bff",
    color: "#fff",
  },
  aiMessage: {
    alignSelf: "flex-start",
    backgroundColor: "#fff",
    border: "1px solid #e0e0e0",
  },
  messageRole: {
    fontSize: "0.75rem",
    fontWeight: "bold",
    marginBottom: "0.25rem",
    opacity: 0.8,
  },
  audio: {
    marginTop: "0.5rem",
    width: "100%",
    height: "32px",
  },
  statusBar: {
    textAlign: "center",
    padding: "0.5rem",
    fontSize: "0.85rem",
    color: "#666",
    backgroundColor: "#fff",
    borderTop: "1px solid #e0e0e0",
  },
  controls: {
    display: "flex",
    justifyContent: "center",
    padding: "1rem",
    backgroundColor: "#fff",
    borderTop: "1px solid #e0e0e0",
  },
  micButton: {
    width: "72px",
    height: "72px",
    borderRadius: "50%",
    border: "3px solid #007bff",
    backgroundColor: "#fff",
    fontSize: "2rem",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.2s ease",
  },
  micRecording: {
    backgroundColor: "#ff4444",
    borderColor: "#ff4444",
    animation: "pulse 1.5s infinite",
  },
  micDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
};
