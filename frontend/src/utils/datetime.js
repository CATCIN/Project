export function formatKST(iso) {
  if (!iso) return '정보 없음';
  const d = new Date(iso);
  return d.toLocaleString('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric', month: 'numeric', day: 'numeric',
    hour: 'numeric', minute: 'numeric'
  });
}

export function formatKSTDate(iso) {
  if (!iso) return '정보 없음';
  const d = new Date(iso);
  return d.toLocaleDateString('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric', month: '2-digit', day: '2-digit'
  }).replace(/\s/g, '');
}
