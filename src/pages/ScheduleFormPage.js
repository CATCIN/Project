// src/pages/ScheduleFormPage.js

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchMedicineList } from '../api/medicineService';
import { createSchedule } from '../api/scheduleService';
import './ScheduleFormPage.css';

function ScheduleFormPage() {
  const navigate = useNavigate();

  // 1) 약 목록 상태
  const [medicines, setMedicines] = useState([]);
  const [loadingMeds, setLoadingMeds] = useState(true);
  const [errorMeds, setErrorMeds] = useState(null);

  // 2) 폼 상태
  const [medicineId, setMedicineId] = useState('');
  const [intervalDays, setIntervalDays] = useState(1);
  const [dose, setDose] = useState(1);
  const [note, setNote] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // 3) 약 목록 불러오기
  useEffect(() => {
    async function loadMeds() {
      try {
        const data = await fetchMedicineList();
        setMedicines(data);
      } catch (err) {
        console.error(err);
        setErrorMeds(err.message || 'Failed to load medicines');
      } finally {
        setLoadingMeds(false);
      }
    }
    loadMeds();
  }, []);

  // 4) 폼 제출 핸들러
  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // 필수값 검사
    if (!medicineId || !intervalDays || !dose) {
      setError('Medicine, Interval, Dose 필수 입력 항목입니다.');
      setSubmitting(false);
      return;
    }

    const formData = new FormData();
    formData.append('medicine_id', medicineId);
    formData.append('interval_days', intervalDays.toString());
    formData.append('dose', dose.toString());
    formData.append('note', note);

    try {
      await createSchedule(formData);
      navigate('/schedules');
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to create schedule');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="schedule-form-page">
      <h1>Add New Schedule</h1>

      {loadingMeds ? (
        <p>Loading medicines...</p>
      ) : errorMeds ? (
        <p style={{ color: 'red' }}>Error: {errorMeds}</p>
      ) : (
        <form className="schedule-form" onSubmit={handleSubmit}>
          {/* Medicine 선택 */}
          <div className="form-group">
            <label htmlFor="medicineId">Medicine*</label>
            <select
              id="medicineId"
              value={medicineId}
              required
              onChange={(e) => setMedicineId(e.target.value)}
            >
              <option value="">-- Select Medicine --</option>
              {medicines.map((med) => (
                <option key={med.id} value={med.id}>
                  {med.name} ({med.category})
                </option>
              ))}
            </select>
          </div>

          {/* Interval (days) */}
          <div className="form-group">
            <label htmlFor="intervalDays">Interval (days)*</label>
            <input
              id="intervalDays"
              type="number"
              min="1"
              value={intervalDays}
              required
              onChange={(e) =>
                setIntervalDays(parseInt(e.target.value, 10) || 1)
              }
            />
          </div>

          {/* Dose */}
          <div className="form-group">
            <label htmlFor="dose">Dose*</label>
            <input
              id="dose"
              type="number"
              min="1"
              value={dose}
              required
              onChange={(e) => setDose(parseInt(e.target.value, 10) || 1)}
            />
          </div>

          {/* Note (선택) */}
          <div className="form-group">
            <label htmlFor="note">Note</label>
            <textarea
              id="note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="예: 식전 투약"
              rows="3"
            />
          </div>

          {/* 에러 메시지 */}
          {error && <p className="error-text">{error}</p>}

          {/* 제출 및 취소 버튼 */}
          <button
            type="submit"
            className="submit-button"
            disabled={submitting}
          >
            {submitting ? 'Submitting...' : 'Create Schedule'}
          </button>
          <button
            type="button"
            className="cancel-button"
            onClick={() => navigate('/catcin/schedules')}
            disabled={submitting}
          >
            Cancel
          </button>
        </form>
      )}
    </div>
  );
}

export default ScheduleFormPage;
