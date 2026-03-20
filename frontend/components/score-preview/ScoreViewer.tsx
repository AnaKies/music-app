'use client';

import { useEffect, useRef, useState } from 'react';

interface ScoreViewerProps {
  previewAccess: string;
  title: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function resolvePreviewUrl(previewAccess: string): string {
  if (/^https?:\/\//i.test(previewAccess)) {
    return previewAccess;
  }

  if (previewAccess.startsWith('/')) {
    return `${API_BASE_URL}${previewAccess}`;
  }

  return `${API_BASE_URL}/${previewAccess}`;
}

export function ScoreViewer({ previewAccess, title }: ScoreViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState(true);

  useEffect(() => {
    let isMounted = true;
    let osmdInstance: { clear?: () => void } | null = null;

    async function renderScore() {
      try {
        setIsRendering(true);
        setRenderError(null);

        const response = await fetch(resolvePreviewUrl(previewAccess));
        if (!response.ok) {
          throw new Error('preview_fetch_failed');
        }

        const musicXml = await response.text();
        if (!containerRef.current) {
          return;
        }

        const { OpenSheetMusicDisplay } = await import('opensheetmusicdisplay');
        const osmd = new OpenSheetMusicDisplay(containerRef.current, {
          drawingParameters: 'compacttight',
          autoResize: true,
          followCursor: false,
          drawTitle: true,
          drawSubtitle: false,
          drawComposer: false,
          drawCredits: false,
          backend: 'svg',
        });

        osmdInstance = osmd;
        await osmd.load(musicXml);
        osmd.render();

        if (isMounted) {
          setIsRendering(false);
        }
      } catch (_error) {
        if (isMounted) {
          setRenderError('The score preview could not be rendered.');
          setIsRendering(false);
        }
      }
    }

    void renderScore();

    return () => {
      isMounted = false;
      if (osmdInstance?.clear) {
        osmdInstance.clear();
      }
    };
  }, [previewAccess]);

  if (renderError) {
    return <p className="score-preview__render-error">{renderError}</p>;
  }

  return (
    <div className="score-preview__viewer-shell">
      {isRendering ? <p className="score-preview__viewer-status">Rendering the score preview.</p> : null}
      <div ref={containerRef} className="score-preview__viewer" aria-label={`${title} score viewer`} />
    </div>
  );
}
