import { create } from 'zustand';
import { AlertItem } from '../types';

interface EmergencyState {
  isEmergencyActive: boolean;
  activeAlert: AlertItem | null;
  countdownSeconds: number;
  audioMuted: boolean;
  triggerEmergency: (alert: AlertItem) => void;
  dismissEmergency: () => void;
  toggleAudio: () => void;
  setCountdownSeconds: (seconds: number) => void;
}

export const useEmergencyStore = create<EmergencyState>((set) => ({
  isEmergencyActive: false,
  activeAlert: null,
  countdownSeconds: 5,
  audioMuted: false,

  triggerEmergency: (alert: AlertItem) => {
    set({
      isEmergencyActive: true,
      activeAlert: alert,
      countdownSeconds: 5,
    });
  },

  dismissEmergency: () => {
    set({
      isEmergencyActive: false,
      activeAlert: null,
    });
  },

  toggleAudio: () => set((state) => ({ audioMuted: !state.audioMuted })),
  setCountdownSeconds: (countdownSeconds) => set({ countdownSeconds }),
}));
