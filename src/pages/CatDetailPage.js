import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchCatDetail } from '../api/catService';
import { fetchMedicalLogs } from '../api/mediLogService';
import './CatDetailPage.css';

function CatDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [cat, setCat] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        // 고양이 상세 정보와 의료 기록을 동시에 가져옵니다.
        const [catData, mediLogData] = await Promise.all([
          fetchCatDetail(id),
          fetchMedicalLogs(id)
        ]);
        setCat(catData);
        setLogs(mediLogData.logs || []);
      } catch (err) {
        console.error("데이터 로딩 오류:", err);
        setError(err.message || 'Unknown error');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  if (loading) return <div className="cat-detail-page"><p>Loading details...</p></div>;
  if (error) return <div className="cat-detail-page"><p style={{ color: 'red' }}>Error: {error}</p></div>;
  if (!cat) return <div className="cat-detail-page"><p>Cat not found.</p></div>;

  // 날짜 포맷팅 함수
  const formatDateTime = (isoString) => {
    if (!isoString) return "정보 없음";
    const date = new Date(isoString);
    return date.toLocaleString('ko-KR');
  };

  return (
    <div className="cat-detail-page">
      <button className="back-button" onClick={() => navigate(-1)}>
        ← 고양이 리스트로
      </button>
      
      <div className="cat-info-card">
        <img
          src={cat.image_url || ''}
          alt={cat.note || 'Cat image'}
          className="cat-detail-image"
        />
        <div className="cat-basic-info">
          <h1>{cat.cat_code || cat.id}</h1>
          <p><strong>Source:</strong> {cat.source}</p>
          <p><strong>Note:</strong> {cat.note}</p>
          {/* --- 수정된 부분: 'save_at' 대신 'updated_at' 사용 --- */}
          <p><strong>최초 등록일:</strong> {formatDateTime(cat.created_at)}</p>
          <p><strong>마지막 업데이트:</strong> {formatDateTime(cat.updated_at)}</p>
        </div>
      </div>

      <div className="medical-history">
        <h2>Medical History</h2>
        <table className="medical-history-table">
          <thead>
            <tr>
              <th>Administered At</th>
              <th>Medicine ID</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {logs.length > 0 ? (
              logs.map((entry, idx) => (
                <tr key={entry.medicine_id + '_' + idx}>
                  <td>{formatDateTime(entry.administered_at)}</td>
                  <td>{entry.medicine_id}</td>
                  <td>{entry.note}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3">투약 기록이 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default CatDetailPage;
