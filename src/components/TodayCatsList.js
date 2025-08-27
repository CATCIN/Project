import TodayCatItem from './TodayCatItem';

function TodayCatsList() {
  const todayCats = [
    { name: 'catA', lastDate: '25.05.14', thumbnail: '/images/catA.jpg' },
    { name: 'catB', lastDate: '25.05.14', thumbnail: '/images/catB.jpg' },
    { name: 'catC', lastDate: '25.05.14', thumbnail: '/images/catC.jpg' }
  ];

  return (
    <div className="today-cats-card">
      <h3>오늘 투약 대상인 고양이</h3>
      <div className="today-cats-list">
        {todayCats.map((cat, idx) => (
          <TodayCatItem
            key={idx}
            name={cat.name}
            lastDate={cat.lastDate}
            thumbnail={cat.thumbnail}
          />
        ))}
      </div>
    </div>
  );
}

export default TodayCatsList;
