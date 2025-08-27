// src/components/RecentCatsSection.js
import React from 'react';
import CatCard from './CatCard';

function RecentCatsSection() {
  // 예시 데이터: 이미지 URL(혹은 local import), 고양이 이름(여기서는 생략, 이미지만 보여주므로 생략해도 무관)
  const catImages = [
    '/images/cat1.jpg',
    '/images/cat2.jpg',
    '/images/cat3.jpg',
    '/images/cat4.jpg',
    '/images/cat5.jpg',
    '/images/cat6.jpg'
  ];

  return (
    <div className="recent-cats">
      <h2>최근투약한 고양이</h2>
      <div className="cat-grid">
        {catImages.map((imgSrc, idx) => (
          
          <CatCard key={idx} imageUrl={imgSrc} />
        ))}
      </div>
    </div>
  );
}

export default RecentCatsSection;
