const BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  login: (police_id, password) => request("/auth/login", { method: "POST", body: JSON.stringify({ police_id, password }) }),
  listCases: () => request("/cases/"),
  listSuspects: (case_id) => request(`/suspects/?case_id=${case_id}`),
  getSuspect: (id) => request(`/suspects/${id}`),
  deleteSuspect: (id) => request(`/suspects/${id}`, { method: "DELETE" }),
  addSuspectWithPhotos: async (fields, photoFiles) => {
    const form = new FormData();
    Object.entries(fields).forEach(([k, v]) => { if (v) form.append(k, v); });
    photoFiles.forEach((file) => form.append("photos", file));
    const res = await fetch(`${BASE_URL}/suspects/with-photos`, { method: "POST", body: form });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed: ${res.status}`);
    }
    return res.json();
  },
  searchByPhoto: async (file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE_URL}/suspects/search-photo`, { method: "POST", body: form });
    return res.json();
  },
  getGraph: (case_id) => request(`/graph/${case_id}`),
  listAlerts: (status) => request(`/alerts/${status ? `?status=${status}` : ""}`),
  updateAlert: (id, status) => request(`/alerts/${id}?status=${status}`, { method: "PATCH" }),
  simulateTransaction: (payload = {}) => request("/transactions/simulate", { method: "POST", body: JSON.stringify(payload) }),
};

export const WS_URL = "ws://localhost:8000/ws";