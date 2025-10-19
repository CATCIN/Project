// src/pages/CatDetailPage.js
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchCatDetail } from '../api/catService';
import { fetchMedicalLogs } from '../api/mediLogService';
import { fetchCatSchedulesStatus } from '../api/catService';
import './CatDetailPage.css';

function CatDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [cat, setCat] = useState(null);
  const [logs, setLogs] = useState([]);
  const [schedulesStatus, setSchedulesStatus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [catData, mediLogData, schedulesData] = await Promise.all([
          fetchCatDetail(id),
          fetchMedicalLogs(id),
          fetchCatSchedulesStatus(id)
        ]);
        setCat(catData);
        setLogs(mediLogData.logs || []);
        setSchedulesStatus(schedulesData.medications_status || []);
      } catch (err) {
        console.error("데이터 로딩 오류:", err);
        setError(err.message || '알 수 없는 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  if (loading) return <div className="cat-detail-page"><p>로딩 중...</p></div>;
  if (error) return <div className="cat-detail-page"><p style={{ color: 'red' }}>오류: {error}</p></div>;
  if (!cat) return <div className="cat-detail-page"><p>고양이를 찾을 수 없습니다.</p></div>;

  const formatDateTime = (isoString) => {
    if (!isoString || isoString === "정보 없음") return "정보 없음";
    if (isoString === "즉시 가능") return "즉시 가능";
    const date = new Date(isoString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true
    });
  };

  const handleAddSchedule = () => {
    navigate(`/schedule/add?cat_id=${id}`);
  };

  return (
    <div className="cat-detail-page">
      <div className="header-actions">
        <button className="back-button" onClick={() => navigate(-1)}>
          ← Cat List
        </button>
        <button
  className="add-schedule-button"
  onClick={() => navigate(`/catcin/schedule/new?cat_id=${cat.id}`)}
>
  Add Schedule
</button>
      </div>
      
      <div className="cat-info-card">
        <img
          src={cat.image_url || 'https://via.placeholder.com/200?text=No+Image'}
          alt={cat.cat_code || 'Cat image'}
          className="cat-detail-image"
        />
        <div className="cat-basic-info">
          <div className="cat-header">
            <h1 style={{ display: 'inline-block', marginRight: 10 }}>
              {cat.cat_code || 'CAT_UNDEFINED'}
            </h1>
            <span
              className={`source-tag ${cat.source === 'user' ? 'source-user' : 'source-system'}`}
              style={{ verticalAlign: 'middle' }}
            >
              {cat.source === 'user' ? '사용자 등록' : '시스템 등록'}
            </span>
            </div>
            <p><strong>Note:</strong> {cat.note || '특이사항 없음'}</p>
            <p><strong>최초 등록일:</strong> {formatDateTime(cat.created_at)}</p>
            <p><strong>마지막 업데이트:</strong> {formatDateTime(cat.updated_at)}</p>
        </div>
        <div className="additional-info-box upcoming-schedules-container">
          <h2>Upcoming Schedules</h2>
          <div className="schedule-table-wrapper"> 
          <table className="schedule-table">
            <thead>
              <tr>
                <th>약 이름</th>
                <th>종류</th>
                <th>투약 주기</th>
                <th>용량</th>
                <th>다음 투약일</th>
              </tr>
            </thead>
            <tbody>
              {schedulesStatus.length > 0 ? (
                schedulesStatus.map((schedule, idx) => (
                  <tr key={schedule.schedule_id || idx}>
                    <td>{schedule.medicine_name || '정보 없음'}</td>
                    <td>{schedule.medicine_category || '미분류'}</td>
                    <td>{schedule.interval_days}일</td>
                    <td>{schedule.dose}알</td>
                    <td>{formatDateTime(schedule.next_due_date)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5">등록된 투약 스케줄이 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div> 
        </div>
      </div>
    
      <div className="medical-history">
        <h2>Medical History</h2>
        <table className="medical-history-table">
          <thead>
            <tr>
              <th>Administered At</th>
              <th>Medicine Name</th>
              <th>Category</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {logs.length > 0 ? (
              logs.map((entry) => (
                <tr key={entry.id}>
                  <td>{formatDateTime(entry.administered_at)}</td>
                  <td>{entry.medicine_name || '알 수 없음'}</td>
                  <td>{entry.medicine_category || '미분류'}</td>
                  <td>{entry.note || '메모 없음'}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4">투약 기록이 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default CatDetailPage;