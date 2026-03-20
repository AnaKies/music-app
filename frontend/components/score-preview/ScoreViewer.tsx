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
  const [pageCount, setPageCount] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    let isMounted = true;
    let osmdInstance: { clear?: () => void } | null = null;

    function updateVisiblePage(container: HTMLDivElement, page: number) {
      const pageItems = Array.from(container.children) as HTMLElement[];
      if (!pageItems.length) {
        return;
      }

      pageItems.forEach((item, index) => {
        item.style.display = index + 1 === page ? 'block' : 'none';
      });
    }

    async function renderScore() {
      try {
        setIsRendering(true);
        setRenderError(null);
        setCurrentPage(1);
        setPageCount(1);

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
          drawPartNames: false,
          drawPartAbbreviations: false,
          backend: 'svg',
        });

        osmdInstance = osmd;
        await osmd.load(musicXml);
        osmd.render();

        if (isMounted) {
          const renderedPages = Math.max(containerRef.current.children.length, 1);
          setPageCount(renderedPages);
          setCurrentPage(1);
          updateVisiblePage(containerRef.current, 1);
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

  useEffect(() => {
    if (!containerRef.current || isRendering) {
      return;
    }

    const pageItems = Array.from(containerRef.current.children) as HTMLElement[];
    if (!pageItems.length) {
      return;
    }

    pageItems.forEach((item, index) => {
      item.style.display = index + 1 === currentPage ? 'block' : 'none';
    });
  }, [currentPage, isRendering]);

  if (renderError) {
    return <p className="score-preview__render-error">{renderError}</p>;
  }

  return (
    <div className="score-preview__viewer-shell">
      {isRendering ? <p className="score-preview__viewer-status">Rendering the score preview.</p> : null}
      {pageCount > 1 ? (
        <div className="score-preview__pagination" aria-label="Score preview pagination">
          <button
            type="button"
            className="score-preview__page-button"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((page) => Math.max(page - 1, 1))}
          >
            Previous page
          </button>
          <p className="score-preview__page-indicator">
            Page {currentPage} of {pageCount}
          </p>
          <button
            type="button"
            className="score-preview__page-button"
            disabled={currentPage === pageCount}
            onClick={() => setCurrentPage((page) => Math.min(page + 1, pageCount))}
          >
            Next page
          </button>
        </div>
      ) : null}
      <div ref={containerRef} className="score-preview__viewer" aria-label={`${title} score viewer`} />
    </div>
  );
}
