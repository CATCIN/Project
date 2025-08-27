// src/pages/CatDetailPage.js
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchCatDetail } from '../api/catService';
import { fetchMedicalLogs } from '../api/mediLogService';
import './CatDetailPage.css';

function CatDetailPage() {
  const { id } = useParams();       // URL 파라미터에서 id를 꺼냄 (문자열)
  const navigate = useNavigate();

  const [cat, setCat] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loadingCat, setLoadingCat] = useState(true);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [errorCat, setErrorCat] = useState(null);
  const [, setErrorLogs] = useState(null);


  useEffect(() => {
    async function loadCatDetail() {
      try {
        const data = await fetchCatDetail(id);
        setCat(data);
      } catch (err) {
        console.error(err);
        setErrorCat(err.message || 'Unknown error');
      } finally {
        setLoadingCat(false);
      }
    }
    loadCatDetail();
  }, [id]);

  useEffect(() => {
    async function loadLogs() {
      try {
        const data = await fetchMedicalLogs(id);
        setLogs(data.logs || []);
      } catch (err) {
        console.error(err);
        setErrorLogs(err.message || 'Unknown error');
      } finally {
        setLoadingLogs(false);
      }
    }
    loadLogs();
  }, [id]);
 if (loadingCat) {
    return (
      <div className="cat-detail-page">
        <p>Loading cat detail...</p>
      </div>
    );
  }
  if (errorCat) {
    return (
      <div className="cat-detail-page">
        <p style={{ color: 'red' }}>Error loading cat: {errorCat}</p>
        <button onClick={() => navigate(-1)}>뒤로 가기</button>
      </div>
    );
  }
  if (!cat) {
    return (
      <div className="cat-detail-page">
        <p>Cat not found.</p>
        <button onClick={() => navigate(-1)}>뒤로 가기</button>
      </div>
    );
  }

  return (
    <div className="cat-detail-page">
      <button className="back-button" onClick={() => navigate(-1)}>
        ← 고양이 리스트로
      </button>
      <div className="cat-info-card">
        {/* 상단 이미지 */}
          <img
            src={cat.image_path}
            alt={cat.note || 'Cat image'}
            onError={(e) => {
              e.currentTarget.onerror = null;
              e.currentTarget.src = ''; // 또는 placeholder
              e.currentTarget.style.display = 'none';
            }}
            className="cat-detail-image"
          />

        {/* 상단 기본 정보 */}
        <div className="cat-basic-info">
          <h1>{cat.id}</h1>
          <h2>{cat.name}</h2>
          <p>source: {cat.source}</p>
          <p>note: {cat.note}</p>
          <p>Last Visit: {cat && cat.save_at ? cat.save_at.split('T')[0] + ' ' + cat.save_at.split('T')[1].split('.')[0] : '정보 없음'}</p>
        </div>
      </div>

      {/* 의료 기록(투약 로그) 섹션 */}
      <div className="medical-history">
        <h2>Medical History</h2>

        {loadingLogs ? (
          <p>Loading medical logs...</p>
        ) : (
          <table className="medical-history-table">
            <thead>
              <tr>
                <th>Administered At</th>
                <th>Medicine ID</th>
                <th>Note</th>
                {/* 추후 API가 medicine_type 필드를 추가하면 여기에 
                    <th>Medicine Type</th> 같은 칼럼을 추가할 수 있습니다. */}
              </tr>
            </thead>
            <tbody>
              {logs.map((entry, idx) => {
                const [datePart, timePart] = entry.administered_at.split('T');
                const timeWithoutMs = timePart.split('.')[0];
                const formattedAt = `${datePart} ${timeWithoutMs}`;

                return (
                  <tr key={entry.medicine_id + '_' + idx}>
                    <td>{formattedAt}</td>
                    <td>{entry.medicine_id}</td>
                    <td>{entry.note}</td>
                    {/* 추후:
                        <td>{entry.medicine_type}</td>
                    */}
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default CatDetailPage;
