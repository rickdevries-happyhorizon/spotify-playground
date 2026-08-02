import { useEffect, useState } from 'react';
import Layout from '../components/layout/Layout.jsx';
import { fetchSettings, lookupPlaylist, saveSettings } from '../api/client.js';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { ThemePreview, SettingsCardShell } from '../components/settings/SettingsParts.jsx';

function PlaylistRow({ value, name, onChange, onRemove, removable = true }) {
  const { t } = useI18n();
  const [meta, setMeta] = useState(name || '');

  useEffect(() => {
    if (!value.trim()) {
      setMeta('');
      return undefined;
    }

    const timer = setTimeout(async () => {
      try {
        const data = await lookupPlaylist(value.trim());
        setMeta(data.name || '');
      } catch {
        setMeta('');
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [value]);

  return (
    <div className="playlist-input-row">
      <label className="settings-field playlist-input-row__field">
        <span className="sr-only">{t('Playlist URL')}</span>
        <input
          type="text"
          className="playlist-id-input"
          placeholder="https://open.spotify.com/playlist/…"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          autoComplete="off"
          aria-label={t('Playlist URL')}
        />
        {meta && <span className="playlist-meta playlist-meta--resolved">{meta}</span>}
      </label>
      {removable && (
        <div className="playlist-input-row__actions">
          <button
            type="button"
            className="playlist-remove-btn"
            title={t('Remove playlist')}
            aria-label={t('Remove playlist')}
            onClick={onRemove}
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const { t, tn, setLocale } = useI18n();
  const { setPage, setBanner, showStatus } = useApp();
  const [loading, setLoading] = useState(true);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    ui_skin: 'light',
    locale: 'en',
    destination_playlist: '',
    destination_name: '',
    source_playlists: [''],
    tracking_playlists: [''],
    sync_start_date: '',
    tracking_start_date: '',
    artist_discovery_enabled: false,
  });

  useEffect(() => {
    setPage({
      title: t('Settings'),
      subtitle: t('Customize your sync workflow and visual style.'),
      cover: null,
    });
    document.documentElement.dataset.skin = form.ui_skin;
  }, [form.ui_skin, setPage, t]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const settings = await fetchSettings();
        if (cancelled) return;
        setForm({
          ui_skin: settings.ui_skin || 'light',
          locale: settings.locale || 'en',
          destination_playlist: settings.destination_playlist?.spotify_id || '',
          destination_name: settings.destination_playlist?.name || '',
          source_playlists: settings.source_playlists?.length
            ? settings.source_playlists.map((p) => p.spotify_id || '')
            : [''],
          tracking_playlists: settings.tracking_playlists?.length
            ? settings.tracking_playlists.map((p) => p.spotify_id || '')
            : [''],
          sync_start_date: settings.sync_start_date || '',
          tracking_start_date: settings.tracking_start_date || settings.start_date || '',
          artist_discovery_enabled: Boolean(settings.artist_discovery_enabled),
        });
        document.documentElement.dataset.skin = settings.ui_skin || 'light';
      } catch (error) {
        showStatus(error.message, 'error');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [showStatus]);

  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setDirty(true);
    if (key === 'ui_skin') {
      document.documentElement.dataset.skin = value;
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      const payload = {
        ui_skin: form.ui_skin,
        locale: form.locale,
        destination_playlist: form.destination_playlist.trim(),
        source_playlists: form.source_playlists.map((v) => v.trim()).filter(Boolean),
        tracking_playlists: form.tracking_playlists.map((v) => v.trim()).filter(Boolean),
        sync_start_date: form.sync_start_date || null,
        tracking_start_date: form.tracking_start_date || null,
        artist_discovery_enabled: form.artist_discovery_enabled,
      };
      const saved = await saveSettings(payload);
      await setLocale(saved.locale || form.locale);
      setDirty(false);
      setBanner('');
      showStatus(t('Settings saved'));
    } catch (error) {
      showStatus(error.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const breadcrumbs = [
    { label: t('Home'), to: '/' },
    { label: t('Settings') },
  ];

  const sourceCount = form.source_playlists.filter((value) => value.trim()).length;
  const trackingCount = form.tracking_playlists.filter((value) => value.trim()).length;

  if (loading) {
    return (
      <Layout breadcrumbs={breadcrumbs}>
        <p>{t('Loading…')}</p>
      </Layout>
    );
  }

  return (
    <Layout breadcrumbs={breadcrumbs}>
      <section className="settings-screen view" id="settings-view" aria-labelledby="settings-hero-title">
        <div className="settings-hero">
          <div className="settings-hero__content">
            <span className="settings-hero__icon" aria-hidden="true">
              ⚙
            </span>
            <div>
              <h2 className="settings-hero__title animated-gradient-text" id="settings-hero-title">
                {t('Control panel')}
              </h2>
              <p className="settings-hero__subtitle">
                {t('Tune the look, sync playlists, and set how new tracks are imported.')}
              </p>
            </div>
          </div>
        </div>

        <form className="settings-form" id="settings-form" onSubmit={handleSubmit}>
          <div className="settings-grid">
            <SettingsCardShell
              className="settings-card settings-card--theme magic-card"
              accentClass=""
              aria-labelledby="settings-theme-heading"
            >
              <div className="settings-card__header">
                <span className="settings-card__icon" aria-hidden="true">
                  🎨
                </span>
                <div>
                  <h3 id="settings-theme-heading">{t('Theme')}</h3>
                  <p>{t('Pick the vibe for the whole app.')}</p>
                </div>
              </div>
              <div className="theme-cards" role="radiogroup" aria-labelledby="settings-theme-heading">
                {[
                  { value: 'light', label: t('Light'), hint: t('Clean black & white') },
                  { value: 'dark', label: t('Dark'), hint: t('Flat dark mode') },
                  { value: 'retroui', label: t('RetroUI'), hint: t('Neo-brutalism') },
                  { value: 'winxp', label: t('Windows XP'), hint: t('Classic Luna desktop') },
                ].map((theme) => (
                  <label key={theme.value} className={`theme-card theme-card--${theme.value}`}>
                    <input
                      type="radio"
                      name="ui_skin"
                      value={theme.value}
                      checked={form.ui_skin === theme.value}
                      onChange={() => updateField('ui_skin', theme.value)}
                    />
                    <span className="theme-card__frame">
                      <ThemePreview skin={theme.value} />
                      <span className="theme-card__label">
                        <strong>{theme.label}</strong>
                        <small>{theme.hint}</small>
                      </span>
                      <span className="theme-card__check" aria-hidden="true">
                        ✓
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </SettingsCardShell>

            <SettingsCardShell
              className="settings-card settings-card--language magic-card"
              accentClass=""
              aria-labelledby="settings-language-heading"
            >
              <div className="settings-card__header">
                <span className="settings-card__icon" aria-hidden="true">
                  🌐
                </span>
                <div>
                  <h3 id="settings-language-heading">{t('Language')}</h3>
                  <p>{t('Choose the language for labels and messages.')}</p>
                </div>
              </div>
              <div className="language-cards" role="radiogroup" aria-labelledby="settings-language-heading">
                {[
                  { value: 'en', label: t('English'), hint: 'English' },
                  { value: 'nl', label: t('Dutch'), hint: 'Nederlands' },
                  { value: 'brab', label: t('Brabants'), hint: 'Brabants' },
                ].map((lang) => (
                  <label key={lang.value} className="language-card">
                    <input
                      type="radio"
                      name="locale"
                      value={lang.value}
                      checked={form.locale === lang.value}
                      onChange={() => updateField('locale', lang.value)}
                    />
                    <span className="language-card__frame">
                      <span className="language-card__label">
                        <strong>{lang.label}</strong>
                        <small>{lang.hint}</small>
                      </span>
                      <span className="language-card__check" aria-hidden="true">
                        ✓
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </SettingsCardShell>

            <SettingsCardShell
              className="settings-card settings-card--playlists magic-card"
              accentClass=""
              aria-labelledby="settings-playlists-heading"
            >
              <div className="settings-card__header">
                <span className="settings-card__icon" aria-hidden="true">
                  🎵
                </span>
                <div>
                  <h3 id="settings-playlists-heading">{t('Playlists')}</h3>
                  <p>{t('Configure destination, sources, and tracking playlists.')}</p>
                </div>
              </div>
              <div className="settings-playlists-grid">
                <div className="settings-playlist-field settings-playlist-field--destination">
                  <h4 className="settings-playlist-field__title" id="destination-playlist-heading">
                    {t('Destination playlist')}
                  </h4>
                  <p className="settings-playlist-field__desc">{t('Where synced tracks land.')}</p>
                  <label className="settings-field">
                    <span className="sr-only">{t('Playlist URL')}</span>
                    {form.destination_name && (
                      <span className="playlist-meta playlist-meta--resolved">{form.destination_name}</span>
                    )}
                    <input
                      type="text"
                      name="destination_playlist"
                      value={form.destination_playlist}
                      onChange={(event) => updateField('destination_playlist', event.target.value)}
                      placeholder="https://open.spotify.com/playlist/…"
                      autoComplete="off"
                      aria-labelledby="destination-playlist-heading"
                    />
                  </label>
                </div>

                <div className="settings-playlist-field settings-playlist-field--source">
                  <div className="settings-playlist-field__head">
                    <div>
                      <h4 className="settings-playlist-field__title" id="source-playlists-heading">
                        {t('Source playlists')}
                      </h4>
                      <p className="settings-playlist-field__desc">
                        {t('Playlists to pull tracks from during sync.')}
                      </p>
                    </div>
                    <span className="settings-count">{tn('1 playlist', '{count} playlists', sourceCount)}</span>
                  </div>
                  <div className="playlist-input-list" role="group" aria-labelledby="source-playlists-heading">
                    {form.source_playlists.map((value, index) => (
                      <PlaylistRow
                        key={`source-${index}`}
                        value={value}
                        onChange={(next) => {
                          const list = [...form.source_playlists];
                          list[index] = next;
                          updateField('source_playlists', list);
                        }}
                        onRemove={() => {
                          const list = form.source_playlists.filter((_, i) => i !== index);
                          updateField('source_playlists', list.length ? list : ['']);
                        }}
                      />
                    ))}
                  </div>
                  <button
                    type="button"
                    className="playlist-add-btn"
                    onClick={() => updateField('source_playlists', [...form.source_playlists, ''])}
                  >
                    {t('+ Add source playlist')}
                  </button>
                </div>

                <div className="settings-playlist-field settings-playlist-field--tracking">
                  <div className="settings-playlist-field__head">
                    <div>
                      <h4 className="settings-playlist-field__title" id="tracking-playlists-heading">
                        {t('Tracking playlists')}
                      </h4>
                      <p className="settings-playlist-field__desc">
                        {t('Playlists scanned when importing new tracks.')}
                      </p>
                    </div>
                    <span className="settings-count">{tn('1 playlist', '{count} playlists', trackingCount)}</span>
                  </div>
                  <div className="playlist-input-list" role="group" aria-labelledby="tracking-playlists-heading">
                    {form.tracking_playlists.map((value, index) => (
                      <PlaylistRow
                        key={`tracking-${index}`}
                        value={value}
                        onChange={(next) => {
                          const list = [...form.tracking_playlists];
                          list[index] = next;
                          updateField('tracking_playlists', list);
                        }}
                        onRemove={() => {
                          const list = form.tracking_playlists.filter((_, i) => i !== index);
                          updateField('tracking_playlists', list.length ? list : ['']);
                        }}
                      />
                    ))}
                  </div>
                  <button
                    type="button"
                    className="playlist-add-btn"
                    onClick={() => updateField('tracking_playlists', [...form.tracking_playlists, ''])}
                  >
                    {t('+ Add tracking playlist')}
                  </button>
                </div>
              </div>
            </SettingsCardShell>

            <SettingsCardShell
              className="settings-card settings-card--dates magic-card"
              accentClass=""
              aria-labelledby="settings-dates-heading"
            >
              <div className="settings-card__header">
                <span className="settings-card__icon" aria-hidden="true">
                  📅
                </span>
                <div>
                  <h3 id="settings-dates-heading">{t('Dates')}</h3>
                  <p>{t('Control how far back sync and new-track import look.')}</p>
                </div>
              </div>
              <div className="settings-dates-grid">
                <div className="settings-date-field">
                  <h4 className="settings-date-field__title">{t('Sync start date')}</h4>
                  <p className="settings-date-field__desc">
                    {t('Artist releases and source playlist sync look back from this date.')}
                  </p>
                  <label className="settings-field">
                    <span className="settings-field__label">
                      {t('Start date')}{' '}
                      <span className="settings-field__hint">{t('(empty = last 7 days)')}</span>
                    </span>
                    <input
                      type="date"
                      name="sync_start_date"
                      value={form.sync_start_date}
                      onChange={(event) => updateField('sync_start_date', event.target.value)}
                    />
                  </label>
                </div>
                <div className="settings-date-field">
                  <h4 className="settings-date-field__title">{t('New tracks start date')}</h4>
                  <p className="settings-date-field__desc">
                    {t('Only import tracks into new_tracks after this date.')}
                  </p>
                  <label className="settings-field">
                    <span className="settings-field__label">{t('Start date')}</span>
                    <input
                      type="date"
                      name="tracking_start_date"
                      value={form.tracking_start_date}
                      onChange={(event) => updateField('tracking_start_date', event.target.value)}
                    />
                  </label>
                </div>
                <div className="settings-date-field settings-date-field--toggle">
                  <h4 className="settings-date-field__title">{t('Artist discovery')}</h4>
                  <p className="settings-date-field__desc">
                    {t('Find new artists from your tracking playlists and add recent releases to the destination playlist.')}
                  </p>
                  <label className="settings-toggle">
                    <input
                      type="checkbox"
                      name="artist_discovery_enabled"
                      checked={form.artist_discovery_enabled}
                      onChange={(event) => updateField('artist_discovery_enabled', event.target.checked)}
                    />
                    <span className="settings-toggle__control" aria-hidden="true">
                      <span className="settings-toggle__knob" />
                    </span>
                    <span className="settings-toggle__label">{t('Enable artist discovery during sync')}</span>
                  </label>
                </div>
              </div>
            </SettingsCardShell>
          </div>

          <div className={`settings-dock${dirty ? ' is-dirty' : ''}`} id="settings-dock">
            <div className="settings-dock__status" role="status" aria-live="polite">
              <span className="settings-dock__pulse" aria-hidden="true" />
              <span id="settings-dock-text">{dirty ? t('Ready to save') : t('All changes saved')}</span>
            </div>
            <button type="submit" className="settings-save shimmer-button" disabled={!dirty || saving}>
              <span className="settings-save__shine" aria-hidden="true" />
              <span className="shimmer-button__spark" aria-hidden="true" />
              {t('Save settings')}
            </button>
          </div>
        </form>
      </section>
    </Layout>
  );
}
