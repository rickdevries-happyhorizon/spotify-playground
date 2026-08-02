import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/layout/Layout.jsx';
import CardArt from '../components/CardArt.jsx';
import { fetchGenres } from '../api/client.js';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { genrePath } from '../utils/paths.js';

function GenreSkeletonItem() {
  return (
    <li className="genre-skeleton-item" aria-hidden="true">
      <div className="genre-card genre-card--skeleton">
        <span className="skeleton skeleton--art" />
        <span className="genre-card__body">
          <span className="skeleton skeleton--line skeleton--line-title" />
          <span className="skeleton skeleton--line skeleton--line-meta" />
        </span>
      </div>
    </li>
  );
}

export default function GenreListPage() {
  const { t, tn } = useI18n();
  const { setPage, setBanner, showStatus } = useApp();
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPage({
      title: t('Track to-do'),
      subtitle: t('Choose a genre to manage reference URLs for its tracks.'),
      cover: null,
    });
  }, [setPage, t]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setBanner(t('Loading genres…'), 'loading');
      try {
        const data = await fetchGenres();
        if (!cancelled) {
          setGenres(data.genres || []);
          if (!data.total) {
            setBanner(t('No tracks found in new_tracks table.'), 'error');
          } else {
            setBanner('');
          }
        }
      } catch (error) {
        if (!cancelled) {
          setBanner(t('Failed to load genres: {message}', { message: error.message }), 'error');
          showStatus(error.message, 'error');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [setBanner, showStatus, t]);

  const breadcrumbs = [
    { label: t('Home'), to: '/' },
    { label: t('Track to-do') },
  ];

  return (
    <Layout breadcrumbs={breadcrumbs}>
      <section className="genre-screen view" id="genre-view" aria-labelledby="genre-heading">
        <h2 id="genre-heading">{t('Genres')}</h2>
        <ul className="genre-grid" id="genre-grid" aria-busy={loading}>
          {loading &&
            Array.from({ length: 6 }).map((_, index) => <GenreSkeletonItem key={index} />)}
          {!loading && genres.length === 0 && <li className="empty">{t('No genres found.')}</li>}
          {!loading &&
            genres.map((genre, index) => (
              <li key={genre.slug}>
                <Link
                  className="genre-card blur-fade"
                  to={genrePath(genre.slug)}
                  style={{ animationDelay: `${Math.min(index, 12) * 45}ms` }}
                >
                  <CardArt imageUrl={genre.image_url} label={genre.label} />
                  <span className="genre-card__body">
                    <span className="genre-card__name">{genre.label}</span>
                    <span className="genre-card__count">
                      {tn('1 track', '{count} tracks', genre.track_count)}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
        </ul>
      </section>
    </Layout>
  );
}
