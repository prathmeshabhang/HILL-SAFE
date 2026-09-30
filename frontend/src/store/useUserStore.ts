import { create } from 'zustand';
import { UserProfile, UserRole, UserLocation } from '../types';

interface UserState {
  user: UserProfile | null;
  token: string | null;
  role: UserRole;
  location: UserLocation;
  isGuest: boolean;
  setRole: (role: UserRole) => void;
  setLocation: (location: UserLocation) => void;
  setAuth: (user: UserProfile, token: string) => void;
  logout: () => void;
  detectGpsLocation: () => Promise<boolean>;
}

// Default to Upper Beas basin (Manali, Himachal Pradesh, India)
const DEFAULT_LOCATION: UserLocation = {
  lat: 32.2396,
  lng: 77.1887,
  name: 'Manali Town, Beas River Valley',
  altitudeMeters: 2050,
};

export const useUserStore = create<UserState>((set) => ({
  user: {
    id: 'user-default-1',
    email: 'citizen@beas-valley.gov.in',
    fullName: 'Ananya Sharma',
    role: 'INCIDENT_COMMANDER', // Start in Commander role so all EOC features are easily testable
    agency: 'Himachal Pradesh State Disaster Management Authority',
    isCommander: true,
  },
  token: localStorage.getItem('floody_token') || 'dev-mock-session-token',
  role: (localStorage.getItem('floody_role') as UserRole) || 'INCIDENT_COMMANDER',
  location: DEFAULT_LOCATION,
  isGuest: false,

  setRole: (role: UserRole) => {
    localStorage.setItem('floody_role', role);
    set((state) => ({
      role,
      user: state.user
        ? {
            ...state.user,
            role,
            isCommander: role === 'INCIDENT_COMMANDER' || role === 'ADMIN',
          }
        : null,
    }));
  },

  setLocation: (location: UserLocation) => set({ location }),

  setAuth: (user: UserProfile, token: string) => {
    localStorage.setItem('floody_token', token);
    localStorage.setItem('floody_role', user.role);
    set({ user, token, role: user.role, isGuest: false });
  },

  logout: () => {
    localStorage.removeItem('floody_token');
    localStorage.removeItem('floody_role');
    set({
      user: null,
      token: null,
      role: 'CITIZEN',
      isGuest: true,
    });
  },

  detectGpsLocation: async () => {
    if (!navigator.geolocation) return false;
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          set({
            location: {
              lat: pos.coords.latitude,
              lng: pos.coords.longitude,
              name: `GPS: ${pos.coords.latitude.toFixed(4)}°N, ${pos.coords.longitude.toFixed(4)}°E`,
              accuracyMeters: pos.coords.accuracy,
              altitudeMeters: pos.coords.altitude || undefined,
            },
          });
          resolve(true);
        },
        () => {
          // Keep default Beas location
          resolve(false);
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    });
  },
}));
