import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Layout from '../components/layout/Layout.jsx';
import CardArt from '../components/CardArt.jsx';
import { fetchGenres, fetchTracks } from '../api/client.js';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { FILTER_WITH_URL, FILTER_WITHOUT_URL, genrePath, resolveGenreSlug } from '../utils/paths.js';

function FilterSkeletonItem() {
  return (
    <li className="filter-skeleton-item" aria-hidden="true">
      <div className="filter-card filter-card--skeleton">
        <span className="skeleton skeleton--art" />
        <span className="filter-card__body">
          <span className="skeleton skeleton--line skeleton--line-title" />
          <span className="skeleton skeleton--line skeleton--line-meta" />
        </span>
      </div>
    </li>
  );
}

export default function GenreHubPage() {
  const { genreSlug } = useParams();
  const { t, tn } = useI18n();
  const { setPage, setBanner, showStatus } = useApp();
  const [genre, setGenre] = useState(null);
  const [genreImageUrl, setGenreImageUrl] = useState(null);
  const [counts, setCounts] = useState({ withUrl: 0, withoutUrl: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setBanner(t('Loading track counts…'), 'loading');
      try {
        const genresData = await fetchGenres();
        const knownGenres = (genresData.genres || []).map((g) => g.slug);
        const resolved = resolveGenreSlug(genreSlug, knownGenres);
        if (cancelled) return;
        setGenre(resolved);

        setPage({
          title: resolved,
          subtitle: t('Choose a list'),
          cover: null,
        });

        const tracks = await fetchTracks(resolved);
        if (cancelled) return;

        setCounts({
          withUrl: tracks.with_url?.length || 0,
          withoutUrl: tracks.without_url?.length || 0,
        });
        if (tracks.genre_image_url) {
          setGenreImageUrl(tracks.genre_image_url);
          setPage({ cover: tracks.genre_image_url });
        }
        setBanner('');
      } catch (error) {
        if (!cancelled) {
          setBanner(t('Failed to load tracks: {message}', { message: error.message }), 'error');
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
  }, [genreSlug, setBanner, setPage, showStatus, t]);

  const choices = [
    {
      filter: FILTER_WITH_URL,
      label: t('Has reference URL'),
      count: counts.withUrl,
      className: 'filter-card--done',
    },
    {
      filter: FILTER_WITHOUT_URL,
      label: t('Needs reference URL'),
      count: counts.withoutUrl,
      className: 'filter-card--todo',
    },
  ];

  const breadcrumbs = [
    { label: t('Home'), to: '/' },
    { label: t('Track to-do'), to: '/todo' },
    { label: genre || '…' },
  ];

  return (
    <Layout breadcrumbs={breadcrumbs}>
      <section className="genre-hub view" id="genre-hub-view" aria-labelledby="genre-hub-heading">
        <h2 id="genre-hub-heading">{t('Choose a list')}</h2>
        <ul className="filter-grid" id="filter-grid" aria-busy={loading}>
          {loading ? (
            <>
              <FilterSkeletonItem />
              <FilterSkeletonItem />
            </>
          ) : (
            choices.map((choice, index) => (
              <li key={choice.filter}>
                <Link
                  className={`filter-card ${choice.className} blur-fade`}
                  to={genrePath(genre, choice.filter)}
                  style={{ animationDelay: `${index * 60}ms` }}
                >
                  <CardArt imageUrl={genreImageUrl} label={genre || ''} />
                  <span className="filter-card__body">
                    <span className="filter-card__name">{choice.label}</span>
                    <span className="filter-card__count">
                      {tn('1 track', '{count} tracks', choice.count)}
                    </span>
                  </span>
                </Link>
              </li>
            ))
          )}
        </ul>
      </section>
    </Layout>
  );
}
