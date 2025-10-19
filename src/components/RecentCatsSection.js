import React, { useState, useEffect } from 'react';
// 1. react-router-dom에서 Link를 가져옵니다.
import { Link } from 'react-router-dom'; 
import CatCard from './CatCard';

function RecentCatsSection() {
  const [cats, setCats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCats = async () => {
      try {
        const response = await fetch('http://localhost:8000/catcin/cats/recent');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setCats(data); 
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCats();
  }, []);

  if (loading) {
    return <div>고양이 목록을 불러오는 중...</div>;
  }

  if (error) {
    return <div>에러: {error}</div>;
  }

  return (
    <div className="recent-cats">
      <h2>최근 인식된 고양이</h2>
      <div className="cat-grid">
        {cats.map((cat) => (
          <Link to={`/catcin/cats/${cat.id}`} key={cat.id} style={{ textDecoration: 'none', color: 'inherit' }}>
            <CatCard imageUrl={cat.image_url} name={cat.cat_code}/>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default RecentCatsSection;