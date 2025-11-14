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
import './RecentDosageSection.css';


ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

function RecentDosageSection() {
  const data = {
    labels: ['11/1','11/2','11/3','11/4','11/5','11/6','11/7','11/8','11/9','11/10','11/11','11/12'],
    datasets: [
      {
        label: 'This month (count)',
        data: [1, 2, 0, 1, 1, 2, 1, 0, 1, 2, 1, 1],
        backgroundColor: 'rgba(39, 174, 96, 0.9)',
        borderRadius: 4,
        borderSkipped: false
      },
      {
        label: 'Last month (count)',
        data: [0, 1, 1, 1, 0, 1, 2, 1, 1, 1, 2, 1],
        backgroundColor: 'rgba(39, 174, 96, 0.25)',
        borderRadius: 4,
        borderSkipped: false
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          font: { size: 12 },
          padding: 12,
          color: '#333'
        }
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
        },
        ticks: {
          font: { size: 11 }
        }
      },
      y: {
        grid: {
          drawBorder: false,
          color: 'rgba(200,200,200,0.2)'
        },
        ticks: {
          beginAtZero: true,
          font: { size: 11 }
        }
      }
    }
  };

  return (
    <div className="recent-dosage-card">
      <div className="recent-dosage-right">
        <div className="chart-header">
          <h3>최근 투약량</h3>
          <div className="stats">
            <span className="highlight">↑ 2.1% vs last week</span>
          </div>
        </div>
        <div className="chart-area">
          <Bar data={data} options={options} />
        </div>
      </div>
    </div>
  );
}

export default RecentDosageSection;
