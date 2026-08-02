import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Layout from '../components/layout/Layout.jsx';
import TrackItem, { AddTrackForm } from '../components/TrackItem.jsx';
import { fetchGenres, fetchTracks } from '../api/client.js';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import {
  FILTER_WITH_URL,
  FILTER_WITHOUT_URL,
  genrePath,
  resolveGenreSlug,
} from '../utils/paths.js';

export default function TracksPage() {
  const { genreSlug, filter } = useParams();
  const { t } = useI18n();
  const { setPage, setBanner, showStatus } = useApp();
  const [genre, setGenre] = useState(null);
  const [tracks, setTracks] = useState({ with_url: [], without_url: [] });
  const [activeFilter, setActiveFilter] = useState(filter || FILTER_WITH_URL);
  const [loading, setLoading] = useState(true);
  const [highlightedTrackId, setHighlightedTrackId] = useState(null);

  const normalizedFilter =
    filter === FILTER_WITHOUT_URL ? FILTER_WITHOUT_URL : FILTER_WITH_URL;

  useEffect(() => {
    setActiveFilter(normalizedFilter);
    setHighlightedTrackId(null);
  }, [normalizedFilter]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setBanner(t('Loading tracks from database…'), 'loading');
      try {
        const genresData = await fetchGenres();
        const knownGenres = (genresData.genres || []).map((g) => g.slug);
        const resolved = resolveGenreSlug(genreSlug, knownGenres);
        if (cancelled) return;
        setGenre(resolved);

        const filterLabel =
          normalizedFilter === FILTER_WITH_URL ? t('Has reference URL') : t('Needs reference URL');
        setPage({
          title: resolved,
          subtitle: filterLabel,
          cover: null,
        });

        const data = await fetchTracks(resolved);
        if (cancelled) return;

        setTracks({
          with_url: data.with_url || [],
          without_url: data.without_url || [],
        });
        if (data.genre_image_url) {
          setPage({ cover: data.genre_image_url });
        }
        if (!data.total) {
          setBanner(t('No tracks found for {genre}.', { genre: resolved }), 'error');
        } else {
          setBanner('');
        }
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
  }, [genreSlug, normalizedFilter, setBanner, setPage, showStatus, t]);

  const visibleTracks = useMemo(
    () => (activeFilter === FILTER_WITH_URL ? tracks.with_url : tracks.without_url),
    [activeFilter, tracks],
  );

  const handleTrackUpdate = (updated) => {
    setTracks((prev) => {
      const remove = (list) => list.filter((item) => item.id !== updated.id);
      const withList = remove(prev.with_url);
      const without = remove(prev.without_url);
      const entry = { ...updated, reference_url: updated.reference_url };

      if (updated.has_url || updated.reference_url) {
        return {
          with_url: [...withList, entry].sort((a, b) => a.track.localeCompare(b.track)),
          without_url: without,
        };
      }
      return {
        with_url: withList,
        without_url: [...without, entry].sort((a, b) => a.track.localeCompare(b.track)),
      };
    });
  };

  const handleTrackDelete = (trackId) => {
    setHighlightedTrackId((current) => (current === trackId ? null : current));
    setTracks((prev) => ({
      with_url: prev.with_url.filter((item) => item.id !== trackId),
      without_url: prev.without_url.filter((item) => item.id !== trackId),
    }));
  };

  const handleTrackAdded = (created) => {
    setTracks((prev) => {
      const list = created.reference_url ? 'with_url' : 'without_url';
      return {
        ...prev,
        [list]: [...prev[list], created].sort((a, b) => a.track.localeCompare(b.track)),
      };
    });
  };

  const breadcrumbs = [
    { label: t('Home'), to: '/' },
    { label: t('Track to-do'), to: '/todo' },
    { label: genre || '…', to: genre ? genrePath(genre) : undefined },
    {
      label: activeFilter === FILTER_WITH_URL ? t('Has reference URL') : t('Needs reference URL'),
    },
  ];

  if (loading || !genre) {
    return (
      <Layout breadcrumbs={breadcrumbs}>
        <div className="view tracks-screen" id="tracks-view">
          <p className="empty">{t('Loading…')}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout breadcrumbs={breadcrumbs}>
      <div className="view tracks-screen" id="tracks-view">
        <div className="filter-tabs" id="filter-tabs" role="tablist" aria-label={t('Track lists')}>
          <Link
            className={`filter-tab filter-tab--done${activeFilter === FILTER_WITH_URL ? ' active' : ''}`}
            id="tab-with-url"
            to={genrePath(genre, FILTER_WITH_URL)}
            role="tab"
            aria-selected={activeFilter === FILTER_WITH_URL}
            aria-controls="column-done"
          >
            {t('Has reference URL')} <span className="count" id="tab-count-done">{tracks.with_url.length}</span>
          </Link>
          <Link
            className={`filter-tab filter-tab--todo${activeFilter === FILTER_WITHOUT_URL ? ' active' : ''}`}
            id="tab-without-url"
            to={genrePath(genre, FILTER_WITHOUT_URL)}
            role="tab"
            aria-selected={activeFilter === FILTER_WITHOUT_URL}
            aria-controls="column-todo"
          >
            {t('Needs reference URL')} <span className="count" id="tab-count-todo">{tracks.without_url.length}</span>
          </Link>
        </div>

        <AddTrackForm genre={genre} onAdded={handleTrackAdded} />

        <div className="tracks-panels">
          <section
            className="column column--done"
            id="column-done"
            role="tabpanel"
            aria-labelledby="tab-with-url"
            hidden={activeFilter !== FILTER_WITH_URL}
          >
            <div className="column-header">
              <span>{t('Has reference URL')}</span>
              <span className="count" id="count-done">{tracks.with_url.length}</span>
            </div>
            <ul className="track-list" id="list-done">
              {loading && <li className="empty">{t('Loading…')}</li>}
              {!loading && activeFilter === FILTER_WITH_URL && visibleTracks.length === 0 && (
                <li className="empty">{t('No tracks with a URL yet.')}</li>
              )}
              {!loading &&
                activeFilter === FILTER_WITH_URL &&
                visibleTracks.map((track) => (
                  <TrackItem
                    key={track.id}
                    track={track}
                    highlighted={highlightedTrackId === track.id}
                    onHighlight={() => setHighlightedTrackId(track.id)}
                    onUpdate={handleTrackUpdate}
                    onDelete={handleTrackDelete}
                  />
                ))}
            </ul>
          </section>

          <section
            className="column column--todo"
            id="column-todo"
            role="tabpanel"
            aria-labelledby="tab-without-url"
            hidden={activeFilter !== FILTER_WITHOUT_URL}
          >
            <div className="column-header">
              <span>{t('Needs reference URL')}</span>
              <span className="count" id="count-todo">{tracks.without_url.length}</span>
            </div>
            <ul className="track-list" id="list-todo">
              {loading && <li className="empty">{t('Loading…')}</li>}
              {!loading && activeFilter === FILTER_WITHOUT_URL && visibleTracks.length === 0 && (
                <li className="empty">{t('All tracks have a reference URL.')}</li>
              )}
              {!loading &&
                activeFilter === FILTER_WITHOUT_URL &&
                visibleTracks.map((track) => (
                  <TrackItem
                    key={track.id}
                    track={track}
                    highlighted={highlightedTrackId === track.id}
                    onHighlight={() => setHighlightedTrackId(track.id)}
                    onUpdate={handleTrackUpdate}
                    onDelete={handleTrackDelete}
                  />
                ))}
            </ul>
          </section>
        </div>

        {activeFilter === FILTER_WITHOUT_URL && (
          <div className="url-finder-waver" aria-hidden="true">
            <img
              className="url-finder-waver__banana"
              src="/static/img/hyves-dancing-banana.gif"
              alt=""
              width="120"
              height="127"
              decoding="async"
            />
          </div>
        )}
      </div>
    </Layout>
  );
}
