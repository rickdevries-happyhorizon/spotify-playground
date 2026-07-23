(function () {
  let locale = window.__LOCALE__ || "en";
  let catalog = window.__TRANSLATIONS__ || {};

  function format(template, vars) {
    if (!vars) return template;
    return template.replace(/\{(\w+)\}/g, (_, key) => String(vars[key] ?? `{${key}}`));
  }

  function t(msgid, vars) {
    const text = catalog[msgid] || msgid;
    return format(text, vars);
  }

  function tn(singularMsgid, pluralMsgid, count, vars) {
    const msgid = count === 1 ? singularMsgid : pluralMsgid;
    return t(msgid, { ...vars, count });
  }

  function setLocale(nextLocale, nextCatalog) {
    locale = nextLocale || locale;
    catalog = nextCatalog || catalog;
    document.documentElement.lang = locale === "brab" ? "nl-BE" : locale;
    document.documentElement.dataset.locale = locale;
  }

  function getLocale() {
    return locale;
  }

  window.t = t;
  window.tn = tn;
  window.setLocale = setLocale;
  window.getLocale = getLocale;
})();
