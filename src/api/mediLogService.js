// src/api/medicalLogService.js
const API_BASE = (process.env.REACT_APP_API_BASE || "").replace(/\/+$/, "");

const API_URL = `${API_BASE}/catcin/mediLogs`;

export async function fetchMedicalLogs(catId) {
  const res = await fetch(`${API_URL}/${catId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch medical logs: ${res.status}`);
  }
  return await res.json();
}

export async function createMedicalLog(formData) {
  const res = await fetch(API_URL, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to create medical log: ${res.status} ${text}`);
  }
  return await res.json();
}

export async function deleteMedicalLog(logId) {
  const url = `${API_URL}/${logId}`;
  const res = await fetch(url, { method: 'DELETE' });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to delete medical log: ${res.status} ${text}`);
  }
  return;
}
