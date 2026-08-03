import { useEffect } from 'react';
import Layout from '../components/layout/Layout.jsx';
import ListeningStatsSection, { useListeningStatsLoader } from '../components/statistics/ListeningStatsSection.jsx';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';

export default function StatisticsPage() {
  const { t } = useI18n();
  const { setPage, setBanner, showStatus } = useApp();
  const stats = useListeningStatsLoader({ setBanner, showStatus });

  useEffect(() => {
    setPage({
      title: t('Statistics'),
      subtitle: t('Your most played tracks and artists on Spotify.'),
      cover: null,
    });
  }, [setPage, t]);

  const breadcrumbs = [
    { label: t('Home'), to: '/' },
    { label: t('Statistics') },
  ];

  return (
    <Layout breadcrumbs={breadcrumbs}>
      <section className="statistics-screen listening-screen view" id="statistics-view" aria-labelledby="stats-heading">
        <h2 id="stats-heading" className="sr-only">
          {t('Statistics')}
        </h2>
        <ListeningStatsSection stats={stats} />
      </section>
    </Layout>
  );
}
