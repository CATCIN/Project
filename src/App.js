// src/App.js
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './components/Dashboard';

import CatListPage from './pages/CatListPage';
import CatDetailPage from './pages/CatDetailPage';
import MedicineListPage  from './pages/MedicineListPage';   // 페이지 컴포넌트 import
import MedicineFormPage  from './pages/MedicineFormPage';   // 등록 페이지 import
import SchedulePage      from './pages/SchedulePage';       // 스케줄 목록 import
import ScheduleFormPage  from './pages/ScheduleFormPage';   // 스케줄 생성 import


function App() {
  return (
    <div className="App">
      <Sidebar />

      <div className="main-content">
        <Header />
        <div className="dashboard-container">
          <Routes>
            {/* 메인(대시보드) */}
            <Route path="/catcin" element={<Dashboard />} />

            {/* 고양이 리스트 */}
            <Route path="/catcin/cats" element={<CatListPage />} />

            {/* 고양이 등록 페이지 */}
            {/*<Route path="/cats/new" element={<CreateCatPage />} />*/}

            {/* 고양이 상세 (예: /cats/1) */}
            <Route path="/catcin/cats/:id" element={<CatDetailPage />} />

            {/* 약 목록 페이지 */}
            <Route path="/catcin/medicine" element={<MedicineListPage />} />

            {/* 약 등록 페이지 */}
            <Route path="/catcin/medicine/new" element={<MedicineFormPage />} />

            {/* 스케줄 목록 페이지 */}
            <Route path="/catcin/schedule" element={<SchedulePage />} />

            {/* 스케줄 등록 페이지 */}
            <Route path="/catcin/schedule/new" element={<ScheduleFormPage />} />

            {/* 설정 페이지, 도움말 페이지 등 */}
            <Route path="/catcin/settings" element={<div>Settings 페이지</div>} />
            <Route path="/catcin/help" element={<div>Help 페이지</div>} />

            {/* 그 외 잘못된 경로는 대시보드로 리디렉션 */}
            <Route path="*" element={<Navigate to="/catcin" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default App;
