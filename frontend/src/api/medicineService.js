const API_BASE = (process.env.REACT_APP_API_BASE || "").replace(/\/+$/, "");

const API_URL = `${API_BASE}/catcin/medicines`;

export async function fetchMedicineList() {
  const res = await fetch(API_URL);
  if (!res.ok) {
    throw new Error(`Failed to fetch medicines: ${res.status}`);
  }
  return await res.json();
}

export async function createMedicine(formData) {
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

export async function deleteMedicine(medicineId) {
  const url = `${API_URL}/${medicineId}`;
  const res = await fetch(url, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to delete medicine: ${res.status} ${text}`);
  }
  
  
  return;
}
