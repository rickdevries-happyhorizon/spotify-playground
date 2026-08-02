import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/layout/Layout.jsx';
import { useJobPolling } from '../hooks/useJobPolling.js';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';

export default function JobProgressPage({
  title,
  subtitle,
  eyebrow,
  steps,
  phaseProgress,
  startJob,
  pollJob,
  resumeJob,
  breadcrumbs,
  successActions,
  errorActions,
  renderResultStats,
  renderCard,
}) {
  const { t } = useI18n();
  const { setPage, setBanner } = useApp();

  const computePercent = (job) => {
    const phase = job.phase || 'starting';
    let percent = phaseProgress[phase] ?? 8;

    if (['playlist_start', 'fetching_tracks', 'playlist_done'].includes(phase)) {
      const index = Number(job.playlist_index || 0);
      const total = Number(job.playlist_total || 1);
      const sliceStart = phaseProgress.playlist_start ?? 18;
      const sliceEnd = phaseProgress.playlist_done ?? 48;
      const slice = sliceEnd - sliceStart;
      const playlistProgress = total ? Math.min(1, Math.max(0, (index - 1) / total)) : 0;
      percent = Math.round(sliceStart + slice * playlistProgress);
    }

    return percent;
  };

  const isDone = (job) => job.phase === 'done' || job.status === 'done';
  const isError = (job) => job.phase === 'error' || job.status === 'error';

  const { phase, job, error, displayPercent, run } = useJobPolling({
    startJob: resumeJob || startJob,
    pollJob,
    computePercent,
    isDone,
    isError,
    autoStart: true,
  });

  usePageMeta({ title, subtitle, setPage, setBanner });

  const activeStepIndex = steps.findIndex((step) => step.key === (job?.phase || 'starting'));

  return (
    <Layout breadcrumbs={breadcrumbs}>
      <section className={`fetch-screen view${phase === 'success' ? ' is-success' : ''}${phase === 'error' ? ' is-error' : ''}`}>
        <div className="fetch-stage">
          <div className="fetch-visual" aria-hidden="true">
            <div className="fetch-orbit fetch-orbit--outer" />
            <div className="fetch-orbit fetch-orbit--inner" />
            <div className="fetch-disc">
              <span className="fetch-disc__groove" />
              <span className="fetch-disc__groove fetch-disc__groove--2" />
              <span className="fetch-disc__label">♪</span>
            </div>
          </div>

          <div className="fetch-content">
            <p className="fetch-eyebrow">{eyebrow}</p>
            <h2 className="fetch-title">{title}</h2>
            <p className="fetch-message">{job?.message || subtitle}</p>

            {phase !== 'success' && phase !== 'error' && (
              <div
                className="fetch-progress-wrap is-active"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(displayPercent)}
              >
                <div className="fetch-progress-track">
                  <div className="fetch-progress-bar" style={{ width: `${displayPercent}%` }} />
                  <div className="fetch-progress-glow" style={{ left: `${displayPercent}%` }} aria-hidden="true" />
                </div>
                <div className="fetch-progress-meta">
                  <span>{job?.message || t('Working…')}</span>
                  <span aria-hidden="true">{Math.round(displayPercent)}%</span>
                </div>
              </div>
            )}

            {renderCard?.(job)}

            <ul className="fetch-steps">
              {steps.map((step, index) => (
                <li
                  key={step.key}
                  className={`fetch-step${
                    index < activeStepIndex || phase === 'success'
                      ? ' is-done'
                      : step.key === (job?.phase || 'starting')
                        ? ' is-active'
                        : ''
                  }`}
                >
                  {step.label}
                </li>
              ))}
            </ul>

            {phase === 'success' && job && (
              <div className="fetch-result">
                <div className="fetch-result__stats">{renderResultStats?.(job, t)}</div>
                <div className="fetch-result__actions">
                  {successActions.map((action) =>
                    action.to ? (
                      <Link key={action.label} className={`fetch-action ${action.className || ''}`} to={action.to}>
                        {action.label}
                      </Link>
                    ) : (
                      <button
                        key={action.label}
                        type="button"
                        className={`fetch-action ${action.className || ''}`}
                        onClick={() => run()}
                      >
                        {action.label}
                      </button>
                    ),
                  )}
                </div>
              </div>
            )}

            {phase === 'error' && (
              <div className="fetch-error" role="alert">
                <p>{error || job?.message}</p>
                <div className="fetch-result__actions">
                  {errorActions.map((action) =>
                    action.to ? (
                      <Link key={action.label} className={`fetch-action ${action.className || ''}`} to={action.to}>
                        {action.label}
                      </Link>
                    ) : (
                      <button
                        key={action.label}
                        type="button"
                        className={`fetch-action ${action.className || ''}`}
                        onClick={() => run()}
                      >
                        {action.label}
                      </button>
                    ),
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </Layout>
  );
}

function usePageMeta({ title, subtitle, setPage, setBanner }) {
  useEffect(() => {
    setPage({ title, subtitle, cover: null });
    setBanner('');
  }, [title, subtitle, setPage, setBanner]);
}
