const params = new URLSearchParams(window.location.search);

const backendUrlInput = document.getElementById("backendUrl");
const backendModeInput = document.getElementById("backendMode");
const uploadFileInput = document.getElementById("uploadFile");
const form = document.getElementById("ocrForm");
const message = document.getElementById("message");
const markdownOutput = document.getElementById("markdownOutput");
const jsonOutput = document.getElementById("jsonOutput");
const healthText = document.getElementById("healthText");
const backendText = document.getElementById("backendText");
const submitButton = document.getElementById("submitButton");

backendUrlInput.value = params.get("backend") || "http://127.0.0.1:5050";
backendText.textContent = backendUrlInput.value;

backendUrlInput.addEventListener("input", async () => {
  backendText.textContent = backendUrlInput.value || "未设置";
  await checkHealth();
});

async function checkHealth() {
  const baseUrl = backendUrlInput.value.trim().replace(/\/$/, "");
  if (!baseUrl) {
    healthText.textContent = "未配置";
    return;
  }

  try {
    const response = await fetch(`${baseUrl}/api/health`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    healthText.textContent = payload.backend || "已连接";
  } catch (error) {
    healthText.textContent = "连接失败";
  }
}

function setMessage(text, isError = false) {
  message.textContent = text;
  message.style.color = isError ? "#b42318" : "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const baseUrl = backendUrlInput.value.trim().replace(/\/$/, "");
  const file = uploadFileInput.files?.[0];

  if (!baseUrl) {
    setMessage("请先填写后端地址。", true);
    return;
  }

  if (!file) {
    setMessage("请先选择一个文件。", true);
    return;
  }

  const body = new FormData();
  body.append("file", file);
  if (backendModeInput.value) {
    body.append("backend_mode", backendModeInput.value);
  }

  submitButton.disabled = true;
  setMessage("正在识别，请稍候...");
  markdownOutput.textContent = "处理中...";
  jsonOutput.textContent = "处理中...";

  try {
    const response = await fetch(`${baseUrl}/api/ocr`, {
      method: "POST",
      body,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "OCR 请求失败");
    }

    const firstResult = payload.results?.[0];
    markdownOutput.textContent =
      firstResult?.markdown || "未返回 Markdown 结果。";
    jsonOutput.textContent = JSON.stringify(firstResult?.json || payload, null, 2);
    setMessage(`识别完成：${payload.filename}`);
  } catch (error) {
    markdownOutput.textContent = "请求失败";
    jsonOutput.textContent = JSON.stringify(
      { error: error.message || "Unknown error" },
      null,
      2
    );
    setMessage(`识别失败：${error.message || "未知错误"}`, true);
  } finally {
    submitButton.disabled = false;
  }
});

checkHealth();
