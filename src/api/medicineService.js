// src/api/medicineService.js
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
    // 브라우저가 자동으로 multipart/form-data; boundary=… 헤더를 붙여줍니다.
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
  // 삭제 성공 시 보통 204 No Content 혹은 200 OK를 반환하므로,
  // 특별히 데이터를 리턴할 필요가 없다면 그냥 return;
  return;
}
