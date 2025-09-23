const API_BASE = (process.env.REACT_APP_API_BASE || "").replace(/\/+$/, "");

const API_URL = `${API_BASE}/catcin/cats`;

export async function fetchCatList() {
  const res = await fetch(API_URL);
  if (!res.ok) {
    throw new Error(`Failed to fetch cat list: ${res.status}`);
  }
  const data = await res.json();
  return data;
}

export async function fetchCatDetail(catId) {
  const res = await fetch(`${API_URL}/${catId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch cat detail (id=${catId}): ${res.status}`);
  }
  const data = await res.json();
  return data;
}

export async function registerCatManual(formData) {
  const url = `${API_BASE}/catcin/register-manual`; 
  
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to register cat manually: ${res.status} ${text}`);
  }
  return await res.json();
}

export async function createCat(formData) {
  const res = await fetch(API_URL, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to create medicine: ${res.status} ${text}`);
  }
  return await res.json();

}

export async function deleteCat(catId) {
  const url = `${API_URL}/${catId}`;
  const res = await fetch(url, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to delete cat: ${res.status} ${text}`);
  }
  return;
}

export async function fetchCatSchedulesStatus(catId) {
  const url = `${API_URL}/${catId}/schedules`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch schedules status: ${res.status}`);
  }
  return await res.json();
}