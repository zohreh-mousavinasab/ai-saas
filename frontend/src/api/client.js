import axios from "axios";

const defaultBackendBaseUrl = "http://127.0.0.1:8000";
const chatTimeout = Number(import.meta.env.VITE_CHAT_TIMEOUT_MS ?? 240000);
const uploadTimeout = Number(import.meta.env.VITE_UPLOAD_TIMEOUT_MS ?? 240000);
const modelChatTimeout = Number(import.meta.env.VITE_MODEL_CHAT_TIMEOUT_MS ?? 300000);

const apiBaseCandidates = Array.from(
  new Set(
    [
      import.meta.env.DEV ? "/api" : null,
      import.meta.env.VITE_API_BASE_URL?.trim(),
      defaultBackendBaseUrl,
      "http://localhost:8000",
    ].filter(Boolean),
  ),
);

let resolvedBaseUrlPromise;

async function resolveBaseURL() {
  if (!resolvedBaseUrlPromise) {
    resolvedBaseUrlPromise = (async () => {
      const probeTimeout = 2000;

      for (const baseURL of apiBaseCandidates) {
        try {
          const response = await axios.get("/health", {
            baseURL,
            timeout: probeTimeout,
            validateStatus: (status) => status >= 200 && status < 500,
          });

          if (response.status === 200 && response.data?.status === "ok") {
            return baseURL;
          }
        } catch {
          continue;
        }
      }

      const error = new Error(
        `Could not reach the backend at any configured base URL: ${apiBaseCandidates.join(", ")}`,
      );
      error.code = "BACKEND_UNREACHABLE";
      error.candidates = apiBaseCandidates;
      throw error;
    })();
  }

  return resolvedBaseUrlPromise;
}

async function requestApi(method, url, options = {}) {
  const baseURL = await resolveBaseURL();
  return axios.request({
    baseURL,
    method,
    url,
    timeout: options.timeout ?? 30000,
    headers: options.headers,
    data: options.data,
  });
}

function extractApiErrorDetail(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object") {
          return item.msg ?? item.message ?? item.detail ?? "";
        }
        return "";
      })
      .filter(Boolean)
      .join(" ");
  }
  return "";
}

export function formatApiError(error, fallbackMessage) {
  if (error?.code === "ECONNABORTED") {
    return "Request timed out. The backend may still be processing a large file or waiting on Ollama.";
  }

  if (!error?.response) {
    if (error?.code === "BACKEND_UNREACHABLE") {
      return [
        "Could not reach the backend.",
        `Tried: ${error.candidates?.join(", ") ?? "unknown"}.`,
        "Start FastAPI with `uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` and refresh the page.",
      ].join(" ");
    }

    if (error?.message && error.message !== "Network Error") {
      return `${error.message} ${fallbackMessage}`;
    }

    return [
      fallbackMessage,
      "Check that FastAPI is running on port 8000 and that `frontend/.env` still has `VITE_API_BASE_URL=/api`.",
    ].join(" ");
  }

  const status = error.response.status;
  const requestId = error.response.data?.request_id ?? error.response.headers?.["x-request-id"];
  const detail = extractApiErrorDetail(error);

  const parts = [];
  if (detail) parts.push(detail);
  else parts.push(fallbackMessage);
  parts.push(`HTTP ${status}`);
  if (requestId) parts.push(`request ${requestId}`);

  return parts.join(" | ");
}

export async function getHealth() {
  const response = await requestApi("get", "/health");
  return response.data;
}

export async function getDocuments() {
  const response = await requestApi("get", "/documents");
  return response.data;
}

export async function uploadDocuments(files) {
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append("files", file));

  const response = await requestApi("post", "/upload", {
    data: formData,
    headers: { "Content-Type": "multipart/form-data" },
    timeout: uploadTimeout,
  });
  return response.data;
}

export async function sendChatMessage({ question, documentIds, sessionId, topK = 5 }) {
  const response = await requestApi("post", "/chat", {
    data: {
      question,
      document_ids: documentIds?.length ? documentIds : null,
      session_id: sessionId ?? null,
      top_k: topK,
    },
    timeout: chatTimeout,
  });
  return response.data;
}

export async function sendModelChatMessage(messages) {
  const response = await requestApi("post", "/model-chat", {
    data: { messages },
    timeout: modelChatTimeout,
  });
  return response.data;
}

export async function getChatSessions() {
  const response = await requestApi("get", "/chat/sessions");
  return response.data;
}
