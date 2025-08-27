function TodayCatItem({ name, lastDate, thumbnail }) {
  return (
    <div className="today-cat-item">
      <img src={thumbnail} alt={name} />
      <div className="info">
        <span className="name">{name}</span>
        <span className="last-date">마지막 투약 날짜: {lastDate}</span>
      </div>
    </div>
  );
}

export default TodayCatItem;
