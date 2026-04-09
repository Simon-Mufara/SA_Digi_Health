const API_BASE = "http://127.0.0.1:8000/api/v1";
const TOKEN_KEY = "access_token";
const ROLE_KEY = "assigned_role";

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  window.location.href = "./login.html";
}

async function api(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}), Authorization: `Bearer ${token}` };
  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!resp.ok) {
    const payload = await resp.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${resp.status}`);
  }
  return resp;
}

async function verifyAuthOrRedirect(expectedRole) {
  const token = getToken();
  if (!token) {
    window.location.href = "./login.html";
    return null;
  }
  try {
    const resp = await api("/auth/verify", { method: "GET" });
    const data = await resp.json();
    if (!data.role || (expectedRole && data.role !== expectedRole)) {
      logout();
      return null;
    }
    localStorage.setItem(ROLE_KEY, data.role);
    return data;
  } catch {
    logout();
    return null;
  }
}

function wireHeader(roleLabel) {
  document.getElementById("roleBadge").textContent = roleLabel;
  document.getElementById("logoutBtn").addEventListener("click", logout);
}

function exportCsv(filename, rows) {
  const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const content = rows.map((r) => r.map(esc).join(",")).join("\n");
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function roleToPage(role) {
  const map = {
    doctor: "./doctor.html",
    clinician: "./clinician.html",
    admin: "./admin.html",
    security_officer: "./security.html",
    researcher: "./researcher.html",
  };
  return map[role] || "./login.html";
}

window.RolePortal = { api, verifyAuthOrRedirect, wireHeader, exportCsv, roleToPage, TOKEN_KEY, ROLE_KEY };
