import { useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [srt, setSrt] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setStatus("");
      setSrt("");
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setStatus(
      "Uploading and Processing... (This may take a while for large files)",
    );

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Upload failed");
      }

      const data = await response.json();
      setSrt(data.srt);
      setStatus("Transcription Complete!");
    } catch (error) {
      console.error(error);
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadSrt = () => {
    const element = document.createElement("a");
    const file = new Blob([srt], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = "subtitle.srt";
    document.body.appendChild(element);
    element.click();
  };

  return (
    <div
      className="container"
      style={{ maxWidth: "800px", margin: "0 auto", padding: "2rem" }}
    >
      <h1>AI 语音转字幕 (SRT)</h1>
      <div
        style={{
          marginBottom: "2rem",
          border: "2px dashed #ccc",
          padding: "2rem",
          borderRadius: "8px",
        }}
      >
        <input
          type="file"
          onChange={handleFileChange}
          accept="audio/*,video/*"
        />
        <p style={{ marginTop: "1rem", color: "#666" }}>
          支持 MP3, WAV, MP4, MKV 等格式。大文件自动处理。
        </p>
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        style={{
          padding: "10px 20px",
          fontSize: "16px",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "处理中..." : "开始转写"}
      </button>

      {status && (
        <p style={{ marginTop: "1rem", fontWeight: "bold" }}>{status}</p>
      )}

      {srt && (
        <div style={{ marginTop: "2rem" }}>
          <h3>结果预览:</h3>
          <textarea
            value={srt}
            onChange={(e) => setSrt(e.target.value)}
            rows={20}
            style={{
              width: "100%",
              padding: "10px",
              fontSize: "14px",
              fontFamily: "monospace",
            }}
          />
          <br />
          <button
            onClick={downloadSrt}
            style={{ marginTop: "10px", padding: "10px" }}
          >
            下载 .srt 文件
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
