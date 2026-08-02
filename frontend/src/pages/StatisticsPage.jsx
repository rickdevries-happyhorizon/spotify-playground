import { useEffect, useState } from 'react';
import Layout from '../components/layout/Layout.jsx';
import { fetchGenres, fetchTracks } from '../api/client.js';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';

export default function StatisticsPage() {
  const { t } = useI18n();
  const { setPage, setBanner, showStatus } = useApp();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    setPage({
      title: t('Statistics'),
      subtitle: t('Overview of your new tracks and reference URL progress.'),
      cover: null,
    });
  }, [setPage, t]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setBanner(t('Loading statistics…'), 'loading');
      try {
        const [genresData, tracksData] = await Promise.all([fetchGenres(), fetchTracks()]);
        if (cancelled) return;

        const withUrl = tracksData.with_url || [];
        const withoutUrl = tracksData.without_url || [];
        const total = withUrl.length + withoutUrl.length;
        const completion = total ? (withUrl.length / total) * 100 : 0;

        setStats({
          genres: (genresData.genres || []).length,
          total,
          withUrl: withUrl.length,
          withoutUrl: withoutUrl.length,
          completion,
        });
        setBanner('');
      } catch (error) {
        if (!cancelled) {
          setBanner(t('Failed to load statistics: {message}', { message: error.message }), 'error');
          showStatus(error.message, 'error');
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [setBanner, showStatus, t]);

  const breadcrumbs = [
    { label: t('Home'), to: '/' },
    { label: t('Statistics') },
  ];

  return (
    <Layout breadcrumbs={breadcrumbs}>
      <section className="statistics-screen view" id="statistics-view" aria-labelledby="stats-heading">
        <h2 id="stats-heading" className="sr-only">
          {t('Statistics')}
        </h2>
        {stats && (
          <div className="stats-summary" id="stats-summary">
            <article className="stats-card">
              <span className="stats-card__label">{t('Total tracks')}</span>
              <strong className="stats-card__value">{stats.total}</strong>
            </article>
            <article className="stats-card">
              <span className="stats-card__label">{t('Has reference URL')}</span>
              <strong className="stats-card__value">{stats.withUrl}</strong>
            </article>
            <article className="stats-card">
              <span className="stats-card__label">{t('Needs reference URL')}</span>
              <strong className="stats-card__value">{stats.withoutUrl}</strong>
            </article>
            <article className="stats-card">
              <span className="stats-card__label">{t('Completion')}</span>
              <strong className="stats-card__value">{Math.round(stats.completion)}%</strong>
            </article>
            <article className="stats-card">
              <span className="stats-card__label">{t('Genres')}</span>
              <strong className="stats-card__value">{stats.genres}</strong>
            </article>
          </div>
        )}
      </section>
    </Layout>
  );
}
