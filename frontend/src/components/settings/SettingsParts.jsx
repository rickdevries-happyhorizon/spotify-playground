function ThemePreview({ skin }) {
  const barsBySkin = {
    light: 'theme-card__bars theme-card__bars--mono',
    dark: 'theme-card__bars theme-card__bars--dark',
    retroui: 'theme-card__bars theme-card__bars--retroui',
    winxp: 'theme-card__bars theme-card__bars--winxp',
  };

  return (
    <span className={`theme-card__preview theme-card__preview--${skin}`} aria-hidden="true">
      {skin === 'retroui' && <span className="theme-card__stamp" />}
      {skin === 'winxp' && <span className="theme-card__xp-title" />}
      <span className={barsBySkin[skin]}>
        <span />
        <span />
        <span />
      </span>
    </span>
  );
}

function SettingsCardShell({ accentClass, children, ...props }) {
  return (
    <section {...props}>
      <div className={`settings-card__accent ${accentClass}`} aria-hidden="true" />
      <div className="magic-card__glow" aria-hidden="true" />
      {children}
    </section>
  );
}

export { ThemePreview, SettingsCardShell };
