import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { fetchSettings } from '../api/client.js';

const I18nContext = createContext(null);

function format(template, vars) {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, key) => String(vars[key] ?? `{${key}}`));
}

async function loadCatalog(locale) {
  const response = await fetch(`/static/locale/${locale}.json`);
  if (!response.ok) {
    return {};
  }
  return response.json();
}

export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState('en');
  const [catalog, setCatalog] = useState({});
  const [ready, setReady] = useState(false);

  const applyLocale = useCallback(async (nextLocale) => {
    const catalogData = await loadCatalog(nextLocale);
    setLocaleState(nextLocale);
    setCatalog(catalogData);
    document.documentElement.lang = nextLocale === 'brab' ? 'nl-BE' : nextLocale;
    document.documentElement.dataset.locale = nextLocale;
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const settings = await fetchSettings();
        if (!cancelled) {
          document.documentElement.dataset.skin = settings.ui_skin || 'light';
          await applyLocale(settings.locale || 'en');
        }
      } catch {
        if (!cancelled) {
          await applyLocale('en');
        }
      } finally {
        if (!cancelled) setReady(true);
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, [applyLocale]);

  const t = useCallback(
    (msgid, vars) => format(catalog[msgid] || msgid, vars),
    [catalog],
  );

  const tn = useCallback(
    (singular, plural, count, vars) => t(count === 1 ? singular : plural, { ...vars, count }),
    [t],
  );

  const value = useMemo(
    () => ({ t, tn, locale, setLocale: applyLocale, ready }),
    [t, tn, locale, applyLocale, ready],
  );

  if (!ready) {
    return (
      <div className="page-content container" style={{ padding: '2rem 0' }}>
        <div className="banner loading is-visible" role="status">
          <div className="banner__visual" aria-hidden="true">
            <span className="banner__orb" />
            <span className="banner__ring" />
          </div>
          <div className="banner__body">
            <span className="banner__eyebrow">Loading</span>
            <span className="banner__text">Loading…</span>
          </div>
        </div>
      </div>
    );
  }

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
