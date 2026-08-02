import JobProgressPage from '../components/JobProgressPage.jsx';
import {
  fetchImportStatus,
  fetchActiveSync,
  fetchSyncStatus,
  fetchDownloadStatus,
  startImport,
  startSync,
  startDownload,
} from '../api/client.js';
import { useI18n } from '../context/I18nContext.jsx';

const FETCH_PHASE_PROGRESS = {
  queued: 4,
  starting: 8,
  playlist_start: 18,
  fetching_tracks: 34,
  playlist_done: 48,
  fetching_energy: 72,
  saving: 88,
  done: 100,
  error: 100,
};

export default function FetchPage() {
  const { t } = useI18n();

  return (
    <JobProgressPage
      title={t('Fetching new tracks')}
      subtitle={t('Connecting to Spotify…')}
      eyebrow={t('Spotify import')}
      phaseProgress={FETCH_PHASE_PROGRESS}
      startJob={startImport}
      pollJob={(jobId) => fetchImportStatus(jobId)}
      steps={[
        { key: 'starting', label: t('Prepare') },
        { key: 'playlists', label: t('Scan playlists') },
        { key: 'energy', label: t('Fetch energy') },
        { key: 'saving', label: t('Save tracks') },
        { key: 'done', label: t('Complete') },
      ]}
      breadcrumbs={[
        { label: t('Release Finder'), to: '/' },
        { label: t('Fetch new tracks') },
      ]}
      renderCard={(job) =>
        job?.playlist_name ? (
          <div className="fetch-playlist-card">
            {job.playlist_image_url ? (
              <img className="fetch-playlist-card__art" src={job.playlist_image_url} alt="" />
            ) : (
              <span className="fetch-playlist-card__placeholder" aria-hidden="true">
                ♪
              </span>
            )}
            <div className="fetch-playlist-card__body">
              <span className="fetch-playlist-card__label">{t('Current playlist')}</span>
              <strong className="fetch-playlist-card__name">{job.playlist_name}</strong>
            </div>
          </div>
        ) : null
      }
      renderResultStats={(job, translate) => (
        <>
          <p>{translate('Import complete.')}</p>
          {job.inserted != null && (
            <p>{translate('{count} tracks added', { count: job.inserted })}</p>
          )}
          {job.energy_unavailable && (
            <p className="fetch-result__note">
              {translate(
                'Track energy is not available. Spotify no longer allows new apps to use the audio-features API.',
              )}
            </p>
          )}
        </>
      )}
      successActions={[
        { label: t('View to-do list'), to: '/todo', className: 'fetch-action--primary shimmer-button' },
        { label: t('Fetch again'), className: 'fetch-action--ghost' },
        { label: t('Back to home'), to: '/', className: 'fetch-action--ghost' },
      ]}
      errorActions={[
        { label: t('Open settings'), to: '/settings', className: 'fetch-action--primary' },
        { label: t('Try again'), className: 'fetch-action--ghost' },
      ]}
    />
  );
}

export function SyncPage() {
  const { t } = useI18n();

  const resumeOrStart = async () => {
    const active = await fetchActiveSync();
    if (active?.id) return active;
    return startSync(false);
  };

  return (
    <JobProgressPage
      title={t('Syncing playlists')}
      subtitle={t('Connecting to Spotify…')}
      eyebrow={t('Playlist sync')}
      phaseProgress={{
        queued: 2,
        starting: 4,
        artists_start: 6,
        artists_done: 22,
        discovery_done: 34,
        playlist_start: 38,
        fetching_tracks: 48,
        playlist_done: 62,
        adding: 84,
        done: 100,
        error: 100,
      }}
      startJob={() => startSync(false)}
      resumeJob={resumeOrStart}
      pollJob={(jobId) => fetchSyncStatus(jobId)}
      steps={[
        { key: 'starting', label: t('Prepare') },
        { key: 'artists_start', label: t('Followed artists') },
        { key: 'discovery_start', label: t('Discovery') },
        { key: 'playlist_start', label: t('Source playlists') },
        { key: 'done', label: t('Complete') },
      ]}
      breadcrumbs={[
        { label: t('Release Finder'), to: '/' },
        { label: t('Sync playlists') },
      ]}
      renderResultStats={(job, translate) => (
        <p>{translate('Sync complete. {count} tracks added.', { count: job.tracks_added ?? 0 })}</p>
      )}
      successActions={[
        { label: t('Back to home'), to: '/', className: 'fetch-action--primary shimmer-button' },
        { label: t('Sync again'), className: 'fetch-action--ghost' },
      ]}
      errorActions={[
        { label: t('Open settings'), to: '/settings', className: 'fetch-action--primary' },
        { label: t('Try again'), className: 'fetch-action--ghost' },
      ]}
    />
  );
}

export function DownloadPage() {
  const { t } = useI18n();

  return (
    <JobProgressPage
      title={t('Downloading tracks')}
      subtitle={t('Preparing downloads…')}
      eyebrow={t('AIFF download')}
      phaseProgress={{
        queued: 4,
        starting: 8,
        downloading: 40,
        tagging: 75,
        done: 100,
        error: 100,
      }}
      startJob={startDownload}
      pollJob={(jobId) => fetchDownloadStatus(jobId)}
      steps={[
        { key: 'starting', label: t('Prepare') },
        { key: 'downloading', label: t('Download') },
        { key: 'tagging', label: t('Tag metadata') },
        { key: 'done', label: t('Complete') },
      ]}
      breadcrumbs={[
        { label: t('Release Finder'), to: '/' },
        { label: t('Download to AIFF') },
      ]}
      renderResultStats={(job, translate) => {
        const successCount = Number(job.success_count ?? job.result?.success_count ?? 0);
        const errorCount = Number(job.error_count ?? job.result?.error_count ?? 0);

        return (
          <>
            {successCount > 0 ? (
              <p>
                {successCount === 1
                  ? translate('1 track downloaded as AIFF.')
                  : translate('{count} tracks downloaded as AIFF.', { count: successCount })}
              </p>
            ) : (
              <p>{translate('No tracks were downloaded.')}</p>
            )}
            {errorCount > 0 && (
              <p className="fetch-result__note">
                {errorCount === 1
                  ? translate('1 track failed.')
                  : translate('{count} tracks failed.', { count: errorCount })}
              </p>
            )}
          </>
        );
      }}
      successActions={[
        { label: t('View to-do list'), to: '/todo', className: 'fetch-action--primary shimmer-button' },
        { label: t('Download again'), className: 'fetch-action--ghost' },
        { label: t('Back to home'), to: '/', className: 'fetch-action--ghost' },
      ]}
      errorActions={[
        { label: t('Open settings'), to: '/settings', className: 'fetch-action--primary' },
        { label: t('Try again'), className: 'fetch-action--ghost' },
      ]}
    />
  );
}
