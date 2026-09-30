/**
 * frontend/src/components/Map/MapContainer.tsx
 * ============================================
 * Primary Disaster-Intelligence Geospatial Container for FLOODY SHIELD.
 * Powered 100% by MapLibre GL JS v6 with hardware-accelerated WebGL2 rendering,
 * continuous multi-hazard raster surfaces, and authoritative PostGIS feeds.
 *
 * All Google Maps dependencies have been removed.
 */

import React from 'react';
import { MapLibreContainer } from './MapLibreContainer';

export interface MapContainerProps {
  interactive?: boolean;
  className?: string;
  showControls?: boolean;
  onFeatureSelect?: (type: string, data: any) => void;
  preferredEngine?: 'maplibre' | 'google';
}

export const MapContainer: React.FC<MapContainerProps> = ({
  className = 'w-full h-full min-h-[500px]',
  showControls = true,
  onFeatureSelect,
  preferredEngine = 'maplibre',
}) => {
  return (
    <div className={`relative ${className}`}>
      <MapLibreContainer
        className="w-full h-full"
        showControls={showControls}
        onFeatureSelect={onFeatureSelect}
      />
    </div>
  );
};
