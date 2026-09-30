import { create } from 'zustand';

export interface MapLayersState {
  naturalDams: boolean;
  criticalZones: boolean; // Administrative Wards & Gram Panchayats
  floodRisk: boolean;     // Continuous Hazard Terrain Surface / Flood
  landslideRisk: boolean; // Landslide Susceptibility
  riverNetwork: boolean;  // Authoritative Beas River & Gorge Tributaries
  infrastructure: boolean;
  safeHavens: boolean;
  evacuationRoutes: boolean;
  sensorStations: boolean;
  radarOverlay: boolean;
}

export type BaseMapType = 'satellite' | 'hybrid' | 'terrain' | 'roadmap';

export interface MapFeatureDetails {
  type: string;
  id: string;
  name: string;
  riskTier?: string;
  dataMode?: string;
  timestamp?: string;
  properties: Record<string, any>;
  coordinates?: [number, number];
}

interface MapState {
  center: [number, number]; // [lng, lat]
  zoom: number;
  pitch: number;
  bearing: number;
  layers: MapLayersState;
  hazardOpacity: number;
  activeBasemap: BaseMapType;
  selectedFeatureId: string | null;
  selectedFeature: MapFeatureDetails | null;
  selectedRouteId: string | null;
  mapLoaded: boolean;
  setViewport: (center: [number, number], zoom: number, pitch?: number, bearing?: number) => void;
  toggleLayer: (layerKey: keyof MapLayersState) => void;
  setLayer: (layerKey: keyof MapLayersState, enabled: boolean) => void;
  setHazardOpacity: (opacity: number) => void;
  setActiveBasemap: (basemap: BaseMapType) => void;
  setSelectedFeatureId: (id: string | null) => void;
  setSelectedFeature: (feature: MapFeatureDetails | null) => void;
  setSelectedRouteId: (id: string | null) => void;
  setMapLoaded: (loaded: boolean) => void;
  flyToLocation: (lng: number, lat: number, zoom?: number) => void;
  resetToBeasCatchment: () => void;
}

// Upper Beas Basin bounding coordinates: 31.40°N–32.45°N, 76.80°E–77.45°E
export const BEAS_CATCHMENT_CENTER: [number, number] = [77.1887, 32.2396];
export const BEAS_CATCHMENT_BOUNDS: [[number, number], [number, number]] = [
  [76.90, 31.60],
  [77.40, 32.40],
];

export const useMapStore = create<MapState>((set) => ({
  center: BEAS_CATCHMENT_CENTER,
  zoom: 11.2,
  pitch: 40,
  bearing: -10,
  mapLoaded: false,
  selectedFeatureId: null,
  selectedFeature: null,
  selectedRouteId: null,
  hazardOpacity: 0.65,
  activeBasemap: 'hybrid', // Satellite imagery + clear town/road labels
  layers: {
    naturalDams: true,
    criticalZones: true,
    floodRisk: true,
    landslideRisk: true,
    riverNetwork: true,
    infrastructure: false,
    safeHavens: true,
    evacuationRoutes: true,
    sensorStations: true,
    radarOverlay: false,
  },

  setViewport: (center, zoom, pitch = 40, bearing = -10) =>
    set({ center, zoom, pitch, bearing }),

  toggleLayer: (layerKey) =>
    set((state) => ({
      layers: { ...state.layers, [layerKey]: !state.layers[layerKey] },
    })),

  setLayer: (layerKey, enabled) =>
    set((state) => ({
      layers: { ...state.layers, [layerKey]: enabled },
    })),

  setHazardOpacity: (hazardOpacity) => set({ hazardOpacity }),

  setActiveBasemap: (activeBasemap) => set({ activeBasemap }),

  setSelectedFeatureId: (id) => set({ selectedFeatureId: id }),

  setSelectedFeature: (selectedFeature) =>
    set({
      selectedFeature,
      selectedFeatureId: selectedFeature ? selectedFeature.id : null,
    }),

  setSelectedRouteId: (selectedRouteId) =>
    set((state) => ({
      selectedRouteId,
      layers: {
        ...state.layers,
        evacuationRoutes: true,
        safeHavens: true,
      },
    })),

  setMapLoaded: (mapLoaded) => set({ mapLoaded }),

  flyToLocation: (arg1, arg2, zoom = 13.5) => {
    // Robust coordinate order auto-detection for Himachal/Upper Beas basin:
    // Longitude is ~76.8-77.5, Latitude is ~31.4-32.5.
    let lng = arg1;
    let lat = arg2;
    if (arg1 < 50 && arg2 > 50) {
      // Swapped: arg1 is latitude (~32), arg2 is longitude (~77)
      lat = arg1;
      lng = arg2;
    }
    set({ center: [lng, lat], zoom, pitch: 45 });
  },

  resetToBeasCatchment: () =>
    set({
      center: BEAS_CATCHMENT_CENTER,
      zoom: 11.2,
      pitch: 40,
      bearing: -10,
    }),
}));
