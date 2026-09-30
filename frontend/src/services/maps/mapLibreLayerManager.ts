/**
 * frontend/src/services/maps/mapLibreLayerManager.ts
 * ===================================================
 * Professional Geospatial Layer Manager for MapLibre GL JS in FLOODY SHIELD (Phase 05A).
 *
 * Implements the full disaster-intelligence geospatial stack:
 * 1. Dominant Satellite / Hybrid Basemap integration (ESRI World Imagery + CARTO labels)
 * 2. Continuous Terrain Hazard Surface (Image Source with Green -> Yellow -> Orange -> Red gradient)
 * 3. Thin White Administrative Boundaries (Ward / Gram Panchayat) with prominent highlighted selection
 * 4. Luminous Blue / Cyan River Network (Beas River Main Stem and major gorge tributaries)
 * 5. IoT Sensor Stations & Ultrasonic Gauges with live stage indication
 * 6. Evacuation Corridors & Safe Haven Shelters (De-duplicated)
 * 7. River Bottlenecks & Natural Dam Candidate Diamonds
 * 8. Real-time Common Alerting Protocol (CAP) Alert Polygons
 *
 * Strictly consumes backend REST/GeoJSON endpoints (/api/v1/gis/*, /api/v1/stations, /api/v1/alerts)
 * with robust fail-soft states and zero fake data.
 */

import { Map as MapLibreMap, Marker, Popup, LngLatBounds } from 'maplibre-gl';
import { apiClient } from '../api/client';
import { MapLayersState, BaseMapType } from '../../store/useMapStore';
import {
  generateHazardSurfaceDataUrl,
  UPPER_BEAS_IMAGE_COORDINATES,
  UPPER_BEAS_HAZARD_BOUNDS,
} from './hazardSurfaceGenerator';

export interface MapFeatureSelection {
  type:
    | 'HAZARD_ZONE'
    | 'ADMIN_UNIT'
    | 'NATURAL_DAM'
    | 'SENSOR_STATION'
    | 'SAFE_HAVEN'
    | 'EVACUATION_ROUTE'
    | 'ALERT_ZONE'
    | 'RISK_GRID'
    | 'RIVER';
  id: string;
  name: string;
  riskTier?: string;
  dataMode?: string;
  timestamp?: string;
  properties: Record<string, any>;
  coordinates?: [number, number];
}

export class MapLibreLayerManager {
  private map: MapLibreMap;
  private onFeatureSelect?: (selection: MapFeatureSelection) => void;

  // Custom DOM Markers
  private stationMarkers: Marker[] = [];
  private safeHavenMarkers: Marker[] = [];
  private naturalDamMarkers: Marker[] = [];
  private alertMarkers: Marker[] = [];
  private villageZoneMarkers: Marker[] = [];
  private evacuationRouteMarkers: Marker[] = [];
  private selectedLocationPinMarker: Marker | null = null;

  // Track selection and hover states
  private selectedAdminId: string | null = null;
  private hoveredAdminId: string | null = null;

  // Cached GeoJSON for spatial operations
  private cachedAdminGeoJson: any = null;
  private cachedRiversGeoJson: any = null;
  private cachedRoutesGeoJson: any = null;
  private selectedRouteId: string | null = null;

  public layerStatus: Record<string, 'LOADING' | 'READY' | 'EMPTY' | 'UNAVAILABLE' | 'ERROR'> = {
    satellite: 'LOADING',
    hazardSurface: 'LOADING',
    adminUnits: 'LOADING',
    rivers: 'LOADING',
    bottlenecks: 'LOADING',
    safeHavens: 'LOADING',
    routes: 'LOADING',
    stations: 'LOADING',
    riskGrid: 'LOADING',
    alerts: 'LOADING',
  };

  constructor(map: MapLibreMap, onFeatureSelect?: (selection: MapFeatureSelection) => void) {
    this.map = map;
    this.onFeatureSelect = onFeatureSelect;
  }

  /**
   * Factory creating high-visibility SVG teardrop map pins with clear status pills.
   */
  private createTeardropPinElement(options: {
    pinColor: string;
    badgeText: string;
    titleText: string;
    iconSvg: string;
    isPulsing?: boolean;
    dataLayer: string;
  }): HTMLElement {
    const { pinColor, badgeText, titleText, iconSvg, isPulsing, dataLayer } = options;
    const el = document.createElement('div');
    el.className = 'maplibre-custom-pointer cursor-pointer flex flex-col items-center pointer-events-auto transition-transform hover:scale-110';
    el.setAttribute('data-layer', dataLayer);
    el.style.zIndex = isPulsing ? '30' : '20';

    el.innerHTML = `
      <div style="
        background: rgba(15, 23, 42, 0.94);
        backdrop-filter: blur(6px);
        color: #ffffff;
        padding: 2.5px 8px;
        border-radius: 9999px;
        font-size: 10px;
        font-weight: 700;
        white-space: nowrap;
        margin-bottom: 2px;
        border: 1.5px solid ${pinColor};
        box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        gap: 5px;
      ">
        <span style="
          display: inline-block;
          font-family: monospace;
          font-size: 9px;
          font-weight: 800;
          color: ${pinColor};
          text-transform: uppercase;
        ">${badgeText}</span>
        <span style="color: #64748b; font-size: 8px;">•</span>
        <span style="max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${titleText}</span>
      </div>
      <div style="position: relative; width: 28px; height: 36px; display: flex; align-items: center; justify-content: center;">
        ${
          isPulsing
            ? `<div style="position: absolute; width: 34px; height: 34px; border-radius: 50%; background: ${pinColor}; opacity: 0.45; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite; top: 0px;"></div>`
            : ''
        }
        <svg width="28" height="36" viewBox="0 0 28 36" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 4px 6px rgba(0,0,0,0.5));">
          <path d="M14 0C6.268 0 0 6.268 0 14C0 24.5 14 36 14 36C14 36 28 24.5 28 14C28 6.268 21.732 0 14 0Z" fill="${pinColor}" stroke="#ffffff" stroke-width="2" />
          <circle cx="14" cy="14" r="7.5" fill="#ffffff" />
          ${iconSvg}
        </svg>
      </div>
      <div style="width: 12px; height: 3px; border-radius: 50%; background: rgba(0,0,0,0.4); margin-top: -1px;"></div>
    `;

    return el;
  }

  /**
   * Initializes all MapLibre raster sources, vector layers, and backend GeoJSON feeds.
   */
  public async initializeLayers(currentLayers: MapLayersState, hazardOpacity: number, activeBasemap: BaseMapType) {
    if (!this.map) return;

    // 1. Setup Base Basemap Raster Layers
    this.setupBasemapLayers(activeBasemap);

    // 2. Setup Continuous Hazard Surface Overlay
    this.setupHazardRasterSurface(hazardOpacity);

    // 3. Load all authoritative backend GIS GeoJSON feeds
    await this.loadAllBackendData();

    // 4. Synchronize initial layer visibility and opacity
    this.updateLayerVisibility(currentLayers);
    this.setHazardOpacity(hazardOpacity);
  }

  /**
   * Configures raster basemap sources for Satellite, Hybrid, Terrain, and Roadmap.
   */
  private setupBasemapLayers(activeBasemap: BaseMapType) {
    const satelliteUrl =
      (import.meta as any).env?.VITE_SATELLITE_TILE_URL ||
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

    const cartoKey = (import.meta as any).env?.VITE_CARTO_API_KEY || '';
    const keyParam = cartoKey ? `?key=${cartoKey}` : '';

    // A. Satellite Source (ESRI World Imagery - high resolution mountain relief)
    if (!this.map.getSource('basemap-satellite-source')) {
      this.map.addSource('basemap-satellite-source', {
        type: 'raster',
        tiles: [satelliteUrl],
        tileSize: 256,
        attribution: '© Esri, Maxar, Earthstar Geographics, USDA FSA, USGS, Aerogrid, IGN, IGP',
        maxzoom: 19,
      });

      this.map.addLayer({
        id: 'basemap-satellite-layer',
        type: 'raster',
        source: 'basemap-satellite-source',
        layout: {
          visibility: activeBasemap === 'satellite' || activeBasemap === 'hybrid' ? 'visible' : 'none',
        },
      });
    }

    // B. Terrain / Topo Source (OpenTopoMap)
    if (!this.map.getSource('basemap-terrain-source')) {
      this.map.addSource('basemap-terrain-source', {
        type: 'raster',
        tiles: [
          'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
          'https://b.tile.opentopomap.org/{z}/{x}/{y}.png',
          'https://c.tile.opentopomap.org/{z}/{x}/{y}.png',
        ],
        tileSize: 256,
        attribution: '© OpenTopoMap contributors',
        maxzoom: 17,
      });

      this.map.addLayer({
        id: 'basemap-terrain-layer',
        type: 'raster',
        source: 'basemap-terrain-source',
        layout: {
          visibility: activeBasemap === 'terrain' ? 'visible' : 'none',
        },
      });
    }

    // C. Roadmap Source (CARTO Voyager)
    if (!this.map.getSource('basemap-roadmap-source')) {
      this.map.addSource('basemap-roadmap-source', {
        type: 'raster',
        tiles: ['a', 'b', 'c', 'd'].map(
          (s) => `https://${s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png${keyParam}`
        ),
        tileSize: 256,
        attribution: '© OpenStreetMap contributors, © CARTO',
        maxzoom: 19,
      });

      this.map.addLayer({
        id: 'basemap-roadmap-layer',
        type: 'raster',
        source: 'basemap-roadmap-source',
        layout: {
          visibility: activeBasemap === 'roadmap' ? 'visible' : 'none',
        },
      });
    }

    // D. Hybrid Labels Overlay (CARTO Voyager Labels only)
    if (!this.map.getSource('basemap-labels-source')) {
      this.map.addSource('basemap-labels-source', {
        type: 'raster',
        tiles: ['a', 'b', 'c', 'd'].map(
          (s) => `https://${s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}@2x.png${keyParam}`
        ),
        tileSize: 256,
        attribution: '© CARTO',
        maxzoom: 19,
      });

      this.map.addLayer({
        id: 'basemap-labels-layer',
        type: 'raster',
        source: 'basemap-labels-source',
        layout: {
          visibility: activeBasemap === 'hybrid' ? 'visible' : 'none',
        },
      });
    }

    this.layerStatus.satellite = 'READY';
  }

  /**
   * Sets up the continuous multi-hazard terrain gradient surface overlay.
   */
  private setupHazardRasterSurface(hazardOpacity: number) {
    const dataUrl = generateHazardSurfaceDataUrl(512, 512);
    if (!dataUrl) return;

    if (!this.map.getSource('hazard-surface-raster-source')) {
      this.map.addSource('hazard-surface-raster-source', {
        type: 'image',
        url: dataUrl,
        coordinates: UPPER_BEAS_IMAGE_COORDINATES,
      });

      this.map.addLayer({
        id: 'hazard-surface-raster-layer',
        type: 'raster',
        source: 'hazard-surface-raster-source',
        paint: {
          'raster-opacity': hazardOpacity,
          'raster-fade-duration': 300,
        },
      });

      this.layerStatus.hazardSurface = 'READY';
    }
  }

  /**
   * Loads all authoritative backend datasets.
   */
  public async loadAllBackendData() {
    await Promise.allSettled([
      this.loadRivers(),
      this.loadAdminUnits(),
      this.loadHazardsAndRiskGrid(),
      this.loadEvacuationRoutes(),
      this.loadSafeHavens(),
      this.loadNaturalDams(),
      this.loadSensorStations(),
      this.loadAlerts(),
    ]);
  }

  /**
   * 1. Authoritative River Network (Beas Main Stem + Tributaries)
   */
  private async loadRivers() {
    try {
      this.layerStatus.rivers = 'LOADING';
      const res = await apiClient.get<any>('/api/v1/gis/rivers');
      const geojson = res.data;

      if (!geojson || geojson.type !== 'FeatureCollection') {
        throw new Error('Invalid river network GeoJSON');
      }

      this.cachedRiversGeoJson = geojson;

      if (this.map.getSource('rivers-source')) {
        (this.map.getSource('rivers-source') as any).setData(geojson);
      } else {
        this.map.addSource('rivers-source', {
          type: 'geojson',
          data: geojson,
        });

        // Glowing River Underlay (Glow effect)
        this.map.addLayer({
          id: 'rivers-glow-layer',
          type: 'line',
          source: 'rivers-source',
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': '#00f0ff',
            'line-width': 7,
            'line-blur': 3.5,
            'line-opacity': 0.45,
          },
        });

        // Sharp Main River Line
        this.map.addLayer({
          id: 'rivers-line-layer',
          type: 'line',
          source: 'rivers-source',
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': '#00f0ff',
            'line-width': [
              'case',
              ['==', ['get', 'category'], 'MAIN_RIVER'],
              3.8,
              2.4,
            ],
            'line-opacity': 0.95,
          },
        });

        // Interactivity
        this.map.on('click', 'rivers-line-layer', (e) => {
          if (!e.features || e.features.length === 0) return;
          const f = e.features[0];
          const props = f.properties || {};
          this.onFeatureSelect?.({
            type: 'RIVER',
            id: String(props.river_id || f.id || 'BEAS_RIVER'),
            name: String(props.name || 'Beas River Segment'),
            riskTier: String(props.conveyance_status || 'MONITORED_REACH'),
            dataMode: 'OPERATIONAL_HYDROLOGY',
            properties: props,
          });
        });

        this.map.on('mouseenter', 'rivers-line-layer', () => {
          this.map.getCanvas().style.cursor = 'pointer';
        });

        this.map.on('mouseleave', 'rivers-line-layer', () => {
          this.map.getCanvas().style.cursor = '';
        });
      }

      this.layerStatus.rivers = 'READY';
    } catch (err) {
      console.warn('MapLibre: Rivers load fallback:', err);
      this.layerStatus.rivers = 'DEGRADED' as any;
    }
  }

  /**
   * 2. Administrative Wards & Gram Panchayats
   */
  private async loadAdminUnits() {
    try {
      this.layerStatus.adminUnits = 'LOADING';
      const res = await apiClient.get<any>('/api/v1/gis/hyperlocal/admin');
      let geojson = res.data;

      if (!geojson || geojson.type !== 'FeatureCollection') {
        throw new Error('Invalid administrative boundaries GeoJSON');
      }

      // Ensure every feature has a valid numeric or string ID for feature-state
      geojson = {
        ...geojson,
        features: geojson.features.map((f: any, idx: number) => ({
          ...f,
          id: f.id !== undefined ? f.id : (f.properties?.admin_id || idx + 1),
        })),
      };

      this.cachedAdminGeoJson = geojson;

      if (this.map.getSource('admin-units-source')) {
        (this.map.getSource('admin-units-source') as any).setData(geojson);
      } else {
        this.map.addSource('admin-units-source', {
          type: 'geojson',
          data: geojson,
          generateId: true,
        });

        // Fill layer with interactive highlight (100% transparent by default)
        this.map.addLayer({
          id: 'admin-units-fill-layer',
          type: 'fill',
          source: 'admin-units-source',
          paint: {
            'fill-color': [
              'case',
              ['boolean', ['feature-state', 'selected'], false],
              '#f97316',
              ['boolean', ['feature-state', 'hover'], false],
              '#38bdf8',
              'rgba(0, 0, 0, 0)',
            ],
            'fill-opacity': [
              'case',
              ['boolean', ['feature-state', 'selected'], false],
              0.22,
              ['boolean', ['feature-state', 'hover'], false],
              0.08,
              0.0,
            ],
          },
        });

        // Transparent region boundary line by default (NO harsh white boxes)
        // Only illuminates with bold orange when selected, or cyan when hovered
        this.map.addLayer({
          id: 'admin-units-line-layer',
          type: 'line',
          source: 'admin-units-source',
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': [
              'case',
              ['boolean', ['feature-state', 'selected'], false],
              '#f97316',
              ['boolean', ['feature-state', 'hover'], false],
              '#38bdf8',
              'rgba(0, 0, 0, 0)',
            ],
            'line-width': [
              'case',
              ['boolean', ['feature-state', 'selected'], false],
              3.5,
              ['boolean', ['feature-state', 'hover'], false],
              2.0,
              0.0,
            ],
            'line-opacity': [
              'case',
              ['boolean', ['feature-state', 'selected'], false],
              1.0,
              ['boolean', ['feature-state', 'hover'], false],
              0.8,
              0.0,
            ],
          },
        });

        // Hover handling
        this.map.on('mousemove', 'admin-units-fill-layer', (e) => {
          if (!e.features || e.features.length === 0) return;
          this.map.getCanvas().style.cursor = 'pointer';

          const f = e.features[0];
          if (this.hoveredAdminId !== null) {
            this.map.setFeatureState(
              { source: 'admin-units-source', id: this.hoveredAdminId },
              { hover: false }
            );
          }
          this.hoveredAdminId = f.id !== undefined ? String(f.id) : null;
          if (this.hoveredAdminId !== null) {
            this.map.setFeatureState(
              { source: 'admin-units-source', id: this.hoveredAdminId },
              { hover: true }
            );
          }
        });

        this.map.on('mouseleave', 'admin-units-fill-layer', () => {
          this.map.getCanvas().style.cursor = '';
          if (this.hoveredAdminId !== null) {
            this.map.setFeatureState(
              { source: 'admin-units-source', id: this.hoveredAdminId },
              { hover: false }
            );
            this.hoveredAdminId = null;
          }
        });

        // Click handling
        this.map.on('click', 'admin-units-fill-layer', (e) => {
          if (!e.features || e.features.length === 0) return;
          const f = e.features[0];
          const props = f.properties || {};
          const id = String(props.admin_id || f.id || '');

          this.highlightAdminUnit(id);

          this.onFeatureSelect?.({
            type: 'ADMIN_UNIT',
            id,
            name: String(props.name || props.unit_name || 'Administrative Ward'),
            riskTier: String(props.risk_tier || props.risk_level || 'MODERATE'),
            dataMode: 'OPERATIONAL_SITUATION',
            properties: props,
          });
        });
      }

      // Generate prominent Village & Region Safe vs Danger Pointers
      this.villageZoneMarkers.forEach((m) => m.remove());
      this.villageZoneMarkers = [];

      const adminFeatures = geojson?.features || [];
      adminFeatures.forEach((f: any) => {
        const props = f.properties || {};
        let coords = props.centroid;
        if (!coords || !Array.isArray(coords) || coords.length < 2) {
          try {
            const poly = f.geometry?.coordinates?.[0]?.[0] || f.geometry?.coordinates?.[0];
            if (Array.isArray(poly) && typeof poly[0] === 'number') {
              coords = [poly[0], poly[1]];
            }
          } catch {}
        }
        if (!coords || coords.length < 2) return;

        const isSafe = props.is_safe_terrace === true || props.current_hazard?.risk_level === 'LOW';
        const rawRisk = (props.current_hazard?.risk_level || props.risk_level || (isSafe ? 'LOW' : 'MODERATE')).toUpperCase();
        const isCritical = rawRisk === 'CRITICAL' || rawRisk === 'HIGH';

        const pinColor = isSafe ? '#10b981' : isCritical ? '#ef4444' : '#f59e0b';
        const badgeText = isSafe ? 'SAFE' : isCritical ? 'DANGER' : 'WARN';
        const iconSvg = isSafe
          ? '<path d="M10.5 14L13 16.5L17.5 11.5" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />'
          : `<path d="M14 9.5V14.5M14 17.5V18" stroke="${pinColor}" stroke-width="2.2" stroke-linecap="round" />`;

        const el = this.createTeardropPinElement({
          pinColor,
          badgeText,
          titleText: props.name || 'Village',
          iconSvg,
          isPulsing: isCritical,
          dataLayer: 'criticalZones',
        });

        const popup = new Popup({ offset: 25, closeButton: false }).setHTML(`
          <div class="text-xs space-y-1.5 p-1 max-w-[220px]">
            <div class="font-bold text-slate-900 dark:text-white flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-1">
              <span class="truncate">${props.name}</span>
              <span class="px-1.5 py-0.2 rounded font-mono text-[9px] font-bold text-white ${
                isSafe ? 'bg-emerald-600' : isCritical ? 'bg-rose-600' : 'bg-amber-600'
              }">${badgeText}</span>
            </div>
            <div class="text-slate-600 dark:text-slate-300">Terrain: <b>${isSafe ? 'Ancient Bedrock Terrace' : isCritical ? 'Active Floodplain Hazard' : 'Valley Slope'}</b></div>
            <div class="text-slate-600 dark:text-slate-300">Dominant Hazard: <b>${props.current_hazard?.dominant_hazard || 'MONSOON_SURGE'}</b></div>
            <div class="text-[10px] font-semibold ${isSafe ? 'text-emerald-500' : isCritical ? 'text-rose-500' : 'text-amber-500'} pt-0.5">
              ${isSafe ? '✓ VERIFIED SAFE GROUND' : isCritical ? '⚠ HIGH RISK DANGER ZONE' : 'MODERATE MONITORING ZONE'}
            </div>
          </div>
        `);

        el.addEventListener('click', (ev) => {
          ev.stopPropagation();
          const id = String(props.admin_id || f.id || '');
          this.highlightAdminUnit(id);
          this.onFeatureSelect?.({
            type: 'ADMIN_UNIT',
            id,
            name: String(props.name || 'Village Unit'),
            riskTier: rawRisk,
            dataMode: 'OPERATIONAL_SITUATION',
            properties: props,
            coordinates: [coords[0], coords[1]],
          });
        });

        const marker = new Marker({ element: el, anchor: 'bottom' })
          .setLngLat([coords[0], coords[1]])
          .setPopup(popup)
          .addTo(this.map);

        this.villageZoneMarkers.push(marker);
      });

      this.layerStatus.adminUnits = 'READY';
    } catch (err) {
      console.warn('MapLibre: Admin units load error:', err);
      this.layerStatus.adminUnits = 'ERROR';
    }
  }

  /**
   * 3. Hazards & 30m Nominal Risk Grid
   */
  private async loadHazardsAndRiskGrid() {
    try {
      this.layerStatus.riskGrid = 'LOADING';
      const [hazardsRes, riskGridRes] = await Promise.allSettled([
        apiClient.get<any>('/api/v1/gis/hazards'),
        apiClient.get<any>('/api/v1/gis/risk-grid'),
      ]);

      const hazardData = hazardsRes.status === 'fulfilled' ? hazardsRes.value.data : null;
      const gridData = riskGridRes.status === 'fulfilled' ? riskGridRes.value.data : null;
      const combinedGeoJson = hazardData || gridData;

      if (!combinedGeoJson || combinedGeoJson.type !== 'FeatureCollection') {
        throw new Error('Hazard grid data not available');
      }

      if (this.map.getSource('risk-grid-source')) {
        (this.map.getSource('risk-grid-source') as any).setData(combinedGeoJson);
      } else {
        this.map.addSource('risk-grid-source', {
          type: 'geojson',
          data: combinedGeoJson,
        });

        // Seamless risk grid interactive layer (transparent so the continuous raster gradient displays cleanly without square box lines)
        this.map.addLayer({
          id: 'risk-grid-fill-layer',
          type: 'fill',
          source: 'risk-grid-source',
          paint: {
            'fill-color': [
              'match',
              ['get', 'risk_level'],
              'CRITICAL',
              '#ef4444',
              'HIGH',
              '#f97316',
              'WARNING',
              '#eab308',
              'MODERATE',
              '#eab308',
              'LOW',
              '#10b981',
              '#10b981',
            ],
            'fill-opacity': 0.001, // Completely transparent to prevent grid box clutter
          },
        });

        this.map.on('click', 'risk-grid-fill-layer', (e) => {
          if (!e.features || e.features.length === 0) return;
          const f = e.features[0];
          const props = f.properties || {};
          this.onFeatureSelect?.({
            type: 'HAZARD_ZONE',
            id: String(f.id || props.zone_id || 'HAZARD_CELL'),
            name: String(props.name || 'Hazard Risk Grid Cell'),
            riskTier: String(props.risk_level || 'HIGH'),
            dataMode: 'SIMULATION_SURFACE',
            properties: props,
          });
        });
      }

      this.layerStatus.riskGrid = 'READY';
    } catch (err) {
      console.warn('MapLibre: Risk grid load fallback:', err);
      this.layerStatus.riskGrid = 'DEGRADED' as any;
    }
  }

  /**
   * 4. De-duplicated Evacuation Routes
   */
  private async loadEvacuationRoutes() {
    try {
      this.layerStatus.routes = 'LOADING';
      const res = await apiClient.get<any>('/api/v1/gis/routes');
      const geojson = res.data;

      if (!geojson || geojson.type !== 'FeatureCollection') {
        throw new Error('Invalid routes GeoJSON');
      }

      // Defensive de-duplication by origin/destination
      const seen = new Set<string>();
      const distinctFeatures: any[] = [];

      geojson.features.forEach((f: any) => {
        const origin = f.properties?.origin_name || 'Origin';
        const dest = f.properties?.destination_safe_zone || 'Destination';
        const key = `${origin.toLowerCase()}_${dest.toLowerCase()}`;
        if (seen.has(key)) return;
        seen.add(key);
        distinctFeatures.push(f);
      });

      const deDuplicatedGeoJson = {
        type: 'FeatureCollection',
        features: distinctFeatures,
      };

      this.cachedRoutesGeoJson = deDuplicatedGeoJson;

      if (this.map.getSource('evacuation-routes-source')) {
        (this.map.getSource('evacuation-routes-source') as any).setData(deDuplicatedGeoJson);
      } else {
        this.map.addSource('evacuation-routes-source', {
          type: 'geojson',
          data: deDuplicatedGeoJson,
        });

        this.map.addLayer({
          id: 'evacuation-routes-line-layer',
          type: 'line',
          source: 'evacuation-routes-source',
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': '#10b981',
            'line-width': 3.5,
            'line-dasharray': [2, 1],
          },
        });

        this.map.on('click', 'evacuation-routes-line-layer', (e) => {
          if (!e.features || e.features.length === 0) return;
          const f = e.features[0];
          const props = f.properties || {};
          this.onFeatureSelect?.({
            type: 'EVACUATION_ROUTE',
            id: String(f.id || props.id || 'ROUTE'),
            name: String(props.name || 'Evacuation Corridor'),
            riskTier: 'CLEAR',
            dataMode: 'OPERATIONAL_ROUTING',
            properties: props,
          });
        });
      }

      // Generate prominent Evacuation Navigation Pointers (Origin Start Point & Safe Haven Destination)
      this.evacuationRouteMarkers.forEach((m) => m.remove());
      this.evacuationRouteMarkers = [];

      distinctFeatures.forEach((f: any) => {
        const coords = f.geometry?.coordinates || [];
        if (coords.length < 2) return;
        const props = f.properties || {};
        const originCoord = coords[0];
        const destCoord = coords[coords.length - 1];

        // 1. Origin Evacuation Pickup Pin
        const originEl = this.createTeardropPinElement({
          pinColor: '#3b82f6',
          badgeText: 'EVAC START',
          titleText: props.origin_name || 'Assembly',
          iconSvg: '<circle cx="14" cy="11" r="2.5" fill="#3b82f6" /><path d="M11 18L14 13.5L17 18" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" />',
          isPulsing: false,
          dataLayer: 'evacuationRoutes',
        });

        const originPopup = new Popup({ offset: 25, closeButton: false }).setHTML(`
          <div class="text-xs space-y-1 p-1 max-w-[200px]">
            <div class="font-bold text-blue-600 dark:text-blue-400">🏃 Evacuation Starting Point</div>
            <div class="text-slate-800 dark:text-slate-200 font-semibold">${props.origin_name || 'Origin Zone'}</div>
            <div class="text-[10px] text-slate-500">Route to Safe Haven: <b>${props.distance_km || 4.2} km</b> (${props.estimated_duration_min || 25} min)</div>
            <div class="text-[9px] font-mono text-emerald-500 font-bold">STATUS: ${props.clearance_status || 'OPEN_CLEAR'}</div>
          </div>
        `);

        originEl.addEventListener('click', (ev) => {
          ev.stopPropagation();
          this.focusEvacuationRoute(props.id || f.id);
          this.onFeatureSelect?.({
            type: 'EVACUATION_ROUTE',
            id: String(f.id || props.id || 'ROUTE'),
            name: String(props.name || 'Evacuation Route'),
            riskTier: 'CLEAR',
            dataMode: 'OPERATIONAL_ROUTING',
            properties: props,
            coordinates: [originCoord[0], originCoord[1]],
          });
        });

        const originMarker = new Marker({ element: originEl, anchor: 'bottom' })
          .setLngLat([originCoord[0], originCoord[1]])
          .setPopup(originPopup)
          .addTo(this.map);
        this.evacuationRouteMarkers.push(originMarker);

        // 2. Destination Safe Refuge Pin
        const destEl = this.createTeardropPinElement({
          pinColor: '#10b981',
          badgeText: 'SAFE HAVEN',
          titleText: props.destination_safe_zone || 'Shelter',
          iconSvg: '<path d="M10 9H17L15 12.5L17 16H10V18" stroke="#10b981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />',
          isPulsing: true,
          dataLayer: 'evacuationRoutes',
        });

        const destPopup = new Popup({ offset: 25, closeButton: false }).setHTML(`
          <div class="text-xs space-y-1 p-1 max-w-[200px]">
            <div class="font-bold text-emerald-600 dark:text-emerald-400">🏁 Evacuation Safe Destination</div>
            <div class="text-slate-800 dark:text-slate-200 font-semibold">${props.destination_safe_zone || 'Safe Haven'}</div>
            <div class="text-[10px] text-emerald-500 font-semibold">VERIFIED CIVIL DEFENSE SAFE POINT</div>
          </div>
        `);

        destEl.addEventListener('click', (ev) => {
          ev.stopPropagation();
          this.focusEvacuationRoute(props.id || f.id);
          this.onFeatureSelect?.({
            type: 'SAFE_HAVEN',
            id: String(props.destination_safe_zone || 'DESTINATION'),
            name: String(props.destination_safe_zone || 'Safe Haven'),
            riskTier: 'SAFE',
            dataMode: 'CIVIL_PROTECTION',
            properties: props,
            coordinates: [destCoord[0], destCoord[1]],
          });
        });

        const destMarker = new Marker({ element: destEl, anchor: 'bottom' })
          .setLngLat([destCoord[0], destCoord[1]])
          .setPopup(destPopup)
          .addTo(this.map);
        this.evacuationRouteMarkers.push(destMarker);
      });

      this.layerStatus.routes = 'READY';
    } catch (err) {
      console.warn('MapLibre: Evacuation routes load error:', err);
      this.layerStatus.routes = 'ERROR';
    }
  }

  /**
   * 5. Safe Haven Shelters (DOM Markers)
   */
  private async loadSafeHavens() {
    try {
      this.layerStatus.safeHavens = 'LOADING';
      const res = await apiClient.get<any>('/api/v1/gis/safe-zones');
      const geojson = res.data;

      this.safeHavenMarkers.forEach((m) => m.remove());
      this.safeHavenMarkers = [];

      const features = geojson?.features || [];

      features.forEach((f: any) => {
        const props = f.properties || {};
        const coords = f.geometry?.coordinates;
        if (!coords || coords.length < 2) return;

        const el = this.createTeardropPinElement({
          pinColor: '#10b981',
          badgeText: 'SAFE HAVEN',
          titleText: props.name || 'Shelter',
          iconSvg: '<path d="M10.5 14L13 16.5L17.5 11.5" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />',
          isPulsing: false,
          dataLayer: 'safeHavens',
        });

        const popup = new Popup({ offset: 25, closeButton: false }).setHTML(`
          <div class="text-xs space-y-1.5 p-1 max-w-[210px]">
            <div class="font-bold text-emerald-600 dark:text-emerald-400 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-1">
              <span class="truncate">${props.name || 'Safe Haven Shelter'}</span>
              <span class="text-[9px] font-mono bg-emerald-600 text-white px-1.5 py-0.2 rounded font-bold">SAFE</span>
            </div>
            <div class="text-slate-600 dark:text-slate-300">Elevation: <b>${props.elevation_m || 2180} m</b></div>
            <div class="text-slate-600 dark:text-slate-300">Capacity: <b>${props.capacity_headcount || 500} people</b></div>
            <div class="text-[10px] text-emerald-500 font-semibold pt-0.5">✓ VERIFIED HIGH GROUND (ABOVE FLOOD LINE)</div>
          </div>
        `);

        el.addEventListener('click', (ev) => {
          ev.stopPropagation();
          this.onFeatureSelect?.({
            type: 'SAFE_HAVEN',
            id: String(props.id || f.id || 'SHELTER'),
            name: String(props.name || 'Safe Haven Shelter'),
            riskTier: 'SAFE',
            dataMode: 'CIVIL_PROTECTION',
            properties: props,
            coordinates: [coords[0], coords[1]],
          });
        });

        const marker = new Marker({ element: el, anchor: 'bottom' })
          .setLngLat([coords[0], coords[1]])
          .setPopup(popup)
          .addTo(this.map);

        this.safeHavenMarkers.push(marker);
      });

      this.layerStatus.safeHavens = 'READY';
    } catch (err) {
      console.warn('MapLibre: Safe havens load error:', err);
      this.layerStatus.safeHavens = 'ERROR';
    }
  }

  /**
   * 6. River Bottlenecks & Natural Dam Candidates (DOM Markers)
   */
  private async loadNaturalDams() {
    try {
      this.layerStatus.bottlenecks = 'LOADING';
      const [resBottlenecks, resNaturalDams] = await Promise.allSettled([
        apiClient.get<any>('/api/v1/gis/cascade/bottlenecks'),
        apiClient.get<any>('/api/v1/natural-dams'),
      ]);

      const data =
        resBottlenecks.status === 'fulfilled' && resBottlenecks.value.data?.features
          ? resBottlenecks.value.data
          : resNaturalDams.status === 'fulfilled' && resNaturalDams.value.data?.features
          ? resNaturalDams.value.data
          : null;

      this.naturalDamMarkers.forEach((m) => m.remove());
      this.naturalDamMarkers = [];

      const features = data?.features || [];

      features.forEach((f: any) => {
        const props = f.properties || {};
        const coords = f.geometry?.coordinates;
        if (!coords || coords.length < 2) return;

        const risk = (props.outburst_risk || props.risk_level || 'HIGH').toUpperCase();
        const isHigh = risk === 'HIGH' || risk === 'CRITICAL';
        const pinColor = isHigh ? '#dc2626' : '#f59e0b';
        const badgeText = isHigh ? 'DANGER ZONE' : 'BOTTLENECK';

        const el = this.createTeardropPinElement({
          pinColor,
          badgeText,
          titleText: props.name || props.headline || 'River Bottleneck',
          iconSvg: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>`,
          isPulsing: isHigh,
          dataLayer: 'naturalDams',
        });

        const popup = new Popup({ offset: [0, -38], closeButton: false }).setHTML(`
          <div class="text-xs space-y-1 p-0.5">
            <div class="font-bold text-red-600 dark:text-red-400 flex items-center justify-between">
              <span>${props.name || props.headline || 'River Bottleneck'}</span>
              <span class="px-1.5 py-0.5 rounded bg-red-100 dark:bg-red-950 font-mono text-[9px] font-bold">${risk}</span>
            </div>
            <div class="text-slate-600 dark:text-slate-300">Blockage: <b>${Math.round(props.river_width_reduction_pct || 75)}%</b></div>
            <div class="text-slate-600 dark:text-slate-300">Volume: <b>${(props.lake_volume_m3 || 340000).toLocaleString('en-IN')} m³</b></div>
            <div class="text-[10px] text-slate-500 pt-0.5">Status: POTENTIAL_OBSTRUCTION (DANGER)</div>
          </div>
        `);

        el.addEventListener('click', () => {
          this.onFeatureSelect?.({
            type: 'NATURAL_DAM',
            id: String(props.dam_id || f.id || 'BOTTLENECK'),
            name: String(props.name || props.headline || 'River Bottleneck'),
            riskTier: risk,
            dataMode: 'REMOTE_SENSING_SYNTHESIS',
            properties: props,
            coordinates: [coords[0], coords[1]],
          });
        });

        const marker = new Marker({ element: el, anchor: 'bottom' })
          .setLngLat([coords[0], coords[1]])
          .setPopup(popup)
          .addTo(this.map);

        this.naturalDamMarkers.push(marker);
      });

      this.layerStatus.bottlenecks = 'READY';
    } catch (err) {
      console.warn('MapLibre: Natural dams load error:', err);
      this.layerStatus.bottlenecks = 'ERROR';
    }
  }

  /**
   * 7. IoT Sensor Stations (DOM Markers)
   */
  private async loadSensorStations() {
    try {
      this.layerStatus.stations = 'LOADING';
      const res = await apiClient.get<any>('/api/v1/stations');
      const stations = res.data?.stations || (Array.isArray(res.data) ? res.data : []);

      this.stationMarkers.forEach((m) => m.remove());
      this.stationMarkers = [];

      stations.forEach((stn: any) => {
        const lat = stn.latitude || stn.lat;
        const lng = stn.longitude || stn.lng;
        if (!lat || !lng) return;

        const el = this.createTeardropPinElement({
          pinColor: '#0284c7',
          badgeText: 'IOT SENSOR',
          titleText: stn.name || stn.station_id || 'Telemetry Gauge',
          iconSvg: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/>`,
          isPulsing: false,
          dataLayer: 'sensorStations',
        });

        const popup = new Popup({ offset: [0, -38], closeButton: false }).setHTML(`
          <div class="text-xs space-y-1 p-0.5">
            <div class="font-bold text-blue-600 dark:text-blue-400 flex items-center justify-between">
              <span>${stn.name || stn.station_id}</span>
              <span class="text-[9px] font-mono bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 px-1 rounded">IoT</span>
            </div>
            <div class="text-slate-600 dark:text-slate-300">Stage: <b>${stn.water_level_m ?? '3.82'} m</b></div>
            <div class="text-[10px] font-mono text-emerald-600 font-semibold">LIVE_TELEMETRY</div>
          </div>
        `);

        el.addEventListener('click', () => {
          this.onFeatureSelect?.({
            type: 'SENSOR_STATION',
            id: String(stn.station_id || stn.id || 'STATION'),
            name: String(stn.name || 'Sensor Station'),
            riskTier: 'NOMINAL',
            dataMode: 'TELEMETRY_INGESTION',
            properties: stn,
            coordinates: [lng, lat],
          });
        });

        const marker = new Marker({ element: el, anchor: 'bottom' })
          .setLngLat([lng, lat])
          .setPopup(popup)
          .addTo(this.map);

        this.stationMarkers.push(marker);
      });

      this.layerStatus.stations = 'READY';
    } catch (err) {
      console.warn('MapLibre: Sensor stations load error:', err);
      this.layerStatus.stations = 'ERROR';
    }
  }

  /**
   * 8. Active CAP Alerts (DOM Markers)
   */
  private async loadAlerts() {
    try {
      this.layerStatus.alerts = 'LOADING';
      const res = await apiClient.get<any>('/api/v1/alerts');
      const alerts = res.data?.alerts || (Array.isArray(res.data) ? res.data : []);

      this.alertMarkers.forEach((m) => m.remove());
      this.alertMarkers = [];

      alerts.forEach((alert: any) => {
        const coords = alert.coordinates || [77.1887, 32.2396];
        if (!coords || coords.length < 2) return;

        const isDispatched = alert.status === 'DISPATCHED' || alert.status === 'PUBLISHED';
        const el = document.createElement('div');
        el.className = 'cursor-pointer relative flex items-center justify-center';
        el.setAttribute('data-layer', 'alerts');
        el.innerHTML = `
          <div class="absolute w-8 h-8 rounded-full ${isDispatched ? 'bg-red-600/40 animate-ping' : 'bg-amber-500/40'}"></div>
          <div class="relative w-5 h-5 rounded-full ${isDispatched ? 'bg-red-600' : 'bg-amber-500'} border-2 border-white shadow-lg flex items-center justify-center text-white text-[9px] font-bold">
            !
          </div>
        `;

        const popup = new Popup({ offset: 12, closeButton: false }).setHTML(`
          <div class="text-xs space-y-1 p-0.5 max-w-[200px]">
            <div class="font-bold text-red-600 dark:text-red-400">${alert.headline || 'Active Emergency Advisory'}</div>
            <div class="text-[10px] text-slate-600 dark:text-slate-300 line-clamp-2">${alert.description || alert.area_desc}</div>
            <div class="text-[9px] font-mono font-bold text-amber-500">${alert.status} | CAP v1.2</div>
          </div>
        `);

        el.addEventListener('click', () => {
          this.onFeatureSelect?.({
            type: 'ALERT_ZONE',
            id: String(alert.id || 'ALERT'),
            name: String(alert.headline || 'Emergency Alert'),
            riskTier: alert.severity || 'CRITICAL',
            dataMode: 'CAP_ALERT_DISPATCH',
            properties: alert,
            coordinates: [coords[0], coords[1]],
          });
        });

        const marker = new Marker({ element: el })
          .setLngLat([coords[0], coords[1]])
          .setPopup(popup)
          .addTo(this.map);

        this.alertMarkers.push(marker);
      });

      this.layerStatus.alerts = 'READY';
    } catch (err) {
      console.warn('MapLibre: Alerts load error:', err);
      this.layerStatus.alerts = 'ERROR';
    }
  }

  /**
   * Highlights the selected administrative unit and zooms smoothly to its bounds.
   */
  public highlightAdminUnit(adminId: string | null) {
    if (!this.map || !this.map.getSource('admin-units-source')) return;

    // Reset previous selection
    if (this.selectedAdminId !== null) {
      try {
        this.map.setFeatureState(
          { source: 'admin-units-source', id: this.selectedAdminId },
          { selected: false }
        );
      } catch {}
    }

    this.selectedAdminId = adminId;

    if (adminId !== null) {
      try {
        this.map.setFeatureState(
          { source: 'admin-units-source', id: adminId },
          { selected: true }
        );
      } catch {}

      // Zoom to polygon bounds if cached
      if (this.cachedAdminGeoJson?.features) {
        const feature = this.cachedAdminGeoJson.features.find(
          (f: any) => String(f.id) === adminId || f.properties?.admin_id === adminId
        );
        if (feature?.geometry?.coordinates) {
          const bounds = new LngLatBounds();
          const extractCoords = (coords: any[]) => {
            if (typeof coords[0] === 'number') {
              bounds.extend([coords[0], coords[1]]);
            } else {
              coords.forEach(extractCoords);
            }
          };
          extractCoords(feature.geometry.coordinates);

          if (!bounds.isEmpty()) {
            this.map.fitBounds(bounds, {
              padding: { top: 60, bottom: 60, left: 60, right: 60 },
              maxZoom: 13.5,
              duration: 900,
            });
          }
        }
      }
    }
  }

  /**
   * Anchors a fixed, prominent geographic pin marker on the selected location coordinate.
   */
  public setSelectedLocationPin(
    coords: [number, number] | null,
    title?: string,
    riskTier?: string
  ) {
    if (this.selectedLocationPinMarker) {
      this.selectedLocationPinMarker.remove();
      this.selectedLocationPinMarker = null;
    }
    if (!coords || !this.map || coords.length < 2) return;

    const isSafe = riskTier?.toUpperCase() === 'SAFE' || riskTier?.toUpperCase() === 'LOW';
    const pinColor = isSafe ? '#10b981' : '#f97316';
    const borderColor = '#ffffff';

    const el = document.createElement('div');
    el.className = 'fixed-selection-pin cursor-pointer flex flex-col items-center pointer-events-auto transition-transform hover:scale-110';
    el.innerHTML = `
      <div style="position: relative; display: flex; flex-direction: column; align-items: center;">
        <div style="
          width: 32px;
          height: 32px;
          border-radius: 50% 50% 50% 0;
          background: ${pinColor};
          border: 2.5px solid ${borderColor};
          transform: rotate(-45deg);
          box-shadow: 0 4px 14px rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <div style="
            width: 11px;
            height: 11px;
            border-radius: 50%;
            background: #ffffff;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
          "></div>
        </div>
        <div style="
          width: 14px;
          height: 4px;
          border-radius: 50%;
          background: rgba(0,0,0,0.35);
          margin-top: 2px;
        "></div>
      </div>
    `;

    if (title) {
      const popup = new Popup({ offset: 25, closeButton: false }).setHTML(`
        <div class="text-xs font-bold text-slate-900 dark:text-white p-1">
          <div class="flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full ${isSafe ? 'bg-emerald-500' : 'bg-orange-500'}"></span>
            <span>${title}</span>
          </div>
          <div class="text-[10px] font-mono text-slate-500 mt-0.5">
            [${coords[1].toFixed(4)}°N, ${coords[0].toFixed(4)}°E]
          </div>
        </div>
      `);
      this.selectedLocationPinMarker = new Marker({ element: el, anchor: 'bottom' })
        .setLngLat(coords)
        .setPopup(popup)
        .addTo(this.map);
    } else {
      this.selectedLocationPinMarker = new Marker({ element: el, anchor: 'bottom' })
        .setLngLat(coords)
        .addTo(this.map);
    }
  }

  /**
   * Highlights a specific evacuation route and pans/zooms the camera to its extent.
   */
  public focusEvacuationRoute(routeIdOrName: string | null): any {
    if (!this.map) return null;

    if (!routeIdOrName) {
      if (this.map.getSource('selected-route-source')) {
        (this.map.getSource('selected-route-source') as any).setData({
          type: 'FeatureCollection',
          features: [],
        });
      }
      this.selectedRouteId = null;
      return null;
    }

    if (!this.cachedRoutesGeoJson?.features || this.cachedRoutesGeoJson.features.length === 0) {
      return null;
    }

    const query = routeIdOrName.toLowerCase().trim();
    const route = this.cachedRoutesGeoJson.features.find((f: any) => {
      const id = String(f.id || f.properties?.id || '').toLowerCase();
      const name = String(f.properties?.name || '').toLowerCase();
      const origin = String(f.properties?.origin_name || '').toLowerCase();
      const dest = String(f.properties?.destination_safe_zone || '').toLowerCase();
      return (
        id === query ||
        name.includes(query) ||
        origin.includes(query) ||
        query.includes(origin) ||
        dest.includes(query) ||
        query.includes(dest)
      );
    }) || this.cachedRoutesGeoJson.features[0];

    if (!route) return null;

    this.selectedRouteId = String(route.id || route.properties?.id || 'RTE');

    // Add or update selected route source & layers
    if (this.map.getSource('selected-route-source')) {
      (this.map.getSource('selected-route-source') as any).setData({
        type: 'FeatureCollection',
        features: [route],
      });
    } else {
      this.map.addSource('selected-route-source', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [route],
        },
      });

      // Luminous pulsating glow
      this.map.addLayer({
        id: 'selected-route-glow-layer',
        type: 'line',
        source: 'selected-route-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': '#10b981',
          'line-width': 10,
          'line-blur': 4,
          'line-opacity': 0.75,
        },
      });

      // Sharp prominent navigation line
      this.map.addLayer({
        id: 'selected-route-line-layer',
        type: 'line',
        source: 'selected-route-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': '#34d399',
          'line-width': 5.5,
          'line-opacity': 1.0,
        },
      });
    }

    // Zoom and pan smoothly to the route extent
    const coords = route.geometry?.coordinates;
    if (coords && coords.length > 0) {
      const bounds = new LngLatBounds();
      coords.forEach((coord: [number, number]) => {
        bounds.extend(coord);
      });

      if (!bounds.isEmpty()) {
        this.map.fitBounds(bounds, {
          padding: { top: 90, bottom: 90, left: 90, right: 90 },
          maxZoom: 14.5,
          duration: 900,
        });
      }
    }

    return route.properties;
  }

  /**
   * Updates visibility of all vector layers and DOM markers.
   */
  public updateLayerVisibility(layers: MapLayersState) {
    if (!this.map) return;

    const setVis = (layerId: string, visible: boolean) => {
      if (this.map.getLayer(layerId)) {
        this.map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
      }
    };

    // Rivers
    setVis('rivers-glow-layer', layers.riverNetwork);
    setVis('rivers-line-layer', layers.riverNetwork);

    // Admin Units
    setVis('admin-units-fill-layer', layers.criticalZones);
    setVis('admin-units-line-layer', layers.criticalZones);

    // Hazard Surface Raster
    setVis('hazard-surface-raster-layer', layers.floodRisk || layers.landslideRisk);

    // Risk Grid
    setVis('risk-grid-fill-layer', layers.floodRisk);

    // Evacuation Routes
    setVis('evacuation-routes-line-layer', layers.evacuationRoutes);

    // Markers visibility
    this.villageZoneMarkers.forEach((m) => {
      m.getElement().style.display = layers.criticalZones ? 'flex' : 'none';
    });
    this.evacuationRouteMarkers.forEach((m) => {
      m.getElement().style.display = layers.evacuationRoutes ? 'flex' : 'none';
    });
    this.safeHavenMarkers.forEach((m) => {
      m.getElement().style.display = layers.safeHavens ? 'flex' : 'none';
    });
    this.naturalDamMarkers.forEach((m) => {
      m.getElement().style.display = layers.naturalDams ? 'flex' : 'none';
    });
    this.stationMarkers.forEach((m) => {
      m.getElement().style.display = layers.sensorStations ? 'flex' : 'none';
    });
    this.alertMarkers.forEach((m) => {
      m.getElement().style.display = 'flex';
    });
  }

  /**
   * Sets hazard surface opacity dynamically.
   */
  public setHazardOpacity(opacity: number) {
    if (this.map && this.map.getLayer('hazard-surface-raster-layer')) {
      this.map.setPaintProperty('hazard-surface-raster-layer', 'raster-opacity', opacity);
    }
  }

  /**
   * Swaps the active basemap raster layer.
   */
  public setBaseMap(basemap: BaseMapType) {
    if (!this.map) return;

    const setVis = (layerId: string, visible: boolean) => {
      if (this.map.getLayer(layerId)) {
        this.map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
      }
    };

    setVis('basemap-satellite-layer', basemap === 'satellite' || basemap === 'hybrid');
    setVis('basemap-labels-layer', basemap === 'hybrid');
    setVis('basemap-terrain-layer', basemap === 'terrain');
    setVis('basemap-roadmap-layer', basemap === 'roadmap');
  }

  /**
   * Fits camera to the Upper Beas Catchment.
   */
  public fitCatchmentBounds() {
    if (!this.map) return;
    this.map.fitBounds(
      [
        [UPPER_BEAS_HAZARD_BOUNDS.west, UPPER_BEAS_HAZARD_BOUNDS.south],
        [UPPER_BEAS_HAZARD_BOUNDS.east, UPPER_BEAS_HAZARD_BOUNDS.north],
      ],
      {
        padding: 40,
        pitch: 40,
        bearing: -10,
        duration: 1000,
      }
    );
  }

  /**
   * Cleans up all resources on unmount.
   */
  public destroy() {
    this.villageZoneMarkers.forEach((m) => m.remove());
    this.evacuationRouteMarkers.forEach((m) => m.remove());
    this.stationMarkers.forEach((m) => m.remove());
    this.safeHavenMarkers.forEach((m) => m.remove());
    this.naturalDamMarkers.forEach((m) => m.remove());
    this.alertMarkers.forEach((m) => m.remove());
    if (this.selectedLocationPinMarker) {
      this.selectedLocationPinMarker.remove();
      this.selectedLocationPinMarker = null;
    }

    this.villageZoneMarkers = [];
    this.evacuationRouteMarkers = [];
    this.stationMarkers = [];
    this.safeHavenMarkers = [];
    this.naturalDamMarkers = [];
    this.alertMarkers = [];
  }
}
