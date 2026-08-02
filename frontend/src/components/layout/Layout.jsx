import { Link, useLocation } from 'react-router-dom';
import { useApp } from '../../context/AppContext.jsx';
import { useI18n } from '../../context/I18nContext.jsx';

export default function Layout({ children, breadcrumbs = [] }) {
  const { pageTitle, pageSubtitle, pageCover, banner, status, copyToast } = useApp();
  const { t } = useI18n();
  const location = useLocation();
  const isSettings = location.pathname === '/settings';

  return (
    <>
      <a className="skip-link" href="#main-content">
        {t('Skip to main content')}
      </a>

      <header className="site-header">
        <div className="container">
          <div className="page-heading">
            <img
              className="page-cover"
              src={pageCover || undefined}
              alt=""
              hidden={!pageCover}
            />
            <div className="page-heading__text">
              <h1 id="page-title" className="animated-gradient-text">
                {pageTitle}
              </h1>
              <p id="page-subtitle">{pageSubtitle}</p>
            </div>
          </div>
        </div>
      </header>

      {breadcrumbs.length > 0 && (
        <div className="breadcrumbs-bar" id="breadcrumbs-bar">
          <div className="container">
            <nav className="breadcrumbs" id="breadcrumbs" aria-label={t('Breadcrumb')}>
              <ol className="breadcrumbs__list" id="breadcrumbs-list">
                {breadcrumbs.map((crumb, index) => {
                  const isCurrent = !crumb.to;
                  return (
                    <li
                      key={`${crumb.label}-${index}`}
                      className={`breadcrumbs__item${isCurrent ? ' breadcrumbs__item--current' : ''}`}
                      {...(isCurrent ? { 'aria-current': 'page' } : {})}
                    >
                      {crumb.to ? (
                        <Link className="breadcrumbs__link" to={crumb.to}>
                          {crumb.label}
                        </Link>
                      ) : (
                        <span className="breadcrumbs__current">{crumb.label}</span>
                      )}
                    </li>
                  );
                })}
              </ol>
            </nav>
          </div>
        </div>
      )}

      <main id="main-content" className="page-content container" tabIndex={-1}>
        {banner.message && (
          <div
            className={`banner ${banner.type} is-visible`}
            id="banner"
            role={banner.type === 'error' ? 'alert' : 'status'}
            aria-live="polite"
          >
            <div className="banner__visual" aria-hidden="true">
              <span className="banner__orb" />
              <span className="banner__ring" />
              <span className="banner__spark" />
            </div>
            <div className="banner__body">
              {banner.type === 'loading' && (
                <span className="banner__eyebrow">{t('Just a moment')}</span>
              )}
              <span className="banner__text">{banner.message}</span>
              <span className="banner__shimmer" aria-hidden="true" />
            </div>
          </div>
        )}
        {children}
      </main>

      <div
        className={`status${status.visible ? ' visible' : ''} ${status.type}`}
        id="status"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {status.message}
      </div>
      <div
        className={`copy-toast${copyToast.visible ? ' visible' : ''}`}
        id="copy-toast"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {copyToast.message}
      </div>

      <Link
        className={`settings-link${isSettings ? ' settings-link--active' : ''}`}
        id="settings-link"
        to="/settings"
        aria-label={t('Settings')}
      >
        <span aria-hidden="true">⚙</span>
        <span>{t('Settings')}</span>
      </Link>
    </>
  );
}
