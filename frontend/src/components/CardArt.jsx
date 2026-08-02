export default function CardArt({ imageUrl, label = '', className = 'card-art' }) {
  if (imageUrl) {
    return <img className={className} src={imageUrl} alt={label} loading="lazy" />;
  }
  return (
    <span className={`art-placeholder ${className}`} aria-hidden="true">
      ♪
    </span>
  );
}
