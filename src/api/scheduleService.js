// src/api/scheduleService.js

const API_BASE = (process.env.REACT_APP_API_BASE || "").replace(/\/+$/, "");

const API_URL = `${API_BASE}/catcin/mediSchedules`;

export async function fetchScheduleList() {
  const res = await fetch(API_URL, {
    method: 'GET',
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch schedules: ${res.status}`);
  }
  return await res.json();
}

export async function createSchedule(formData) {
  const res = await fetch(API_URL, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to create schedule: ${res.status} ${text}`);
  }
  return await res.json(); 
}

export async function deleteSchedule(scheduleId) {
  const url = `${API_URL}/${scheduleId}`;
  const res = await fetch(url, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to delete schedule: ${res.status} ${text}`);
  }
  return;
}
