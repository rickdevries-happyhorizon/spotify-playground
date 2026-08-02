import { Routes, Route, Navigate } from 'react-router-dom';
import StartPage from './pages/StartPage.jsx';
import GenreListPage from './pages/GenreListPage.jsx';
import GenreHubPage from './pages/GenreHubPage.jsx';
import TracksPage from './pages/TracksPage.jsx';
import SettingsPage from './pages/SettingsPage.jsx';
import StatisticsPage from './pages/StatisticsPage.jsx';
import FetchPage, { SyncPage, DownloadPage } from './pages/JobPages.jsx';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<StartPage />} />
      <Route path="/todo" element={<GenreListPage />} />
      <Route path="/todo/:genreSlug" element={<GenreHubPage />} />
      <Route path="/todo/:genreSlug/:filter" element={<TracksPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/statistics" element={<StatisticsPage />} />
      <Route path="/fetch" element={<FetchPage />} />
      <Route path="/sync" element={<SyncPage />} />
      <Route path="/download" element={<DownloadPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
