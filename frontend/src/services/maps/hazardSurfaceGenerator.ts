/**
 * frontend/src/services/maps/hazardSurfaceGenerator.ts
 * ====================================================
 * High-performance continuous hazard raster surface generator for FLOODY SHIELD.
 * Generates a smooth multi-hazard terrain gradient (Green -> Yellow -> Orange -> Red)
 * draped over the Upper Beas Basin bounding envelope:
 *
 * Coordinates:
 *   North: 32.40°N  (Rohtang Pass Crest)
 *   South: 31.62°N  (Larji / Aut Gorge)
 *   West:  76.90°E  (Kangra Ridge)
 *   East:  77.40°E  (Parvati / Pin Parbati Ridge)
 *
 * Preserves mountain satellite relief underneath via smooth alpha blending.
 */

export interface HazardBounds {
  north: number;
  south: number;
  west: number;
  east: number;
}

export const UPPER_BEAS_HAZARD_BOUNDS: HazardBounds = {
  north: 32.40,
  south: 31.62,
  west: 76.90,
  east: 77.40,
};

/**
 * Upper Beas Basin MapLibre Image Source Coordinates:
 * [top-left, top-right, bottom-right, bottom-left] in [lng, lat] format.
 */
export const UPPER_BEAS_IMAGE_COORDINATES: [[number, number], [number, number], [number, number], [number, number]] = [
  [UPPER_BEAS_HAZARD_BOUNDS.west, UPPER_BEAS_HAZARD_BOUNDS.north], // top-left
  [UPPER_BEAS_HAZARD_BOUNDS.east, UPPER_BEAS_HAZARD_BOUNDS.north], // top-right
  [UPPER_BEAS_HAZARD_BOUNDS.east, UPPER_BEAS_HAZARD_BOUNDS.south], // bottom-right
  [UPPER_BEAS_HAZARD_BOUNDS.west, UPPER_BEAS_HAZARD_BOUNDS.south], // bottom-left
];

/**
 * Generates an in-memory PNG Data URL of the continuous multi-hazard risk surface.
 * Seamlessly integrates into MapLibre GL JS as an 'image' source and 'raster' layer.
 */
export function generateHazardSurfaceDataUrl(width = 512, height = 512): string {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');

  if (!ctx) {
    return '';
  }

  // 1. Clear transparent canvas
  ctx.clearRect(0, 0, width, height);

  // 2. Base mountain catchment background: Gentle Low-to-Moderate green/yellow tint
  const baseGrad = ctx.createLinearGradient(0, 0, 0, height);
  baseGrad.addColorStop(0.0, 'rgba(16, 185, 129, 0.15)'); // Rohtang Alpine Crest (Low risk baseline)
  baseGrad.addColorStop(0.35, 'rgba(234, 179, 8, 0.28)'); // Solang / Palchan Valley (Moderate)
  baseGrad.addColorStop(0.65, 'rgba(249, 115, 22, 0.35)'); // Kullu Floodplain (High)
  baseGrad.addColorStop(1.0, 'rgba(16, 185, 129, 0.15)'); // Lower Gorge Basin (Moderate)
  ctx.fillStyle = baseGrad;
  ctx.fillRect(0, 0, width, height);

  // 3. High Inundation Corridor: Longitudinal River valley channel (Red/Orange continuous gradient)
  // River runs roughly north-to-south in the center (x ~ 55% to 45%)
  const riverCorridor = ctx.createLinearGradient(width * 0.58, 0, width * 0.42, height);
  riverCorridor.addColorStop(0.15, 'rgba(239, 68, 68, 0.55)'); // Solang Gorge Choke
  riverCorridor.addColorStop(0.28, 'rgba(249, 115, 22, 0.50)'); // Palchan Confluence
  riverCorridor.addColorStop(0.40, 'rgba(239, 68, 68, 0.60)'); // Old Manali / Manalsu Overwash
  riverCorridor.addColorStop(0.55, 'rgba(234, 179, 8, 0.45)'); // Aleo / Naggar Reach
  riverCorridor.addColorStop(0.80, 'rgba(249, 115, 22, 0.55)'); // Kullu Sarvari Confluence
  riverCorridor.addColorStop(0.95, 'rgba(239, 68, 68, 0.65)'); // Bhuntar / Larji Reservoir Backwater

  ctx.save();
  ctx.beginPath();
  // Draw organic river corridor swath
  ctx.moveTo(width * 0.62, 0);
  ctx.bezierCurveTo(width * 0.65, height * 0.25, width * 0.58, height * 0.45, width * 0.50, height * 0.65);
  ctx.bezierCurveTo(width * 0.45, height * 0.80, width * 0.42, height * 0.90, width * 0.40, height);
  ctx.lineTo(width * 0.32, height);
  ctx.bezierCurveTo(width * 0.34, height * 0.90, width * 0.36, height * 0.80, width * 0.40, height * 0.65);
  ctx.bezierCurveTo(width * 0.46, height * 0.45, width * 0.50, height * 0.25, width * 0.48, 0);
  ctx.closePath();
  ctx.fillStyle = riverCorridor;
  ctx.filter = 'blur(16px)';
  ctx.fill();
  ctx.restore();

  // 4. Critical Hotspot 1: Solang Debris Chute & Natural Dam Breach Zone (Top Center-Left)
  const spotSolang = ctx.createRadialGradient(
    width * 0.55,
    height * 0.18,
    width * 0.02,
    width * 0.55,
    height * 0.18,
    width * 0.18
  );
  spotSolang.addColorStop(0.0, 'rgba(239, 68, 68, 0.85)'); // Critical Core
  spotSolang.addColorStop(0.4, 'rgba(249, 115, 22, 0.65)');
  spotSolang.addColorStop(0.8, 'rgba(234, 179, 8, 0.35)');
  spotSolang.addColorStop(1.0, 'rgba(234, 179, 8, 0.0)');
  ctx.save();
  ctx.filter = 'blur(12px)';
  ctx.fillStyle = spotSolang;
  ctx.beginPath();
  ctx.arc(width * 0.55, height * 0.18, width * 0.18, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // 5. Critical Hotspot 2: Old Manali / Manalsu Flash Flood Fan (Mid Valley)
  const spotManali = ctx.createRadialGradient(
    width * 0.52,
    height * 0.36,
    width * 0.015,
    width * 0.52,
    height * 0.36,
    width * 0.16
  );
  spotManali.addColorStop(0.0, 'rgba(239, 68, 68, 0.80)');
  spotManali.addColorStop(0.45, 'rgba(249, 115, 22, 0.60)');
  spotManali.addColorStop(0.85, 'rgba(234, 179, 8, 0.25)');
  spotManali.addColorStop(1.0, 'rgba(16, 185, 129, 0.0)');
  ctx.save();
  ctx.filter = 'blur(10px)';
  ctx.fillStyle = spotManali;
  ctx.beginPath();
  ctx.arc(width * 0.52, height * 0.36, width * 0.16, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // 6. High Risk Zone 3: Kullu Akhara Bazar / Sarvari Inundation (Lower Valley)
  const spotKullu = ctx.createRadialGradient(
    width * 0.42,
    height * 0.72,
    width * 0.02,
    width * 0.42,
    height * 0.72,
    width * 0.20
  );
  spotKullu.addColorStop(0.0, 'rgba(239, 68, 68, 0.75)');
  spotKullu.addColorStop(0.4, 'rgba(249, 115, 22, 0.55)');
  spotKullu.addColorStop(0.8, 'rgba(234, 179, 8, 0.30)');
  spotKullu.addColorStop(1.0, 'rgba(16, 185, 129, 0.0)');
  ctx.save();
  ctx.filter = 'blur(14px)';
  ctx.fillStyle = spotKullu;
  ctx.beginPath();
  ctx.arc(width * 0.42, height * 0.72, width * 0.20, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  return canvas.toDataURL('image/png');
}
