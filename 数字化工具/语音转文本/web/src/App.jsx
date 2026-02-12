import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [srt, setSrt] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [provider, setProvider] = useState("local");
  const [apiKey, setApiKey] = useState("");
  const [endpointId, setEndpointId] = useState("");

  const [serverStatus, setServerStatus] = useState({
    openai: false,
    groq: false,
  });
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/status")
      .then((res) => res.json())
      .then((data) => setServerStatus(data))
      .catch((err) => console.error("Failed to fetch server status", err));
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setStatus("");
      setSrt("");
      setUploadProgress(0);
    }
  };

  const handleUpload = () => {
    if (!file) return;

    setLoading(true);
    setStatus("准备上传...");
    setUploadProgress(0);

    // Generate a unique task ID for progress tracking
    const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("provider", provider);
    formData.append("api_key", apiKey);
    formData.append("model", endpointId); // Send endpointId as 'model' for VolcArk compatibility
    formData.append("task_id", taskId);

    const xhr = new XMLHttpRequest();
    let progressInterval = null;

    // Start polling for backend progress
    const startPolling = () => {
      progressInterval = setInterval(() => {
        fetch(`http://localhost:8000/progress/${taskId}`)
          .then((res) => res.json())
          .then((data) => {
            if (data && data.status !== "waiting") {
              setStatus(data.status);
              // Only update progress bar if the backend reported something meaningful
              if (data.percent > 0) {
                setUploadProgress(data.percent);
              }
            }
          })
          .catch((err) => console.error("Progress fetch error:", err));
      }, 2000);
    };

    // Track upload progress (client to server)
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded * 100) / e.total);
        // During upload, keep it between 0-99 to leave room for processing progress
        const displayPercent = Math.min(percent, 99);
        setUploadProgress(displayPercent);
        if (percent === 100) {
          setStatus("文件已送达服务器，正在启动处理流程...");
          startPolling();
        } else {
          setStatus(`正在上传文件: ${percent}%`);
        }
      }
    });

    xhr.addEventListener("load", () => {
      if (progressInterval) clearInterval(progressInterval);

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          setSrt(data.srt);
          setStatus("转写完成!");
          setUploadProgress(100);

          // Show rate limit info if available
          if (
            data.rate_limits &&
            data.rate_limits["x-ratelimit-remaining-audio-seconds"]
          ) {
            const secondsLeft = parseFloat(
              data.rate_limits["x-ratelimit-remaining-audio-seconds"],
            );
            if (!isNaN(secondsLeft)) {
              const minsLeft = Math.floor(secondsLeft / 60);
              setStatus(`转写完成! 本小时 API 剩余额度: 约 ${minsLeft} 分钟`);
            }
          }
        } catch (e) {
          setStatus("解析响应失败");
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText);
          let errMsg = errorData.error || "请求失败";

          if (
            xhr.status === 429 ||
            errMsg.includes("429") ||
            errMsg.includes("Rate limit")
          ) {
            errMsg =
              "API 频率限制：当前免费额度已用完（每小时有时长限制）。请等待几分钟再试，或切换到 [本地 Whisper] 模式。";
          } else if (
            (xhr.status === 400 || xhr.status === 500) &&
            errMsg.includes("response_format")
          ) {
            errMsg = "API 参数错误：该服务商不支持此格式。已尝试修正，请重试。";
          }

          setStatus(`错误: ${errMsg}`);
        } catch (e) {
          setStatus(`错误: HTTP ${xhr.status}`);
        }
      }

      setLoading(false);
    });

    xhr.addEventListener("error", () => {
      if (progressInterval) clearInterval(progressInterval);
      setStatus("网络请求错误");
      setLoading(false);
    });

    xhr.open("POST", "http://localhost:8000/transcribe");
    xhr.send(formData);
  };

  const downloadSrt = () => {
    const element = document.createElement("a");
    const file = new Blob([srt], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = "subtitle.srt";
    document.body.appendChild(element);
    element.click();
  };

  const fetchLogs = () => {
    fetch("http://localhost:8000/logs")
      .then((res) => res.json())
      .then((data) => {
        setLogs(data.logs);
        setShowLogs(true);
      })
      .catch((err) => alert("获取日志失败"));
  };

  const clearLogs = () => {
    if (window.confirm("确定要清空后台日志吗？")) {
      fetch("http://localhost:8000/logs/clear", { method: "POST" }).then(() =>
        fetchLogs(),
      );
    }
  };

  return (
    <div
      className="container"
      style={{ maxWidth: "800px", margin: "0 auto", padding: "2rem" }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <h1 style={{ margin: 0 }}>AI 语音转字幕 (SRT)</h1>
        <button
          onClick={fetchLogs}
          style={{
            padding: "8px 15px",
            backgroundColor: "#6c757d",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "14px",
          }}
        >
          查看实时日志
        </button>
      </div>

      <div
        style={{
          marginBottom: "2rem",
          border: "1px solid #ddd",
          padding: "1.5rem",
          borderRadius: "12px",
          textAlign: "center",
          backgroundColor: "#fff",
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
        }}
      >
        <h3 style={{ marginTop: 0 }}>1. 选择服务商</h3>
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          style={{
            padding: "10px",
            width: "100%",
            maxWidth: "400px",
            marginBottom: "15px",
            borderRadius: "6px",
            border: "1px solid #ccc",
          }}
        >
          <option value="openai">OpenAI Whisper (收费，精准，$0.006/分)</option>
          <option value="groq">Groq (免费/极速，需 API Key)</option>
          <option value="volcengine">火山引擎 (火山方舟/豆包，需 EP ID)</option>
          <option value="local">
            本地 Whisper (免费，无需联网，依赖本机 CPU/GPU)
          </option>
        </select>

        {(provider === "openai" ||
          provider === "groq" ||
          provider === "volcengine") && (
          <div
            style={{
              marginTop: "10px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <input
              type="password"
              placeholder={`请输入 ${provider === "openai" ? "OpenAI" : provider === "groq" ? "Groq" : "火山引擎"} API Key`}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={{
                padding: "10px",
                width: "100%",
                maxWidth: "400px",
                borderRadius: "6px",
                border: "1px solid #ccc",
                boxSizing: "border-box",
              }}
            />
            {provider === "volcengine" && (
              <input
                type="text"
                placeholder="请输入 Endpoint ID (推理终端 ID)"
                value={endpointId}
                onChange={(e) => setEndpointId(e.target.value)}
                style={{
                  padding: "10px",
                  width: "100%",
                  maxWidth: "400px",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                  boxSizing: "border-box",
                }}
              />
            )}
            {provider === "groq" && serverStatus.groq && !apiKey && (
              <p
                style={{
                  color: "green",
                  fontSize: "0.85em",
                  marginTop: "8px",
                  fontWeight: "500",
                }}
              >
                ✅ 检测到服务器已配置 Groq Key，可留空直接使用。
              </p>
            )}
          </div>
        )}

        {provider === "local" && (
          <p
            style={{
              fontSize: "0.9em",
              color: "#666",
              backgroundColor: "#f9f9f9",
              padding: "10px",
              borderRadius: "6px",
              borderLeft: "4px solid #007bff",
              maxWidth: "600px",
              margin: "10px auto 0",
            }}
          >
            提示：本地模式首次运行需要下载模型文件，且转写速度取决于您的电脑性能
            (M 系列芯片较快)。
          </p>
        )}
      </div>

      <div
        className="upload-box"
        style={{
          marginBottom: "2rem",
          border: "2px dashed #007bff",
          padding: "2.5rem",
          borderRadius: "12px",
          backgroundColor: "#f0f7ff",
          transition: "all 0.3s ease",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        <h3 style={{ marginTop: 0 }}>2. 上传音视频文件</h3>
        <input
          type="file"
          onChange={handleFileChange}
          accept="audio/*,video/*"
          style={{
            marginBottom: "1rem",
            marginLeft: "auto",
            marginRight: "auto",
            display: "block",
            cursor: "pointer",
          }}
        />
        <p style={{ marginTop: "0.5rem", color: "#666", fontSize: "0.9em" }}>
          支持 MP3, WAV, MP4, MKV 等格式。大文件自动进行切片转写。
        </p>
      </div>

      <div style={{ marginBottom: "2rem" }}>
        <button
          onClick={handleUpload}
          disabled={!file || loading}
          style={{
            padding: "12px 40px",
            fontSize: "18px",
            fontWeight: "bold",
            cursor: loading ? "not-allowed" : "pointer",
            backgroundColor: loading ? "#ccc" : "#007bff",
            color: "white",
            border: "none",
            borderRadius: "50px",
            boxShadow: "0 4px 12px rgba(0,123,255,0.3)",
            transition: "transform 0.2s",
          }}
          onMouseDown={(e) => (e.target.style.transform = "scale(0.95)")}
          onMouseUp={(e) => (e.target.style.transform = "scale(1)")}
        >
          {loading ? "处理中..." : "开始转写"}
        </button>

        {loading && (
          <div style={{ marginTop: "20px", textAlign: "center" }}>
            <div
              style={{
                width: "100%",
                height: "10px",
                backgroundColor: "#eee",
                borderRadius: "5px",
                overflow: "hidden",
                marginBottom: "10px",
              }}
            >
              <div
                style={{
                  width: `${uploadProgress}%`,
                  height: "100%",
                  backgroundColor: "#007bff",
                  transition: "width 0.3s ease",
                }}
              ></div>
            </div>
            <p style={{ color: "#007bff", fontWeight: "bold" }}>{status}</p>
          </div>
        )}

        {!loading && status && (
          <p
            style={{
              marginTop: "1rem",
              fontWeight: "bold",
              color: status.startsWith("错误") ? "red" : "green",
            }}
          >
            {status}
          </p>
        )}
      </div>

      {srt && (
        <div
          style={{
            marginTop: "2rem",
            textAlign: "left",
            animation: "fadeIn 0.5s",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "10px",
            }}
          >
            <h3 style={{ margin: 0 }}>结果预览:</h3>
            <button
              onClick={downloadSrt}
              style={{
                padding: "8px 15px",
                backgroundColor: "#28a745",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              下载 .srt 文件
            </button>
          </div>
          <textarea
            value={srt}
            onChange={(e) => setSrt(e.target.value)}
            rows={15}
            style={{
              width: "100%",
              padding: "15px",
              fontSize: "14px",
              fontFamily: "'Courier New', Courier, monospace",
              borderRadius: "8px",
              border: "1px solid #ddd",
              backgroundColor: "#f8f9fa",
              boxSizing: "border-box",
            }}
          />
        </div>
      )}

      {/* 日志弹窗 */}
      {showLogs && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: "20px",
              borderRadius: "12px",
              width: "80%",
              maxWidth: "1000px",
              maxHeight: "80vh",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "15px",
              }}
            >
              <h3 style={{ margin: 0 }}>后台实时日志 (最后100行)</h3>
              <div>
                <button
                  onClick={clearLogs}
                  style={{
                    marginRight: "10px",
                    padding: "5px 10px",
                    backgroundColor: "#dc3545",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                  }}
                >
                  清空日志
                </button>
                <button
                  onClick={() => setShowLogs(false)}
                  style={{ padding: "5px 10px", cursor: "pointer" }}
                >
                  关闭
                </button>
              </div>
            </div>
            <pre
              style={{
                flex: 1,
                overflowY: "auto",
                backgroundColor: "#1e1e1e",
                color: "#d4d4d4",
                padding: "15px",
                borderRadius: "6px",
                fontFamily: "monospace",
                fontSize: "12px",
                textAlign: "left",
                whiteSpace: "pre-wrap",
              }}
            >
              {logs}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
