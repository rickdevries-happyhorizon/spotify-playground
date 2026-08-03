import { Link } from 'react-router-dom';
import { useI18n } from '../context/I18nContext.jsx';

export default function AppModuleCard({ module: mod, index = 0 }) {
  return (
    <li>
      <Link
        className={`app-card magic-card blur-fade ${mod.className}`}
        to={mod.path}
        style={{ animationDelay: `${index * 70}ms` }}
      >
        <span className="magic-card__glow" aria-hidden="true" />
        <span className="app-card__icon" aria-hidden="true">
          {mod.icon}
        </span>
        <span className="app-card__body">
          <span className="app-card__name">{mod.label}</span>
          <span className="app-card__desc">{mod.description}</span>
        </span>
      </Link>
    </li>
  );
}

export function useAppModules() {
  const { t } = useI18n();

  return [
    {
      label: t('Track to-do list'),
      description: t('Manage reference URLs for new tracks by genre.'),
      icon: '✓',
      path: '/todo',
      className: 'app-card--todo',
    },
    {
      label: t('Fetch new tracks'),
      description: t('Scan tracking playlists for new additions and add them to your download to-do list.'),
      icon: '↓',
      path: '/fetch',
      className: 'app-card--fetch',
    },
    {
      label: t('Sync playlists'),
      description: t('Pull new tracks from followed artists, discovered artists, and source playlists into your destination playlist.'),
      icon: '↻',
      path: '/sync',
      className: 'app-card--sync',
    },
    {
      label: t('Download to AIFF'),
      description: t('Download tracks with YouTube URLs as AIFF files. Completed tracks are removed from your to-do list.'),
      icon: '♫',
      path: '/download',
      className: 'app-card--download',
    },
    {
      label: t('Statistics'),
      description: t('Your most played tracks and artists on Spotify.'),
      icon: '📊',
      path: '/statistics',
      className: 'app-card--stats',
    },
  ];
}
