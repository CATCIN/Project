// src/pages/MedicineListPage.js

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchMedicineList, deleteMedicine } from '../api/medicineService';
import './MedicineListPage.css';

const API_BASE = (process.env.REACT_APP_API_BASE || "").replace(/\/+$/, "");

function MedicineListPage() {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadMedicines() {
      try {
        const data = await fetchMedicineList();
        setMedicines(data);
      } catch (err) {
        console.error(err);
        setError(err.message || 'Unknown error');
      } finally {
        setLoading(false);
      }
    }
    loadMedicines();
  }, []);

  // 삭제 버튼 클릭 시 호출되는 함수
  const handleDelete = async (medicineId) => {
    if (!window.confirm('정말 이 약물을 삭제하시겠습니까?')) {
      return;
    }

    try {
      await deleteMedicine(medicineId);
      setMedicines((prev) => prev.filter((m) => m.id !== medicineId));
    } catch (err) {
      console.error('Failed to delete medicine:', err);
      alert('삭제 중 오류가 발생했습니다.');
    }
  };

  if (loading) {
    return (
      <div className="medicine-list-page">
        <p>Loading medicines...</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="medicine-list-page">
        <p style={{ color: 'red' }}>Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="medicine-list-page">
      <h1>Medicine List</h1>
      <button
        className="add-medicine-button"
        onClick={() => navigate('/catcin/medicine/new')}
      >
        Add Medicine
      </button>

      <div className="medicine-cards-container">
        {medicines.map((med) => (
          <div key={med.id} className="medicine-card">
            {/* 1) 오른쪽 상단에 삭제(X) 버튼 추가 */}
            <button
              className="delete-button"
              onClick={() => handleDelete(med.id)}
              title="Delete"
            >
              ×
            </button>

            <div className="medicine-image-wrapper">
              {med.image_url ? (
                <img
                  className="medicine-image"
                  src={`${API_BASE}${med.image_url}`}
                  alt={med.name}
                />
              ) : (
                <div className="medicine-no-image">No Image</div>
              )}
            </div>

            <div className="medicine-info">
              <h2 className="medicine-name">{med.name}</h2>
              <p className="medicine-category">종 류: {med.category}</p>
              <p className="medicine-interval">
                복용 주기: {med.interval} 일
              </p>
              <p className="medicine-expires">
                유효 기간: {new Date(med.expires_date).toLocaleDateString('ko-KR')}
              </p>
              {med.note && <p className="medicine-note">비고: {med.note}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MedicineListPage;
