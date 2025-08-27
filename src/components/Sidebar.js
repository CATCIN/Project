import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css'; 

function Sidebar() {
  
  const menuItems = [
    { name: 'Main',       label: 'Main',         path: '/catcin' },
    { name: 'CatList',    label: 'Cat List',     path: '/catcin/cats' },
    { name: 'MedicineList', label: 'Medicine List', path: '/catcin/medicine' },
    { name: 'Schedule',   label: 'Schedule',     path: '/catcin/schedule' }
  ];

  const otherItems = [
    { name: 'Settings', label: 'Settings', path: '/catcin/settings' },
    { name: 'Help',     label: 'Help',     path: '/catcin/help' }
  ];
  
  return (
    <div className="sidebar">
      {/* 로고 영역 */}
      <div className="logo">
        <NavLink
          to="/"
          className="logo-link"
        >
          🐱 CatCin
        </NavLink>
      </div>
      <nav>
        {menuItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            end={item.path === '/'} 
            className={({ isActive }) =>
              `menu-item${isActive ? ' active' : ''}`
            }
          >
            {item.label}
          </NavLink>
        ))}

        {/* 구분선 */}
        <div className="divider">OTHERS</div>

        {otherItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `menu-item${isActive ? ' active' : ''}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

export default Sidebar;
