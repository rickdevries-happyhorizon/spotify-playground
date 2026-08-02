import { useState } from 'react';
import { createTrack, deleteTrack, recordCopyTitle, updateTrackUrl } from '../api/client.js';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { copyToClipboard } from '../utils/paths.js';

export default function TrackItem({ track, showGenre = false, onUpdate, onDelete, highlighted, onHighlight }) {
  const { t } = useI18n();
  const { showStatus, showCopyToast } = useApp();
  const [url, setUrl] = useState(track.reference_url || '');
  const [copyCount, setCopyCount] = useState(Number(track.copy_title_count || 0));
  const [saving, setSaving] = useState(false);

  const handleCopyTitle = async () => {
    onHighlight?.();
    const ok = await copyToClipboard(track.track);
    showCopyToast(ok ? t('{label} copied', { label: t('Title') }) : t('Nothing to copy'));
    if (!ok) return;

    const previous = copyCount;
    setCopyCount(previous + 1);
    try {
      const data = await recordCopyTitle(track.id);
      setCopyCount(Number(data.copy_title_count || previous + 1));
    } catch (error) {
      setCopyCount(previous);
      showStatus(error.message, 'error');
    }
  };

  const handleSave = async (event) => {
    event.preventDefault();
    onHighlight?.();
    setSaving(true);
    try {
      const updated = await updateTrackUrl(track.id, url.trim());
      onUpdate?.({
        ...track,
        reference_url: updated.reference_url,
        has_url: updated.has_url,
      });
      showStatus(
        updated.has_url ? t('Saved — moved to Has URL list') : t('Cleared — moved to Needs URL list'),
      );
    } catch (error) {
      showStatus(error.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    onHighlight?.();
    try {
      await deleteTrack(track.id);
      onDelete?.(track.id);
      showStatus(t('Track removed'));
    } catch (error) {
      showStatus(error.message, 'error');
    }
  };

  return (
    <li className="track-item" data-id={track.id}>
      <div className="track-main">
        {track.image_url ? (
          <img className="track-art" src={track.image_url} alt="" loading="lazy" />
        ) : (
          <span className="art-placeholder track-art" aria-hidden="true">
            ♪
          </span>
        )}
        <div className="track-body">
          <div className="track-heading">
            <div
              className={`track-name${highlighted ? ' track-name--highlight' : ''}`}
              role="button"
              tabIndex={0}
              title={t('Click to copy title')}
              aria-label={`${t('Copy track title')}: ${track.track}`}
              onClick={(event) => {
                handleCopyTitle();
                event.currentTarget.blur();
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  handleCopyTitle();
                  event.currentTarget.blur();
                }
              }}
            >
              {track.track}
              {copyCount > 0 && <span className="track-name-count">{copyCount}</span>}
            </div>
            {showGenre && track.genre && <div className="track-genre">{track.genre}</div>}
            {track.energy != null && (
              <div className="track-energy">
                {t('Energy: {value}', { value: Number(track.energy).toFixed(2) })}
              </div>
            )}
          </div>
          <form className="track-form" onSubmit={handleSave}>
            <label className="field-label">
              <span className="sr-only">{t('Reference URL')}</span>
              <input
                type="url"
                name="reference_url"
                placeholder="https://..."
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                aria-label={t('Reference URL')}
                autoComplete="off"
              />
            </label>
            <button type="submit" disabled={saving}>
              {t('Save')}
            </button>
            <button type="button" className="remove" aria-label={`${t('Remove')}: ${track.track}`} onClick={handleRemove}>
              {t('Remove')}
            </button>
          </form>
        </div>
      </div>
    </li>
  );
}

export function AddTrackForm({ genre, onAdded }) {
  const { t } = useI18n();
  const { showStatus } = useApp();
  const [track, setTrack] = useState('');
  const [referenceUrl, setReferenceUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        track: track.trim(),
        reference_url: referenceUrl.trim(),
      };
      if (genre && genre !== 'Uncategorized') {
        payload.genre = genre;
      }
      const created = await createTrack(payload);
      onAdded?.(created);
      setTrack('');
      setReferenceUrl('');
      showStatus(
        created.reference_url ? t('Track added to Has URL list') : t('Track added to Needs URL list'),
      );
    } catch (error) {
      showStatus(error.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="add-panel" aria-labelledby="add-track-heading">
      <h2 id="add-track-heading">{t('Add track')}</h2>
      <form className="add-form" onSubmit={handleSubmit}>
        <label className="field-label">
          <span className="sr-only">{t('Track name')}</span>
          <input
            type="text"
            name="track"
            placeholder={t('Artist - Track name')}
            value={track}
            onChange={(event) => setTrack(event.target.value)}
            autoComplete="off"
            required
          />
        </label>
        <label className="field-label">
          <span className="sr-only">{t('Reference URL')}</span>
          <input
            type="url"
            name="reference_url"
            placeholder={t('Reference URL (optional)')}
            value={referenceUrl}
            onChange={(event) => setReferenceUrl(event.target.value)}
            autoComplete="off"
          />
        </label>
        <button type="submit" className="shimmer-button" disabled={submitting}>
          {t('Add')}
        </button>
      </form>
    </section>
  );
}
