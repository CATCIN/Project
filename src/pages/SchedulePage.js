import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { fetchScheduleList, deleteSchedule } from '../api/scheduleService';
import './SchedulePage.css';

function SchedulePage() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadSchedules() {
      try {
        const data = await fetchScheduleList();
        setSchedules(data);
      } catch (err) {
        setError(err.message || 'Failed to load schedules');
      } finally {
        setLoading(false);
      }
    }
    loadSchedules();
  }, []);

  const handleDelete = async (scheduleId) => {
    if (!window.confirm('이 스케줄을 정말 삭제하시겠습니까?')) return;
    try {
      await deleteSchedule(scheduleId);
      setSchedules((prev) => prev.filter((sch) => sch.id !== scheduleId));
    } catch (err) {
      alert('삭제 중 오류가 발생했습니다.');
    }
  };

  if (loading) return <p>Loading schedules…</p>;
  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

  return (
    <div className="schedule-list-page">
      <h1>Schedule List</h1>
      <p>총 {schedules.length}개의 투약 스케줄이 있습니다.</p>
      <button
        className="add-schedule-button"
        onClick={() => navigate('/catcin/schedule/new')}
      >
        Add Schedule
      </button>

      <div className="schedule-list-container">
        <div className="schedule-card schedule-header">
          <div className="schedule-item date">생성일</div>
          <div className="schedule-item medicine-name">약물명</div>
          <div className="schedule-item target">적용 대상</div>
          <div className="schedule-item interval">투약 주기(일)</div>
          <div className="schedule-item dose">투약 개수(정)</div>
          <div className="schedule-item action">삭제</div>
        </div>

        {schedules.length > 0 ? (
          schedules.map((sch) => {
            const medicineName = sch.medicine_name || (sch.medicine ? sch.medicine.name : 'N/A');
            const createdAt = sch.created_at
              ? new Date(sch.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
              : 'N/A';

            return (
              <div key={sch.id} className="schedule-card">
                <div className="schedule-item date">{createdAt}</div>
                <div className="schedule-item medicine-name">{medicineName}</div>

                <div className="schedule-item target">
                  {sch.cat_id ? (
                    <Link
                      to={`/catcin/cats/${sch.cat_id}`}
                      style={{ textDecoration: 'none', color: '#0b6' }}
                    >
                      {sch.cat_code || sch.cat_id}
                    </Link>
                  ) : (
                    '전체 적용'
                  )}
                </div>

                <div className="schedule-item interval">{sch.interval_days}</div>
                <div className="schedule-item dose">{sch.dose}</div>
                <div className="schedule-item action">
                  <button
                    className="delete-button"
                    onClick={() => handleDelete(sch.id)}
                    title="Delete"
                  >
                    ×
                  </button>
                </div>
              </div>
            );
          })
        ) : (
          <div className="no-schedules">등록된 스케줄이 없습니다.</div>
        )}
      </div>
    </div>
  );
}

export default SchedulePage;
