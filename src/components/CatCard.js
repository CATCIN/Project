import './CatCard.css';

function CatCard({ imageUrl, height = '100%' }) {
  return (
    <div className="cat-card" style={{ height }}>
      <img src={imageUrl} alt="cat" />
    </div>
  );
}

export default CatCard;