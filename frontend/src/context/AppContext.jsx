import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [pageTitle, setPageTitle] = useState('Release Finder');
  const [pageSubtitle, setPageSubtitle] = useState('');
  const [pageCover, setPageCover] = useState(null);
  const [banner, setBannerState] = useState({ message: '', type: 'loading' });
  const [status, setStatusState] = useState({ message: '', type: 'success', visible: false });
  const [copyToast, setCopyToastState] = useState({ message: '', visible: false });

  const setPage = useCallback(({ title, subtitle, cover = null }) => {
    if (title !== undefined) {
      setPageTitle(title);
      document.title = title;
    }
    if (subtitle !== undefined) setPageSubtitle(subtitle);
    if (cover !== undefined) setPageCover(cover);
  }, []);

  const setBanner = useCallback((message, type = 'loading') => {
    setBannerState({ message: message || '', type });
  }, []);

  const showStatus = useCallback((message, type = 'success') => {
    setStatusState({ message, type, visible: true });
    window.clearTimeout(showStatus._timer);
    showStatus._timer = window.setTimeout(() => {
      setStatusState((prev) => ({ ...prev, visible: false }));
    }, 2200);
  }, []);

  const showCopyToast = useCallback((message) => {
    setCopyToastState({ message, visible: true });
    window.clearTimeout(showCopyToast._timer);
    showCopyToast._timer = window.setTimeout(() => {
      setCopyToastState((prev) => ({ ...prev, visible: false }));
    }, 1400);
  }, []);

  const value = useMemo(
    () => ({
      pageTitle,
      pageSubtitle,
      pageCover,
      banner,
      status,
      copyToast,
      setPage,
      setBanner,
      showStatus,
      showCopyToast,
    }),
    [pageTitle, pageSubtitle, pageCover, banner, status, copyToast, setPage, setBanner, showStatus, showCopyToast],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
