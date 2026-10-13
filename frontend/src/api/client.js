const API_BASE = import.meta.env.VITE_API_BASE || "";

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof URLSearchParams ? {} : { "Content-Type": "application/json" }),
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = "Request failed";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch (_) {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function login(email, password) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  return request("/api/auth/login", {
    method: "POST",
    body,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
}

export const me = () => request("/api/auth/me");
export const getStats = () => request("/api/applications/stats");
export const listApplications = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return request(`/api/applications${q ? `?${q}` : ""}`);
};
export const getApplication = (id) => request(`/api/applications/${id}`);
export const createApplication = (payload) =>
  request("/api/applications", { method: "POST", body: JSON.stringify(payload) });
export const decideApplication = (id, payload) =>
  request(`/api/applications/${id}/decision`, { method: "PATCH", body: JSON.stringify(payload) });
export const rescoreApplication = (id) =>
  request(`/api/applications/${id}/rescore`, { method: "POST" });
