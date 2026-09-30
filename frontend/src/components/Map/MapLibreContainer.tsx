/**
 * frontend/src/components/Map/MapLibreContainer.tsx
 * ==================================================
 * Flagship MapLibre GL JS Geospatial Intelligence Map for FLOODY SHIELD (Phase 05A).
 *
 * Recreates the professional disaster-management command visual hierarchy:
 * 1. Dominant Satellite / Hybrid Basemap showing high-detail Himalayan mountain relief
 * 2. Continuous Hazard Terrain Gradient Surface (Green -> Yellow -> Orange -> Red)
 * 3. Luminous Cyan River Network (Beas Main Stem + Tributaries with glowing underlay)
 * 4. Thin White Administrative Boundaries (Wards & Gram Panchayats with highlighted selection)
 * 5. IoT Sensor Stations & Ultrasonic Gauges with live stage indication
 * 6. De-duplicated Evacuation Corridors & Verified Safe Haven Shelters
 * 7. Gorge Bottlenecks & Natural Dam Candidate Diamonds
 * 8. Real-time Common Alerting Protocol (CAP) Alert Polygons
 * 9. Sleek Map Controls (Zoom +/-, North reset, Recenter, Geolocation, Fullscreen)
 * 10. WebGL2 graceful degradation ("MAP GRAPHICS UNSUPPORTED" fallback)
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Map as MapLibreMap } from 'maplibre-gl';
import {
  useMapStore,
  BEAS_CATCHMENT_CENTER,
  BaseMapType,
  MapFeatureDetails,
} from '../../store/useMapStore';
import { useHazardStore } from '../../store/useHazardStore';
import { MapLibreLayerManager, MapFeatureSelection } from '../../services/maps/mapLibreLayerManager';
import { LayerControl } from './LayerControl';
import { MapLegend } from './MapLegend';
import { SelectedLocationPopup } from './SelectedLocationPopup';
import {
  Plus,
  Minus,
  Compass,
  Crosshair,
  Maximize2,
  Navigation,
  AlertTriangle,
  RefreshCw,
  Layers,
} from 'lucide-react';

export interface MapLibreContainerProps {
  interactive?: boolean;
  className?: string;
  showControls?: boolean;
  onFeatureSelect?: (type: string, data: any) => void;
}

/**
 * Validates WebGL2 hardware support as required by MapLibre GL JS v6.
 */
function isWebGL2Available(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!(window.WebGL2RenderingContext && canvas.getContext('webgl2'));
  } catch {
    return false;
  }
}

export const MapLibreContainer: React.FC<MapLibreContainerProps> = ({
  className = 'w-full h-full min-h-[500px]',
  showControls = true,
  onFeatureSelect,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<MapLibreMap | null>(null);
  const layerManagerRef = useRef<MapLibreLayerManager | null>(null);

  const {
    center,
    zoom,
    pitch,
    bearing,
    layers,
    activeBasemap,
    setActiveBasemap,
    hazardOpacity,
    setHazardOpacity,
    selectedFeature,
    setSelectedFeature,
    selectedRouteId,
    setSelectedRouteId,
    setMapLoaded,
    resetToBeasCatchment,
  } = useMapStore();

  const { setSelectedDam, setSelectedStation } = useHazardStore();

  const [webGL2Supported] = useState<boolean>(() => isWebGL2Available());
  const [syncStatus, setSyncStatus] = useState<string>('Initializing MapLibre GL JS...');
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Handle feature click from layer manager
  const handleFeatureSelect = useCallback(
    (selection: MapFeatureSelection) => {
      setSelectedFeature(selection as MapFeatureDetails);
      if (selection.type === 'NATURAL_DAM') {
        setSelectedDam(selection.properties as any);
      } else if (selection.type === 'SENSOR_STATION') {
        setSelectedStation(selection.properties as any);
      } else if (selection.type === 'ADMIN_UNIT') {
        layerManagerRef.current?.highlightAdminUnit(selection.id);
      } else if (selection.type === 'EVACUATION_ROUTE') {
        setSelectedRouteId(selection.id);
        layerManagerRef.current?.focusEvacuationRoute(selection.id);
      }
      onFeatureSelect?.(selection.type, selection.properties);
    },
    [onFeatureSelect, setSelectedDam, setSelectedStation, setSelectedFeature, setSelectedRouteId]
  );

  // Initialize MapLibre GL JS instance
  useEffect(() => {
    if (!webGL2Supported || !mapContainerRef.current) return;

    let isSubscribed = true;

    // Destroy existing instance if any
    if (layerManagerRef.current) {
      layerManagerRef.current.destroy();
      layerManagerRef.current = null;
    }
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    // Bare minimum valid MapLibre style to host our custom raster and vector layers
    const map = new MapLibreMap({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [],
      },
      center: center || BEAS_CATCHMENT_CENTER,
      zoom: zoom || 11.2,
      pitch: pitch || 40,
      bearing: bearing || -10,
      maxBounds: [
        [76.60, 31.20],
        [77.70, 32.65],
      ],
      attributionControl: false,
    });

    mapInstanceRef.current = map;

    map.on('load', async () => {
      if (!isSubscribed) return;

      const layerMgr = new MapLibreLayerManager(map, handleFeatureSelect);
      layerManagerRef.current = layerMgr;

      try {
        await layerMgr.initializeLayers(layers, hazardOpacity, activeBasemap);
        if (isSubscribed) {
          setMapLoaded(true);
          setSyncStatus('GIS Datasets Active');
          const currentRouteId = useMapStore.getState().selectedRouteId;
          if (currentRouteId) {
            layerMgr.focusEvacuationRoute(currentRouteId);
          }
        }
      } catch (err) {
        console.warn('MapLibre Layer Init Warning:', err);
        if (isSubscribed) {
          setSyncStatus('GIS Partial Sync');
        }
      }
    });

    // Handle container resize
    const handleResize = () => {
      map.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      isSubscribed = false;
      window.removeEventListener('resize', handleResize);
      if (layerManagerRef.current) {
        layerManagerRef.current.destroy();
        layerManagerRef.current = null;
      }
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [webGL2Supported]);

  // Synchronize layer visibility when Zustand store updates
  useEffect(() => {
    if (layerManagerRef.current) {
      layerManagerRef.current.updateLayerVisibility(layers);
    }
  }, [layers]);

  // Synchronize hazard opacity changes
  useEffect(() => {
    if (layerManagerRef.current) {
      layerManagerRef.current.setHazardOpacity(hazardOpacity);
    }
  }, [hazardOpacity]);

  // Synchronize base map changes
  useEffect(() => {
    if (layerManagerRef.current) {
      layerManagerRef.current.setBaseMap(activeBasemap);
    }
  }, [activeBasemap]);

  // Synchronize selected feature highlight & fixed map pointer pin
  useEffect(() => {
    if (layerManagerRef.current) {
      if (selectedFeature) {
        if (selectedFeature.type === 'ADMIN_UNIT') {
          layerManagerRef.current.highlightAdminUnit(selectedFeature.id);
        }
        const coords =
          selectedFeature.coordinates ||
          (selectedFeature.properties?.centroid as [number, number]) ||
          (selectedFeature.properties?.longitude && selectedFeature.properties?.latitude
            ? [selectedFeature.properties.longitude, selectedFeature.properties.latitude]
            : null);
        if (coords) {
          layerManagerRef.current.setSelectedLocationPin(coords, selectedFeature.name, selectedFeature.riskTier);
        }
      } else {
        layerManagerRef.current.setSelectedLocationPin(null);
      }
    }
  }, [selectedFeature]);

  // Synchronize evacuation route focus & navigation
  useEffect(() => {
    if (layerManagerRef.current) {
      if (selectedRouteId) {
        layerManagerRef.current.focusEvacuationRoute(selectedRouteId);
      } else {
        layerManagerRef.current.focusEvacuationRoute(null);
      }
    }
  }, [selectedRouteId]);

  // Map Controls Handlers
  const handleZoomIn = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.zoomIn({ duration: 300 });
    }
  };

  const handleZoomOut = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.zoomOut({ duration: 300 });
    }
  };

  const handleResetNorth = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.resetNorthPitch({ duration: 600 });
    }
  };

  const handleRecenter = () => {
    resetToBeasCatchment();
    if (layerManagerRef.current) {
      layerManagerRef.current.fitCatchmentBounds();
    } else if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo({
        center: BEAS_CATCHMENT_CENTER,
        zoom: 11.2,
        pitch: 40,
        bearing: -10,
        duration: 800,
      });
    }
  };

  const handleLocateMe = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          if (mapInstanceRef.current) {
            mapInstanceRef.current.flyTo({
              center: [pos.coords.longitude, pos.coords.latitude],
              zoom: 14,
              duration: 1000,
            });
          }
        },
        (err) => {
          console.warn('Geolocation failed:', err);
        }
      );
    }
  };

  const handleToggleFullscreen = () => {
    if (!mapContainerRef.current) return;
    if (!document.fullscreenElement) {
      mapContainerRef.current.requestFullscreen?.().then(() => setIsFullscreen(true));
    } else {
      document.exitFullscreen?.().then(() => setIsFullscreen(false));
    }
  };

  // WebGL2 Unsupported Graceful Degradation
  if (!webGL2Supported) {
    return (
      <div className={`relative ${className} bg-slate-950 flex items-center justify-center p-6 rounded-2xl border border-slate-800 text-white select-none`}>
        <div className="max-w-md text-center space-y-4 p-6 rounded-2xl bg-slate-900/90 border border-slate-700/80 shadow-2xl">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold tracking-wider uppercase text-amber-400">
              MAP GRAPHICS UNSUPPORTED
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              MapLibre GL JS v6 requires hardware-accelerated WebGL2 rendering to display continuous multi-hazard terrain surfaces and satellite imagery.
            </p>
          </div>
          <div className="pt-2 flex flex-col sm:flex-row gap-2 justify-center">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-xs font-semibold rounded-xl transition shadow-md shadow-blue-500/20"
            >
              <span>Retry Rendering</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={mapContainerRef}
      className={`relative ${className} overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 shadow-inner bg-slate-950`}
    >
      {/* MapLibre WebGL Canvas Container */}
      <div className="w-full h-full" />

      {/* Floating In-Map Overlays */}
      {showControls && (
        <>
          {/* Top-Left: Floating Layers & Basemap Control Panel */}
          <div className="absolute top-4 left-4 z-10 flex flex-col gap-2 pointer-events-auto">
            <LayerControl
              onBaseMapChange={(bm) => setActiveBasemap(bm)}
              onOpacityChange={(op) => setHazardOpacity(op)}
            />
          </div>

          {/* Bottom-Left: Floating Hazard Risk Index Legend */}
          <div className="absolute bottom-4 left-4 z-10 hidden sm:block pointer-events-auto">
            <MapLegend />
          </div>

          {/* Top-Right: Floating Selected Location & Risk Popup */}
          {selectedFeature && (
            <div className="pointer-events-auto">
              <SelectedLocationPopup
                feature={selectedFeature}
                onClose={() => setSelectedFeature(null)}
                onViewEvacuation={() => {
                  useMapStore.getState().setLayer('evacuationRoutes', true);
                  useMapStore.getState().setLayer('safeHavens', true);
                }}
              />
            </div>
          )}

          {/* Right-Hand Disaster-Intelligence Map Toolbar */}
          <div className="absolute bottom-6 right-4 z-10 flex flex-col gap-1.5 pointer-events-auto">
            <div className="flex flex-col bg-slate-950/90 text-white backdrop-blur-md rounded-2xl border border-slate-700/80 shadow-2xl p-1">
              <button
                onClick={handleZoomIn}
                title="Zoom In"
                className="p-2.5 rounded-xl hover:bg-slate-800/80 text-slate-300 hover:text-white transition"
              >
                <Plus className="w-4 h-4 stroke-[2.5]" />
              </button>
              <div className="h-px bg-slate-800 mx-1" />
              <button
                onClick={handleZoomOut}
                title="Zoom Out"
                className="p-2.5 rounded-xl hover:bg-slate-800/80 text-slate-300 hover:text-white transition"
              >
                <Minus className="w-4 h-4 stroke-[2.5]" />
              </button>
            </div>

            <div className="flex flex-col bg-slate-950/90 text-white backdrop-blur-md rounded-2xl border border-slate-700/80 shadow-2xl p-1">
              <button
                onClick={handleResetNorth}
                title="Reset Bearing &amp; Pitch (North)"
                className="p-2.5 rounded-xl hover:bg-slate-800/80 text-slate-300 hover:text-blue-400 transition"
              >
                <Compass className="w-4 h-4" />
              </button>
              <button
                onClick={handleRecenter}
                title="Recenter Upper Beas Catchment"
                className="p-2.5 rounded-xl hover:bg-slate-800/80 text-slate-300 hover:text-blue-400 transition"
              >
                <Crosshair className="w-4 h-4" />
              </button>
              <button
                onClick={handleLocateMe}
                title="Locate My Position"
                className="p-2.5 rounded-xl hover:bg-slate-800/80 text-slate-300 hover:text-blue-400 transition"
              >
                <Navigation className="w-4 h-4" />
              </button>
              <button
                onClick={handleToggleFullscreen}
                title="Toggle Fullscreen"
                className="p-2.5 rounded-xl hover:bg-slate-800/80 text-slate-300 hover:text-blue-400 transition"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Micro Status Badge */}
          <div className="absolute bottom-2 right-20 z-10 hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950/80 border border-slate-800 text-[10px] text-slate-400 backdrop-blur-sm pointer-events-none select-none">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-mono">{syncStatus}</span>
          </div>
        </>
      )}
    </div>
  );
};
