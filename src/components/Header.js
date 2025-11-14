import React from 'react';
import './Header.css';
function Header() {
  return (
    <div className="header">
      <div style={{ width: '120px' }}></div>
      <div className="search-container">
        <input
          type="text"
          placeholder="Search..."
        />
      </div>
    </div>
  );
}

export default Header;
