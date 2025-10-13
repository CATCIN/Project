// src/pages/SchedulePage.js

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchScheduleList, deleteSchedule } from '../api/scheduleService';
import './SchedulePage.css';

function SchedulePage() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

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

  if (loading) return <p>Loading schedules…</p>;
  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

  return (
    <div className="schedule-list-page">
      <h1>Schedule List</h1>
      <p>총 {schedules.length}개의 투약 스케줄이 있습니다.</p>
      <button
        className="add-schedule-button"
        onClick={() => navigate('/schedule/add')} // 경로 수정
      >
        Add Schedule
      </button>

      <table className="schedule-table">
        <thead>
          <tr>
            <th>생성일</th>
            <th>약물명</th>
            <th>적용 대상</th>
            <th>투약 주기(일)</th>
            <th>투약 개수(정)</th>
            <th>삭제</th>
          </tr>
        </thead>
        <tbody>
          {schedules.length > 0 ? (
            schedules.map((sch) => {
              // 백엔드 데이터 구조가 달라도 안전하게 약물명을 찾습니다.
              const medicineName = sch.medicine_name || (sch.medicine ? sch.medicine.name : 'N/A');
              
              // 날짜 포맷을 간단하고 안전하게 변경합니다.
              const createdAt = sch.created_at 
                ? new Date(sch.created_at).toLocaleString('ko-KR') 
                : 'N/A';

              return (
                <tr key={sch.id}>
                  <td>{createdAt}</td>
                  <td>{medicineName}</td>
                  <td>{sch.cat_code || '전체 적용'}</td>
                  <td className="center-cell">{sch.interval_days}</td>
                  <td className="center-cell">{sch.dose}</td>
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
            })
          ) : (
            <tr>
              <td colSpan="6" style={{ textAlign: 'center' }}>
                등록된 스케줄이 없습니다.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default SchedulePage;