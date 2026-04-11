import { useEffect, useRef, useState, useCallback } from 'react';
import { Niivue } from '@niivue/niivue';
import type { BrainMapEvent, ColormapType } from '../types';
import { interpolateColormap, rgbToFloat } from '../utils/colormaps';
import { cn } from '@/lib/utils';
import { Loader2, RotateCcw, ZoomIn, ZoomOut, Move3d } from 'lucide-react';
import { Button } from '@/components/ui/button';

// API base URL for atlas files
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface AtlasData {
  regions: string[];
  lh: {
    n_vertices: number;
    vertex_labels: number[];
    label_names: string[];
  };
  rh: {
    n_vertices: number;
    vertex_labels: number[];
    label_names: string[];
  };
  region_to_labels: Record<string, number[]>;
}

type ViewMode = 'expression' | 'disease' | 'overlay';

interface Brain3DViewerProps {
  expressionMap: BrainMapEvent | null;
  diseaseMap: BrainMapEvent | null;
  viewMode: ViewMode;
  overlayOpacity: number;
  className?: string;
}

export function Brain3DViewer({
  expressionMap,
  diseaseMap,
  viewMode,
  overlayOpacity,
  className,
}: Brain3DViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nvRef = useRef<Niivue | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [atlasData, setAtlasData] = useState<AtlasData | null>(null);

  // Load atlas region mapping
  useEffect(() => {
    async function loadAtlas() {
      try {
        const response = await fetch(`${API_BASE}/api/atlas/dk_regions.json`);
        if (!response.ok) {
          throw new Error('Atlas not prepared. Run: python scripts/prepare_atlas.py');
        }
        const data = await response.json();
        setAtlasData(data);
      } catch (err) {
        console.warn('Failed to load atlas data:', err);
        // Continue without atlas - will use fallback visualization
      }
    }
    loadAtlas();
  }, []);

  // Initialize NiiVue
  useEffect(() => {
    if (!canvasRef.current) return;

    const nv = new Niivue({
      backColor: [0.05, 0.05, 0.08, 1], // Match app background
      show3Dcrosshair: false,
      isOrientCube: false,
      isColorbar: false,
      isRadiologicalConvention: false,
      meshThicknessOn2D: 0,
    });

    nv.attachToCanvas(canvasRef.current);
    nvRef.current = nv;

    // Load brain meshes
    loadBrainMeshes(nv);

    return () => {
      // Cleanup
      nvRef.current = null;
    };
  }, []);

  // Load brain surface meshes
  async function loadBrainMeshes(nv: Niivue) {
    setIsLoading(true);
    setError(null);

    try {
      // Try to load GIFTI meshes from the backend
      const meshUrls = [
        `${API_BASE}/api/atlas/lh.pial.gii`,
        `${API_BASE}/api/atlas/rh.pial.gii`,
      ];

      // Check if atlas files exist
      const checkResponse = await fetch(meshUrls[0], { method: 'HEAD' });

      if (checkResponse.ok) {
        // Load actual mesh files
        await nv.loadMeshes([
          { url: meshUrls[0], rgba255: [200, 200, 200, 255] },
          { url: meshUrls[1], rgba255: [200, 200, 200, 255] },
        ]);
      } else {
        // Use built-in brain mesh as fallback
        await loadFallbackMesh(nv);
      }

      setIsLoading(false);
    } catch (err) {
      console.error('Failed to load brain mesh:', err);
      // Try fallback
      try {
        await loadFallbackMesh(nv);
        setIsLoading(false);
      } catch (fallbackErr) {
        setError('Failed to load 3D brain model');
        setIsLoading(false);
      }
    }
  }

  // Fallback to a built-in or simple mesh
  async function loadFallbackMesh(nv: Niivue) {
    // NiiVue has some built-in demo meshes we can use
    // For a real implementation, you might bundle a default mesh
    try {
      // Try loading a sample mesh from NiiVue's CDN
      await nv.loadMeshes([
        {
          url: 'https://niivue.github.io/niivue/images/BrainMesh_ICBM152.lh.mz3',
          rgba255: [200, 200, 200, 255],
        },
        {
          url: 'https://niivue.github.io/niivue/images/BrainMesh_ICBM152.rh.mz3',
          rgba255: [200, 200, 200, 255],
        },
      ]);
    } catch {
      // If even fallback fails, we'll show error state
      throw new Error('No brain mesh available');
    }
  }

  // Update mesh colors when map data changes
  useEffect(() => {
    if (!nvRef.current || isLoading) return;

    const activeMap = getActiveMap();
    if (!activeMap?.parcellated_values) {
      // Reset to default gray
      updateMeshColors(nvRef.current, null, null, 'viridis');
      return;
    }

    const colormap = activeMap.colormap || 'viridis';
    const valueRange = activeMap.value_range || [0, 1];

    if (viewMode === 'overlay' && expressionMap?.parcellated_values && diseaseMap?.parcellated_values) {
      // Overlay mode - blend both maps
      updateMeshColorsOverlay(
        nvRef.current,
        expressionMap.parcellated_values,
        diseaseMap.parcellated_values,
        expressionMap.value_range || [0, 1],
        diseaseMap.value_range || [0, 1],
        overlayOpacity / 100
      );
    } else {
      // Single map mode
      updateMeshColors(
        nvRef.current,
        activeMap.parcellated_values,
        valueRange,
        colormap
      );
    }
  }, [expressionMap, diseaseMap, viewMode, overlayOpacity, isLoading, atlasData]);

  function getActiveMap(): BrainMapEvent | null {
    if (viewMode === 'expression') return expressionMap;
    if (viewMode === 'disease') return diseaseMap;
    // For overlay, return expression as base (disease will be blended)
    return expressionMap;
  }

  // Update mesh vertex colors based on parcellated values
  function updateMeshColors(
    nv: Niivue,
    values: Record<string, number> | null,
    valueRange: [number, number] | null,
    colormap: ColormapType
  ) {
    if (!nv.meshes || nv.meshes.length === 0) return;

    for (const mesh of nv.meshes) {
      if (!mesh.pts) continue;

      const nVertices = mesh.pts.length / 3;
      const colors = new Float32Array(nVertices * 4);

      if (values && valueRange && atlasData) {
        // Color by parcellated values
        const isLeftHemi = mesh.name?.includes('lh') || mesh.name?.includes('left');
        const hemiData = isLeftHemi ? atlasData.lh : atlasData.rh;

        for (let i = 0; i < nVertices; i++) {
          const labelIdx = hemiData.vertex_labels[i] || 0;
          const regionName = hemiData.label_names[labelIdx];

          // Find matching DK region
          const suffix = isLeftHemi ? '_L' : '_R';
          let value = 0;

          // Try to find the region value
          for (const [region, val] of Object.entries(values)) {
            if (region.endsWith(suffix)) {
              const baseRegion = region.replace(suffix, '').toLowerCase();
              if (regionName?.toLowerCase().includes(baseRegion)) {
                value = val;
                break;
              }
            }
          }

          const rgb = interpolateColormap(value, valueRange, colormap);
          const [r, g, b] = rgbToFloat(rgb);

          colors[i * 4] = r;
          colors[i * 4 + 1] = g;
          colors[i * 4 + 2] = b;
          colors[i * 4 + 3] = 1.0;
        }
      } else {
        // Default gray color
        for (let i = 0; i < nVertices; i++) {
          colors[i * 4] = 0.7;
          colors[i * 4 + 1] = 0.7;
          colors[i * 4 + 2] = 0.7;
          colors[i * 4 + 3] = 1.0;
        }
      }

      // Apply colors to mesh - NiiVue expects Uint8Array
      const rgba255 = new Uint8Array(nVertices * 4);
      for (let i = 0; i < nVertices; i++) {
        rgba255[i * 4] = Math.round(colors[i * 4] * 255);
        rgba255[i * 4 + 1] = Math.round(colors[i * 4 + 1] * 255);
        rgba255[i * 4 + 2] = Math.round(colors[i * 4 + 2] * 255);
        rgba255[i * 4 + 3] = 255;
      }
      mesh.rgba255 = rgba255;
      mesh.updateMesh(nv.gl);
    }

    nv.drawScene();
  }

  // Overlay mode: blend expression and disease maps
  function updateMeshColorsOverlay(
    nv: Niivue,
    expressionValues: Record<string, number>,
    diseaseValues: Record<string, number>,
    expressionRange: [number, number],
    diseaseRange: [number, number],
    blendFactor: number
  ) {
    if (!nv.meshes || nv.meshes.length === 0 || !atlasData) return;

    for (const mesh of nv.meshes) {
      if (!mesh.pts) continue;

      const nVertices = mesh.pts.length / 3;
      const colors = new Float32Array(nVertices * 4);

      const isLeftHemi = mesh.name?.includes('lh') || mesh.name?.includes('left');
      const hemiData = isLeftHemi ? atlasData.lh : atlasData.rh;
      const suffix = isLeftHemi ? '_L' : '_R';

      for (let i = 0; i < nVertices; i++) {
        const labelIdx = hemiData.vertex_labels[i] || 0;
        const regionName = hemiData.label_names[labelIdx];

        let exprValue = 0;
        let diseaseValue = 0;

        // Find matching values
        for (const [region, val] of Object.entries(expressionValues)) {
          if (region.endsWith(suffix)) {
            const baseRegion = region.replace(suffix, '').toLowerCase();
            if (regionName?.toLowerCase().includes(baseRegion)) {
              exprValue = val;
              break;
            }
          }
        }

        for (const [region, val] of Object.entries(diseaseValues)) {
          if (region.endsWith(suffix)) {
            const baseRegion = region.replace(suffix, '').toLowerCase();
            if (regionName?.toLowerCase().includes(baseRegion)) {
              diseaseValue = val;
              break;
            }
          }
        }

        // Get colors from both colormaps
        const exprRgb = interpolateColormap(exprValue, expressionRange, 'viridis');
        const diseaseRgb = interpolateColormap(diseaseValue, diseaseRange, 'inferno');

        // Blend colors
        const [er, eg, eb] = rgbToFloat(exprRgb);
        const [dr, dg, db] = rgbToFloat(diseaseRgb);

        colors[i * 4] = er * (1 - blendFactor) + dr * blendFactor;
        colors[i * 4 + 1] = eg * (1 - blendFactor) + dg * blendFactor;
        colors[i * 4 + 2] = eb * (1 - blendFactor) + db * blendFactor;
        colors[i * 4 + 3] = 1.0;
      }

      // Apply colors to mesh - NiiVue expects Uint8Array
      const overlayRgba255 = new Uint8Array(nVertices * 4);
      for (let i = 0; i < nVertices; i++) {
        overlayRgba255[i * 4] = Math.round(colors[i * 4] * 255);
        overlayRgba255[i * 4 + 1] = Math.round(colors[i * 4 + 1] * 255);
        overlayRgba255[i * 4 + 2] = Math.round(colors[i * 4 + 2] * 255);
        overlayRgba255[i * 4 + 3] = 255;
      }
      mesh.rgba255 = overlayRgba255;
      mesh.updateMesh(nv.gl);
    }

    nv.drawScene();
  }

  // Camera controls
  const resetView = useCallback(() => {
    if (nvRef.current) {
      nvRef.current.setClipPlane([0, 0, 0, 0]);
      nvRef.current.scene.renderAzimuth = 110;
      nvRef.current.scene.renderElevation = 10;
      nvRef.current.drawScene();
    }
  }, []);

  const zoomIn = useCallback(() => {
    if (nvRef.current) {
      nvRef.current.scene.volScaleMultiplier *= 1.2;
      nvRef.current.drawScene();
    }
  }, []);

  const zoomOut = useCallback(() => {
    if (nvRef.current) {
      nvRef.current.scene.volScaleMultiplier /= 1.2;
      nvRef.current.drawScene();
    }
  }, []);

  return (
    <div className={cn('relative flex flex-col', className)}>
      {/* Canvas container */}
      <div className="relative flex-1 min-h-[350px] bg-bg-surface rounded-xl overflow-hidden border border-white/[0.08]">
        <canvas
          ref={canvasRef}
          className="w-full h-full"
          style={{ display: isLoading || error ? 'none' : 'block' }}
        />

        {/* Loading state */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <span className="text-sm text-text-muted">Loading 3D brain model...</span>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3 text-center px-4">
              <Move3d className="w-10 h-10 text-text-muted" />
              <span className="text-sm text-text-muted">{error}</span>
              <span className="text-xs text-text-muted">
                Run: <code className="bg-bg-elevated px-1.5 py-0.5 rounded">python scripts/prepare_atlas.py</code>
              </span>
            </div>
          </div>
        )}

        {/* Controls overlay */}
        {!isLoading && !error && (
          <div className="absolute bottom-3 right-3 flex items-center gap-1.5">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 bg-bg-base/80 backdrop-blur-sm border border-white/[0.08] hover:bg-bg-elevated"
              onClick={zoomOut}
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 bg-bg-base/80 backdrop-blur-sm border border-white/[0.08] hover:bg-bg-elevated"
              onClick={zoomIn}
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 bg-bg-base/80 backdrop-blur-sm border border-white/[0.08] hover:bg-bg-elevated"
              onClick={resetView}
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        )}

        {/* Instructions overlay */}
        {!isLoading && !error && (
          <div className="absolute bottom-3 left-3 text-xs text-text-muted bg-bg-base/60 backdrop-blur-sm px-2 py-1 rounded">
            Drag to rotate
          </div>
        )}
      </div>
    </div>
  );
}
