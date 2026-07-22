import React, { useState } from 'react';
import Sidebar       from './components/Sidebar';
import DashboardPage from './components/DashboardPage';
import PredictionPage from './components/PredictionPage';
import HistoryPage   from './components/HistoryPage';
import InsightsPage  from './components/InsightsPage';
import AboutPage     from './components/AboutPage';

const PAGES = {
  dashboard: <DashboardPage />,
  predict:   <PredictionPage />,
  history:   <HistoryPage />,
  insights:  <InsightsPage />,
  about:     <AboutPage />
};

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <main style={{
        marginLeft: '220px',
        flex: 1,
        minHeight: '100vh',
        backgroundColor: '#F9FAFB'
      }}>
        {PAGES[activePage]}
      </main>
    </div>
  );
}