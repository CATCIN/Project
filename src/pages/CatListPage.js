// src/pages/CatListPage.js

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCatList, deleteCat } from '../api/catService';
import './CatListPage.css';

function CatListPage() {
  const [cats, setCats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const catsPerPage = 8;

  const navigate = useNavigate();

  useEffect(() => {
    async function loadCats() {
      try {
        const data = await fetchCatList();
        const sorted = data.sort((a, b) => new Date(b.save_at) - new Date(a.save_at));
        setCats(sorted);
      } catch (err) {
        console.error(err);
        setError(err.message || 'Unknown error');
      } finally {
        setLoading(false);
      }
    }
    loadCats();
  }, []);

  const handleDelete = async (catId) => {
    if (!window.confirm('이 고양이를 정말 삭제하시겠습니까?')) return;
    try {
      await deleteCat(catId);
      setCats((prev) => prev.filter((cat) => cat.id !== catId));
    } catch (err) {
      console.error('Failed to delete cat:', err);
      alert('삭제 중 오류가 발생했습니다.');
    }
  };

  // 페이징 계산
  const indexOfLastCat = currentPage * catsPerPage;
  const indexOfFirstCat = indexOfLastCat - catsPerPage;
  const currentCats = cats.slice(indexOfFirstCat, indexOfLastCat);
  const totalPages = Math.ceil(cats.length / catsPerPage);
  const goToPage = (pageNum) => setCurrentPage(pageNum);

  if (loading) {
    return (
      <div className="cat-list-page">
        <p>Loading cat list...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cat-list-page">
        <p style={{ color: 'red' }}>Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="cat-list-page">
      <h1>Cat List</h1>

      <div className="cat-cards-container">
        {currentCats.map((cat) => {
          const [datePart, timePart] = cat.save_at.split('T');
          const timeWithoutMs = timePart.split('.')[0];
          const formattedSaveAt = `${datePart} ${timeWithoutMs}`;
          const imageUrl = cat.image_path?.trim() || null;

          return (
            <div key={cat.id} className="cat-card">
              <div className="cat-image-wrapper">
                {imageUrl ? (
                  <img
                    className="cat-image"
                    src={imageUrl}
                    alt={cat.note || 'Cat image'}
                    onError={(e) => {
                      e.currentTarget.onerror = null;
                      e.currentTarget.src = '';
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="cat-no-image">No Image</div>
                )}
              </div>

              <div className="cat-info">
                <p className="cat-id">{cat.id}</p>
                <p className="cat-save-at">{formattedSaveAt}</p>
                <button
                  className="detail-button"
                  onClick={() => navigate(`/catcin/cats/${cat.id}`)}
                >
                  상세 보기
                </button>
              </div>

              <button
                className="delete-button"
                onClick={() => handleDelete(cat.id)}
                title="Delete"
              >
                ×
              </button>
            </div>
          );
        })}
      </div>

      <div className="pagination">
        {Array.from({ length: totalPages }, (_, i) => (
          <button
            key={i + 1}
            className={currentPage === i + 1 ? 'active' : ''}
            onClick={() => goToPage(i + 1)}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  );
}

export default CatListPage;
