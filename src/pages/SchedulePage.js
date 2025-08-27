// src/pages/SchedulePage.js

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  fetchScheduleList,
  deleteSchedule, // deleteSchedule 함수 임포트
} from '../api/scheduleService';
import './SchedulePage.css';

function SchedulePage() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  // 스케줄 삭제 핸들러
  const handleDelete = async (scheduleId) => {
    if (!window.confirm('이 스케줄을 정말 삭제하시겠습니까?')) {
      return;
    }

    try {
      await deleteSchedule(scheduleId);
      setSchedules((prev) => prev.filter((sch) => sch.id !== scheduleId));
    } catch (err) {
      console.error('Failed to delete schedule:', err);
      alert('삭제 중 오류가 발생했습니다.');
    }
  };

  useEffect(() => {
    async function loadSchedules() {
      try {
        const data = await fetchScheduleList();
        setSchedules(data);
      } catch (err) {
        console.error(err);
        setError(err.message || 'Failed to load schedules');
      } finally {
        setLoading(false);
      }
    }
    loadSchedules();
  }, []);

  if (loading) {
    return <p>Loading schedules…</p>;
  }
  if (error) {
    return <p style={{ color: 'red' }}>Error: {error}</p>;
  }

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

      {schedules.length === 0 ? (
        <p className="no-schedules">등록된 스케줄이 없습니다.</p>
      ) : (
        <table className="schedule-table">
          <thead>
            <tr>
              <th>생성일</th>
              <th>투약 주기(일)</th>
              <th>투약 개수(정)</th>
              <th>약물명</th>
              <th>삭제</th>
            </tr>
          </thead>
          <tbody>
            {schedules.map((sch) => {
              // created_at이 문자열이라면 'T' 기준으로 포맷
              const rawCreated = sch.created_at || '';
              let createdFormatted = 'N/A';
              if (typeof rawCreated === 'string' && rawCreated.includes('T')) {
                const [datePart, timePartWithMs] = rawCreated.split('T');
                const timeWithoutMs = timePartWithMs.split('.')[0];
                createdFormatted = `${datePart} ${timeWithoutMs}`;
              }

              return (
                <tr key={sch.id}>
                  <td>{createdFormatted}</td>
                  <td className="center-cell">{sch.interval_days}</td>
                  <td className="center-cell">{sch.dose}</td>
                  <td>{sch.medicine ? sch.medicine.name : 'N/A'}</td>
                  <td className="center-cell">
                    <button
                      className="delete-button"
                      onClick={() => handleDelete(sch.id)}
                      title="Delete"
                    >
                      ×
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default SchedulePage;
