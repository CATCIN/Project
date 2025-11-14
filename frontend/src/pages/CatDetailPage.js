// src/pages/CatDetailPage.js
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchCatDetail, fetchCatSchedulesStatus } from '../api/catService';
import { fetchMedicalLogs } from '../api/mediLogService';
import { formatKST } from '../utils/datetime';
import ScheduleTable from '../components/ScheduleTable';
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
        setError(err.message || '알 수 없는 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;
  if (!cat) return <div>No cat</div>;

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
    navigate(`/catcin/schedule/new?cat_id=${cat.id}`);
  };

  return (
    <div className="cat-detail-page">
      <div className="header-actions">
        <button className="back-button" onClick={() => navigate(-1)}>
          ← Cat List
        </button>
        <button className="add-schedule-button" onClick={handleAddSchedule}>
          Add Schedule
        </button>
      </div>
      <div className="cat-top-grid">
        <div className="cat-photo-card">
          <img
            src={cat.image_url || 'https://via.placeholder.com/320x420?text=No+Image'}
            alt={cat.cat_code || 'Cat image'}
            className="cat-detail-image"
          />
        </div>
        <div className="cat-meta-card">
          <div className="cat-header">
            <h1 className="cat-title">{cat.cat_code || 'CAT_UNDEFINED'}</h1>
            <span
              className={`source-tag ${cat.source === 'user' ? 'source-user' : 'source-system'}`}
            >
              {cat.source === 'user' ? '사용자 등록' : '시스템 등록'}
            </span>
          </div>
          <div className="meta-rows">
            <p><strong>Note:</strong> {cat.note || '특이사항 없음'}</p>
            <p><strong>최초 등록일:</strong> {formatDateTime(cat.created_at)}</p>
            <p><strong>업데이트일 :</strong> {formatDateTime(cat.updated_at)}</p>
          </div>
          <div className="card-header">
            <h2>Upcoming Schedules</h2>
          </div>
          <div className="schedule-table-wrapper">
            <ScheduleTable rows={schedulesStatus} />
          </div>
        </div>
      </div>
      <div className="cat-bottom">
        <div className="card medical-history-card">
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
    </div>
  );
}

export default CatDetailPage;
