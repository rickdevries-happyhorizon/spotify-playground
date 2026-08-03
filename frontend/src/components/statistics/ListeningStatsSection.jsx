import { useEffect, useState } from 'react';
import { fetchListeningStats } from '../../api/client.js';
import { useI18n } from '../../context/I18nContext.jsx';

const PERIODS = ['week', 'month', 'year'];

function formatArtists(artists) {
  return artists?.length ? artists.join(', ') : '';
}

function TopList({ items, kind, emptyLabel, playCountLabel }) {
  if (!items?.length) {
    return <p className="listening-empty">{emptyLabel}</p>;
  }

  return (
    <ol className="listening-top-list">
      {items.map((item, index) => {
        const rank = item.rank ?? index + 1;
        const content = (
          <>
            <span className="listening-top-list__rank">{rank}</span>
            {item.image_url ? (
              <img className="listening-top-list__art" src={item.image_url} alt="" loading="lazy" />
            ) : (
              <span className="listening-top-list__art listening-top-list__art--placeholder" aria-hidden="true">
                {kind === 'track' ? '♫' : '★'}
              </span>
            )}
            <span className="listening-top-list__meta">
              <strong className="listening-top-list__name">{item.name}</strong>
              {kind === 'track' && item.artists?.length > 0 && (
                <span className="listening-top-list__sub">{formatArtists(item.artists)}</span>
              )}
            </span>
            {item.play_count != null && (
              <span className="listening-top-list__count">{playCountLabel(item.play_count)}</span>
            )}
          </>
        );

        return (
          <li key={`${kind}-${item.id || rank}`} className="listening-top-list__item">
            {item.spotify_url ? (
              <a
                className="listening-top-list__link"
                href={item.spotify_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                {content}
              </a>
            ) : (
              <div className="listening-top-list__link">{content}</div>
            )}
          </li>
        );
      })}
    </ol>
  );
}

export default function ListeningStatsSection({ stats }) {
  const { t, tn } = useI18n();
  const [period, setPeriod] = useState('week');

  const periodData = stats?.periods?.[period];
  const periodLabel = {
    week: t('This week'),
    month: t('This month'),
    year: t('This year'),
  }[period];

  if (!stats) {
    return null;
  }

  return (
    <>
      <div className="listening-hero">
        <div className="listening-hero__content">
          <span className="listening-hero__icon" aria-hidden="true">
            🎧
          </span>
          <div>
            <h2 className="listening-hero__title animated-gradient-text" id="listening-heading">
              {t('Your Spotify listening')}
            </h2>
            <p className="listening-hero__subtitle">
              {t('Top tracks and artists based on your play history.')}
            </p>
          </div>
        </div>
      </div>

      <div className="listening-period-tabs" role="tablist" aria-label={t('Time period')}>
        {PERIODS.map((value) => (
          <button
            key={value}
            type="button"
            role="tab"
            id={`listening-tab-${value}`}
            aria-selected={period === value}
            aria-controls={`listening-panel-${value}`}
            className={`listening-period-tabs__btn${period === value ? ' is-active' : ''}`}
            onClick={() => setPeriod(value)}
          >
            {{
              week: t('Week'),
              month: t('Month'),
              year: t('Year'),
            }[value]}
          </button>
        ))}
      </div>

      {periodData && (
        <div
          className="listening-panels"
          id={`listening-panel-${period}`}
          role="tabpanel"
          aria-labelledby={`listening-tab-${period}`}
        >
          {period === 'week' && periodData.source === 'spotify_top' && (
            <p className="listening-source-note">
              {t('Based on Spotify’s overall top lists — recent play history was too limited for this period.')}
            </p>
          )}

          <div className="listening-grid">
            <article className="listening-card magic-card">
              <span className="magic-card__glow" aria-hidden="true" />
              <header className="listening-card__header">
                <h3>{t('Top tracks — {period}', { period: periodLabel })}</h3>
              </header>
              <TopList
                items={periodData.tracks}
                kind="track"
                emptyLabel={t('No tracks found for this period.')}
                playCountLabel={(count) => tn('1 play', '{count} plays', count)}
              />
            </article>

            <article className="listening-card magic-card">
              <span className="magic-card__glow" aria-hidden="true" />
              <header className="listening-card__header">
                <h3>{t('Top artists — {period}', { period: periodLabel })}</h3>
              </header>
              <TopList
                items={periodData.artists}
                kind="artist"
                emptyLabel={t('No artists found for this period.')}
                playCountLabel={(count) => tn('1 play', '{count} plays', count)}
              />
            </article>
          </div>
        </div>
      )}
    </>
  );
}

export function useListeningStatsLoader({ setBanner, showStatus }) {
  const { t } = useI18n();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setBanner(t('Loading listening stats…'), 'loading');
      try {
        const data = await fetchListeningStats();
        if (cancelled) return;
        setStats(data);
        setBanner('');
      } catch (error) {
        if (!cancelled) {
          setBanner(t('Failed to load listening stats: {message}', { message: error.message }), 'error');
          showStatus(error.message, 'error');
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [setBanner, showStatus, t]);

  return stats;
}
