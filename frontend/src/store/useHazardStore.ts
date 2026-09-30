import { create } from 'zustand';
import { RiskSummary, AlertItem, NaturalDamCandidate, StationTelemetry } from '../types';

interface HazardState {
  riskSummary: RiskSummary;
  activeAlerts: AlertItem[];
  selectedDam: NaturalDamCandidate | null;
  selectedStation: StationTelemetry | null;
  backendOnline: boolean;
  setRiskSummary: (summary: RiskSummary) => void;
  setActiveAlerts: (alerts: AlertItem[]) => void;
  setSelectedDam: (dam: NaturalDamCandidate | null) => void;
  setSelectedStation: (station: StationTelemetry | null) => void;
  setBackendOnline: (online: boolean) => void;
}

const DEFAULT_RISK_SUMMARY: RiskSummary = {
  basin: 'Upper Beas River Catchment (Kullu - Manali)',
  timestamp: new Date().toISOString(),
  aggregate_risk_score: 0.68,
  severity_level: 'WARNING',
  active_warnings_count: 2,
  monitored_stations_count: 5,
  natural_dam_threat_level: 'HIGH',
  landslide_susceptibility: 'HIGH',
  rainfall_trend_mm_hr: 18.4,
  primary_threat_description: 'Monsoon surge combined with upstream landslide debris barrier accumulation in Solang tributary.',
};

export const useHazardStore = create<HazardState>((set) => ({
  riskSummary: DEFAULT_RISK_SUMMARY,
  activeAlerts: [
    {
      id: 'ALT-2026-0881',
      code: 'FLASH_FLOOD_WARNING',
      headline: 'Immediate Flash Flood Threat: Solang & Upper Beas Reach',
      description: 'Rapid stream discharge spike detected upstream of Palchan confluence. Water level rising at +0.42 m/hr.',
      severity: 'WARNING',
      status: 'AUTHORIZED',
      affected_zones: ['Palchan', 'Solang', 'Old Manali', 'Aleo'],
      recommended_actions: [
        'Move immediately to designated safe havens above 2,150 m elevation.',
        'Evacuate riverbank settlements within 150 m of Beas main channel.',
        'Avoid NH-3 Kullu-Manali highway low-lying underpasses.'
      ],
      created_at: new Date(Date.now() - 35 * 60000).toISOString(),
      expires_at: new Date(Date.now() + 180 * 60000).toISOString(),
      authorized_by: 'Er. Rajesh Thakur (State Incident Commander)',
      authorized_at: new Date(Date.now() - 30 * 60000).toISOString(),
      source_model: 'Hydrologic Cascade & Flash Flood Intelligence (v4.0)',
      requires_dual_authorization: true,
    }
  ],
  selectedDam: null,
  selectedStation: null,
  backendOnline: true,

  setRiskSummary: (riskSummary) => set({ riskSummary }),
  setActiveAlerts: (activeAlerts) => set({ activeAlerts }),
  setSelectedDam: (selectedDam) => set({ selectedDam }),
  setSelectedStation: (selectedStation) => set({ selectedStation }),
  setBackendOnline: (backendOnline) => set({ backendOnline }),
}));
