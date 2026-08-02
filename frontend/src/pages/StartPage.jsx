import { useEffect } from 'react';
import Layout from '../components/layout/Layout.jsx';
import AppModuleCard, { useAppModules } from '../components/AppModuleCard.jsx';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';

export default function StartPage() {
  const { t } = useI18n();
  const { setPage, setBanner } = useApp();
  const modules = useAppModules();

  useEffect(() => {
    setPage({
      title: t('Release Finder'),
      subtitle: t('Choose a tool to get started.'),
      cover: null,
    });
    setBanner('');
  }, [setPage, setBanner, t]);

  return (
    <Layout>
      <section className="start-screen view" id="start-view" aria-labelledby="start-heading">
        <h2 id="start-heading" className="animated-gradient-text">
          {t('What would you like to do?')}
        </h2>
        <ul className="app-grid" id="app-grid">
          {modules.map((mod, index) => (
            <AppModuleCard key={mod.path} module={mod} index={index} />
          ))}
        </ul>
      </section>
    </Layout>
  );
}
