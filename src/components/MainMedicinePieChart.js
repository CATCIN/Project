// src/components/MainMedicinePieChart.js
import { Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';


ChartJS.register(ArcElement, Tooltip, Legend);

function MainMedicinePieChart() {
  // 더미 데이터 (실제 데이터가 있으면 API 등에서 받아오면 됩니다)
  const data = {
    labels: ['Panacur', 'Paracap', 'Piline'],
    datasets: [
      {
        label: '약물 비율',
        data: [40, 32, 28],
        backgroundColor: [
          '#3498db', // 파란색 (Panacur)
          '#2ecc71', // 연두색 (Paracap)
          '#9b59b6'  // 보라색 (Piline)
        ],
        hoverOffset: 8
      }
    ]
  };

  // 옵션: 툴팁에 “1,890 pills” 같은 상세 텍스트를 넣으려면
  const options = {
    plugins: {
      tooltip: {
        callbacks: {
          label: function (context) {
            const label = context.label || '';
            // 여기서 value는 비율(숫자)인가? 실제값(pills)을 넣으려면
            // 예: pillsCount = [1890, 1500, 1300]처럼 별도의 배열로 관리
            let pillsCount;
            if (label === 'Panacur') pillsCount = 1890;
            else if (label === 'Paracap') pillsCount = 1600;
            else if (label === 'Piline') pillsCount = 1300;
            return `${label}: ${pillsCount.toLocaleString()} pills`;
          }
        }
      },
      legend: {
        display: false // 직접 범례를 커스터마이징 하려고 껐습니다.
      }
    }
  };

  // 직접 범례(Legend)를 커스터마이징: 우리가 만드는 <div className="legend"> 내부에서 색상 박스와 레이블을 나열
  return (
    <div className="medicine-widget">
      <div className="widget-header">
        <h3>주요 투약 약물</h3>
        <button>View Report</button>
      </div>
      <div className="chart-area">
        <div style={{ width: '240px', height: '240px' }}>
          <Pie data={data} options={options} />
        </div>
        <div className="legend">
          <div className="legend-item">
            <div className="legend-color-box pancaur"></div>
            <span>Panacur 40%</span>
          </div>
          <div className="legend-item">
            <div className="legend-color-box paracap"></div>
            <span>Paracap 32%</span>
          </div>
          <div className="legend-item">
            <div className="legend-color-box piline"></div>
            <span>Piline 28%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MainMedicinePieChart;
