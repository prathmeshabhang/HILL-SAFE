import { create } from 'zustand';

interface UiState {
  theme: 'dark' | 'light';
  sidebarOpen: boolean;
  sidebarPinned: boolean;
  sidebarHovered: boolean;
  activeModal: string | null;
  toggleTheme: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSidebarPinned: (pinned: boolean) => void;
  toggleSidebarPinned: () => void;
  setSidebarHovered: (hovered: boolean) => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  theme: (localStorage.getItem('floody_theme') as 'dark' | 'light') || 'dark',
  sidebarOpen: false, // Default to hidden to maximize screen canvas!
  sidebarPinned: false,
  sidebarHovered: false,
  activeModal: null,

  toggleTheme: () =>
    set((state) => {
      const newTheme = state.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('floody_theme', newTheme);
      if (newTheme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      return { theme: newTheme };
    }),

  setTheme: (theme) => {
    localStorage.setItem('floody_theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    set({ theme });
  },

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setSidebarPinned: (pinned) => set({ sidebarPinned: pinned }),
  toggleSidebarPinned: () => set((state) => ({ sidebarPinned: !state.sidebarPinned })),
  setSidebarHovered: (hovered) => set({ sidebarHovered: hovered }),
  openModal: (modalId) => set({ activeModal: modalId }),
  closeModal: () => set({ activeModal: null }),
}));
