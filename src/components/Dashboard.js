// src/components/Dashboard.js
import React from 'react';
import RecentCatsSection from './RecentCatsSection';
import MainMedicinePieChart from './MainMedicinePieChart';
import TodayCatsList from './TodayCatsList';
import RecentDosageSection from './RecentDosageSection';
import './Dashboard.css'; // 레이아웃 관련 혹은 섹션 간 마진/그리드 정의

function Dashboard({ recentCats }) {
  return (
    <div className="dashboard">
      {/* 1. 상단 대시보드 타이틀 */}
      <h1>Dashboard</h1>

      <div className="dashboard-top">
        {/* 왼쪽: 최근 인식된 고양이(6개) */}
        <div className="recent-cats-wrapper">
          <RecentCatsSection cats={recentCats} />
        </div>

        {/* 오른쪽: 주요 투약 약물 Pie Chart 위젯 */}
        <div className="medicine-widget-wrapper">
          <MainMedicinePieChart />
        </div>
      </div>

      <div className="dashboard-bottom">
        {/* 왼쪽: 오늘 투약 대상인 고양이 */}
        <div className="today-cats-wrapper">
          <TodayCatsList />
        </div>

        {/* 오른쪽: 최근 투약량 */}
        <div className="recent-dosage-wrapper">
          <RecentDosageSection />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
