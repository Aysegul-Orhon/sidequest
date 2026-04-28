const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api"
).replace(/\/$/, "");

export function getToken() {
  return localStorage.getItem("token") || "";
}

export function saveToken(token) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

export async function apiFetch(path, { method = "GET", body = null, token = null } = {}) {
  const headers = { "Content-Type": "application/json" };

  if (token) {
    headers["Authorization"] = `Token ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  const text = await res.text();
  let data = null;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text || "Non-JSON response from server." };
  }

  if (!res.ok) {
    const detail = data?.detail;
    if (Array.isArray(detail)) throw new Error(detail.join(" "));
    if (typeof detail === "string") throw new Error(detail);
    throw new Error(JSON.stringify(data) || "Something went wrong");
  }

  return data;
}
