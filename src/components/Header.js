// src/components/Header.js
import React from 'react';

function Header() {
  return (
    <div className="header">
      {/* 로고를 대체하는 빈 공간(왼쪽에 로고가 사이드바에 이미 있기 때문에 빈 칸으로 두거나 추가 UI 배치) */}
      <div style={{ width: '120px' }}></div>

      {/* 검색창 */}
      <div className="search-container">
        <input
          type="text"
          placeholder="Search..."
        />
      </div>

      {/* 우측 프로필 드롭다운(일단 버튼만 만들어 두겠습니다.)
      <div className="profile-btn">
        Admin ▼
      </div>
      */}
    </div>
  );
}

export default Header;
