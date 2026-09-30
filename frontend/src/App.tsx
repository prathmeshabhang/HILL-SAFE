import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/Layout/AppLayout';
import { WelcomePage } from './pages/WelcomePage';
import { HomePage } from './pages/HomePage';
import { VillageWardPage } from './pages/VillageWardPage';
import { FloodMapPage } from './pages/FloodMapPage';
import { ForecastPage } from './pages/ForecastPage';
import { NaturalDamPage } from './pages/NaturalDamPage';
import { DamAnalysisPage } from './pages/DamAnalysisPage';
import { EvacuationPage } from './pages/EvacuationPage';
import { CommunityReportsPage } from './pages/CommunityReportsPage';
import { PreparednessPage } from './pages/PreparednessPage';
import { CommandPage } from './pages/CommandPage';
import { SensorsPage } from './pages/SensorsPage';
import { ModelsPage } from './pages/ModelsPage';
import { EmergencyPage } from './pages/EmergencyPage';
import { LoginPage } from './pages/LoginPage';
import { DevelopmentZonesPage } from './pages/DevelopmentZonesPage';
import { wsClient } from './services/websocket/wsClient';
import { fetchSystemHealth, fetchBasinRiskSummary } from './services/api/endpoints';
import { useHazardStore } from './store/useHazardStore';
import { useUiStore } from './store/useUiStore';

export const App: React.FC = () => {
  const { setBackendOnline, setRiskSummary } = useHazardStore();
  const { theme } = useUiStore();

  useEffect(() => {
    // Synchronize initial dark mode class
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Connect WebSocket gateway
    wsClient.connect();

    // Check system health
    fetchSystemHealth().then((health) => {
      setBackendOnline(health.status === 'healthy');
    });

    // Ingest basin risk summary
    fetchBasinRiskSummary().then(setRiskSummary);

    return () => {
      wsClient.disconnect();
    };
  }, []);

  return (
    <Routes>
      {/* Onboarding / Location Setup */}
      <Route path="/welcome" element={<WelcomePage />} />

      {/* Full-Screen Emergency Alarm (Page 7) */}
      <Route path="/emergency" element={<EmergencyPage />} />

      {/* Primary Disaster Management Layout Shell */}
      <Route element={<AppLayout />}>
        {/* 1. Command Dashboard (Image 1) */}
        <Route path="/" element={<HomePage />} />

        {/* 2. Village / Ward View (Image 2) */}
        <Route path="/ward-view" element={<VillageWardPage />} />

        {/* 3. Catchment Risk Map (Image 3) */}
        <Route path="/map" element={<FloodMapPage />} />

        {/* 4. Forecasts & Prediction (Image 4) */}
        <Route path="/forecasts" element={<ForecastPage />} />

        {/* 5. Sensor & Data Sources (Image 5) */}
        <Route path="/sensors" element={<SensorsPage />} />

        {/* Natural Dam AI Recognition & Hydrodynamic Breach Casing */}
        <Route path="/natural-dams" element={<NaturalDamPage />} />
        <Route path="/dam-analysis" element={<DamAnalysisPage />} />

        {/* Supporting Operations & Intelligence Suite */}
        <Route path="/command" element={<CommandPage />} />
        <Route path="/evacuation" element={<EvacuationPage />} />
        <Route path="/development-zones" element={<DevelopmentZonesPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/models" element={<ModelsPage />} />
        <Route path="/community" element={<CommunityReportsPage />} />
        <Route path="/preparedness" element={<PreparednessPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
