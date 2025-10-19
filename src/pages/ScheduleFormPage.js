// src/pages/ScheduleFormPage.js (이 파일 하나만 사용합니다)
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { fetchMedicineList } from '../api/medicineService';
import { createSchedule } from '../api/scheduleService';
import './ScheduleFormPage.css';

function ScheduleFormPage() {
  const location = useLocation();
  const navigate = useNavigate();

  // URL 쿼리 파라미터에서 cat_id를 가져옵니다. 없으면 null이 됩니다.
  const params = new URLSearchParams(location.search);
  const cat_id = params.get('cat_id');

  const [medicines, setMedicines] = useState([]);
  const [loadingMeds, setLoadingMeds] = useState(true);
  const [errorMeds, setErrorMeds] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // 약 목록 불러오기
  useEffect(() => {
    async function loadMeds() {
      try {
        const data = await fetchMedicineList();
        setMedicines(data);
      } catch (err) {
        setErrorMeds(err.message || 'Failed to load medicines');
      } finally {
        setLoadingMeds(false);
      }
    }
    loadMeds();
  }, []);

  // 폼 제출 핸들러 (개선됨)
  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // FormData가 form 요소의 모든 필드(숨겨진 cat_id 포함)를 자동으로 수집합니다.
    const formData = new FormData(e.target);
    
    // FormData의 medicine_id가 비어있는지 직접 확인
    if (!formData.get('medicine_id')) {
        setError('약을 선택해주세요.');
        setSubmitting(false);
        return;
    }

    try {
      await createSchedule(formData);
      // 성공 후 스케줄 목록 페이지로 이동
      navigate('/catcin/schedule'); 
    } catch (err) {
      setError(err.message || 'Failed to create schedule');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="schedule-form-page">
      {/* cat_id 존재 여부에 따라 제목을 동적으로 변경 */}
      <h1>{cat_id ? 'Add Cat\'s New Schedule' : 'Add New Schedule'}</h1>

      {loadingMeds ? (
        <p>Loading medicines...</p>
      ) : errorMeds ? (
        <p style={{ color: 'red' }}>Error: {errorMeds}</p>
      ) : (
        <form className="schedule-form" onSubmit={handleSubmit}>
          {/* 약 선택 (name 속성 추가) */}
          <div className="form-group">
            <label htmlFor="medicine_id">약*</label>
            <select id="medicine_id" name="medicine_id" required>
              <option value="">-- 약을 선택하세요 --</option>
              {medicines.map((med) => (
                <option key={med.id} value={med.id}>
                  {med.name} ({med.category})
                </option>
              ))}
            </select>
          </div>

          {/* 투약 주기 (name 속성 추가) */}
          <div className="form-group">
            <label htmlFor="interval_days">투약 주기(일)*</label>
            <input
              id="interval_days"
              name="interval_days"
              type="number"
              min="1"
              defaultValue="1"
              required
            />
          </div>

          {/* 용량 (name 속성 추가) */}
          <div className="form-group">
            <label htmlFor="dose">용량(알)*</label>
            <input
              id="dose"
              name="dose"
              type="number"
              min="1"
              defaultValue="1"
              required
            />
          </div>

          {/* 비고 (name 속성 추가) */}
          <div className="form-group">
            <label htmlFor="note">비고</label>
            <textarea
              id="note"
              name="note"
              placeholder="예: 식전 투약"
              rows="3"
            />
          </div>

          {/* cat_id가 URL에 존재할 때만 이 숨겨진 input을 렌더링합니다. */}
          {cat_id && <input type="hidden" name="cat_id" value={cat_id} />}

          {error && <p className="error-text">{error}</p>}

          <div className="form-actions">
            <button type="submit" className="submit-button" disabled={submitting}>
              {submitting ? '생성 중...' : 'Create Schedule'}
            </button>
            <button
              type="button"
              className="cancel-button"
              onClick={() => navigate(-1)} // 간단하게 이전 페이지로 이동
              disabled={submitting}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default ScheduleFormPage;