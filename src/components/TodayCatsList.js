import React, { useEffect, useState } from 'react';
import TodayCatItem from './TodayCatItem';
import { fetchCatsDueToday } from '../api/catService';
import { formatKSTDate } from '../utils/datetime';


function TodayCatsList() {
  const [cats, setCats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchCatsDueToday(3);
        setCats((data.due_today || []).map(c => ({
          ...c,
          lastDateDisplay: c.last_administered_at ? formatKSTDate(c.last_administered_at) : (c.last_administered_date || '정보 없음')
        })));
      } catch (e) {
        setError(e.message || '데이터 불러오기 실패');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="today-cats-card">불러오는 중...</div>;
  if (error) return <div className="today-cats-card">오류: {error}</div>;

  return (
    <div className="today-cats-card">
      <h3>오늘 투약 대상인 고양이</h3>
      <div className="today-cats-list">
        {cats.length > 0 ? (
          cats.map((cat, idx) => (
            <TodayCatItem
              key={idx}
              name={cat.cat_code || '이름 없음'}
              lastDate={cat.lastDateDisplay}
              thumbnail={cat.image_url || 'https://via.placeholder.com/80x80?text=No+Image'}
            />
          ))
        ) : (
          <div className="empty-text">오늘 투약 대상 고양이가 없습니다.</div>
        )}
      </div>
    </div>
  );
}

export default TodayCatsList;
