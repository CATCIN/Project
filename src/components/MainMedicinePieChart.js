// src/components/MainMedicinePieChart.js
import React, { useState, useEffect } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

// 동적 색상 팔레트 (카테고리가 늘어나도 괜찮도록)
const CHART_COLORS = ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e74c3c', '#1abc9c'];

function MainMedicinePieChart() {
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [],
    stats: [], // stats도 초기화
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // [추가] 데이터가 없는지 여부를 명시적으로 관리
  const [noData, setNoData] = useState(false); 

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        setNoData(false); // 초기화
        const response = await fetch('/catcin/schedules/stats/category');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const stats = await response.json();

        if (stats && stats.length > 0) {
          // ... (기존 데이터 변환 로직 동일) ...
          const labels = stats.map(item => item.label);
          const dataValues = stats.map(item => item.value);
          const total = dataValues.reduce((sum, value) => sum + value, 0);

          setChartData({
            labels: labels,
            stats: stats.map(item => ({ ...item, percentage: ((item.value / total) * 100).toFixed(1) })),
            datasets: [
              {
                label: '스케줄 비율',
                data: dataValues,
                backgroundColor: stats.map((_, index) => CHART_COLORS[index % CHART_COLORS.length]),
                hoverOffset: 8,
              },
            ],
          });
        } else {
          // [수정] 데이터가 0건일 때 noData 상태를 true로 설정
          setNoData(true);
          setChartData({ labels: [], datasets: [], stats: [] }); // 상태 비우기
        }
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchChartData();
  }, []);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: {
        callbacks: {
          label: function (context) {
            const label = context.label || '';
            const value = context.parsed || 0;
            return `${label}: ${value}개`;
          },
        },
      },
      legend: {
        display: false,
      },
    },
  };
  
  if (loading) return <div className="medicine-widget"><h3>로딩 중...</h3></div>;
  if (error) return <div className="medicine-widget"><h3>에러: {error}</h3></div>;

  return (
    <div className="medicine-widget">
      <div className="widget-header">
        <h3>주요 투약 약물 카테고리</h3>
      </div>
      <div className="chart-area">
        <div style={{ 
            width: '200px', 
            height: '200px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            color: '#888',
            position: 'relative'
          }}>
          {chartData.datasets.length > 0 ? (
            <Pie data={chartData} options={options} />
          ) : (
            !loading && <p>데이터가 없습니다.</p>
          )}
        </div>
        <div className="legend">
          {chartData.stats && chartData.stats.map((item, index) => (
            <div className="legend-item" key={item.label}>
              <div 
                className="legend-color-box" 
                style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
              ></div>
              <span>{`${item.label} ${item.percentage}%`}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default MainMedicinePieChart;