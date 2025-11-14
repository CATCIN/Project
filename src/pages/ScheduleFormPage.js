import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { fetchMedicineList } from '../api/medicineService';
import { createSchedule } from '../api/scheduleService';
import './ScheduleFormPage.css';

function ScheduleFormPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);
  const cat_id = params.get('cat_id');

  const [medicines, setMedicines] = useState([]);
  const [loadingMeds, setLoadingMeds] = useState(true);
  const [errorMeds, setErrorMeds] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

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

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const formData = new FormData(e.target);
    if (!formData.get('medicine_id')) {
        setError('약을 선택해주세요.');
        setSubmitting(false);
        return;
    }

    try {
      await createSchedule(formData);
      navigate('/catcin/schedule'); 
    } catch (err) {
      setError(err.message || 'Failed to create schedule');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="schedule-form-page">
      <h1>{cat_id ? 'Add Cat\'s New Schedule' : 'Add New Schedule'}</h1>

      {loadingMeds ? (
        <p>Loading medicines...</p>
      ) : errorMeds ? (
        <p style={{ color: 'red' }}>Error: {errorMeds}</p>
      ) : (
        <form className="schedule-form" onSubmit={handleSubmit}>
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
          <div className="form-group">
            <label htmlFor="note">비고</label>
            <textarea
              id="note"
              name="note"
              placeholder="예: 식전 투약"
              rows="3"
            />
          </div>
          {cat_id && <input type="hidden" name="cat_id" value={cat_id} />}

          {error && <p className="error-text">{error}</p>}

          <div className="form-actions">
            <button type="submit" className="submit-button" disabled={submitting}>
              {submitting ? '생성 중...' : 'Create Schedule'}
            </button>
            <button
              type="button"
              className="cancel-button"
              onClick={() => navigate(-1)}
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