// src/components/RecentDosageSection.js
import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend
} from 'chart.js';


ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

function RecentDosageSection() {
  // 예시 데이터: 지난 6일 vs 지난 주 같은 요일(또는 가로축 1~12일)
  // 여기서는 “01, 02, 03 ... 12” 까지 총 12개 막대에,
  // 파란색 막대 = Last 6 days, 연한 파란 점선 막대 = Last Week
  const data = {
    labels: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'],
    datasets: [
      {
        label: 'Last 6 days',
        data: [1200, 1500, 1000, 1800, 1300, 1600, 1400, 1700, 1500, 1900, 2000, 1800],
        backgroundColor: 'rgba(52, 152, 219, 0.8)',
        borderRadius: 4
      },
      {
        label: 'Last Week',
        data: [1000, 1400, 900, 1600, 1200, 1500, 1300, 1600, 1400, 1800, 1900, 1700],
        backgroundColor: 'rgba(52, 152, 219, 0.3)', // 연한 색
        borderRadius: 4
      }
    ]
  };

  const options = {
    plugins: {
      legend: {
        display: false // 범례 숨기기 (오른쪽에 “Last 6 days vs Last Week” 텍스트만 있으면 충분)
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            return context.dataset.label + ': ' + context.parsed.y.toLocaleString();
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        }
      },
      y: {
        grid: {
          drawBorder: false,
          color: 'rgba(200,200,200,0.2)'
        },
        ticks: {
          beginAtZero: true
        }
      }
    }
  };

  return (
    <div className="recent-dosage-card">
      <h3>최근 투약량</h3>

      {/* 간단 텍스트 정보 */}
      <div className="stats">
        <span></span>
        <span className="highlight"> ↑ 2.1% vs last week</span>
        <br />
        <span>Administered from May 1 to 12, 2025</span>
      </div>

      {/* 막대 차트 */}
      <div className="chart-area">
        <Bar data={data} options={options} />
      </div>

      {/* View Report 버튼 */}
      <button className="view-report-btn">View Report</button>
    </div>
  );
}

export default RecentDosageSection;
