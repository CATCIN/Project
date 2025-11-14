import React, { useMemo, useState } from 'react';
import './ScheduleTable.css';

function formatDate(iso) {
  if (!iso) return '정보 없음';
  try {
    const d = new Date(iso);
    return d.toLocaleString('ko-KR', {
      year: 'numeric', month: 'numeric', day: 'numeric',
      hour: 'numeric', minute: 'numeric'
    });
  } catch (e) {
    return '정보 없음';
  }
}

export default function ScheduleTable({ rows = [] }) {
  const [sortKey, setSortKey] = useState(null);
  const [dir, setDir] = useState('asc');

  const columns = [
    { key: 'medicine_name', label: '약 이름' },
    { key: 'medicine_category', label: '종류' },
    { key: 'interval_days', label: '투약 주기' },
    { key: 'dose', label: '용량' },
    { key: 'next_due_date', label: '다음 투약일' },
  ];

  const sorted = useMemo(() => {
    if (!sortKey) return rows;
    const copy = [...rows];
    copy.sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (sortKey === 'next_due_date') {
        const da = va ? new Date(va).getTime() : 0;
        const db = vb ? new Date(vb).getTime() : 0;
        return da - db;
      }
      if (typeof va === 'number' && typeof vb === 'number') return va - vb;
      return String(va || '').localeCompare(String(vb || ''), 'ko');
    });
    if (dir === 'desc') copy.reverse();
    return copy;
  }, [rows, sortKey, dir]);

  const toggleSort = (key) => {
    if (sortKey === key) setDir(dir === 'asc' ? 'desc' : 'asc');
    else {
      setSortKey(key);
      setDir('asc');
    }
  };

  if (!rows || rows.length === 0) {
    return <div className="schedule-table-component empty">등록된 투약 스케줄이 없습니다.</div>;
  }

  return (
    <div className="schedule-table-component">
      <div className="table-headers">
        {columns.map(col => (
          <div
            key={col.key}
            role="button"
            tabIndex={0}
            className={`header-cell ${sortKey === col.key ? 'active' : ''}`}
            onClick={() => toggleSort(col.key)}
            onKeyDown={(e) => { if (e.key === 'Enter') toggleSort(col.key); }}
          >
            <span className="label">{col.label}</span>
            {sortKey === col.key && <span className="sort-indicator">{dir === 'asc' ? '▲' : '▼'}</span>}
          </div>
        ))}
      </div>
      <div className="table-rows">
        {sorted.map((r, idx) => (
          <div className="schedule-row" key={r.schedule_id || idx}>
            <div className="cell name-cell">{r.medicine_name || '정보 없음'}</div>
            <div className="cell center">{r.medicine_category || '미분류'}</div>
            <div className="cell center">{r.interval_days ? `${r.interval_days}일` : '정보 없음'}</div>
            <div className="cell center">{r.dose ? `${r.dose}알` : '정보 없음'}</div>
            <div className="cell center">{formatDate(r.next_due_date)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
