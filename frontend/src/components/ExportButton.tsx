import { clsx } from 'clsx';

interface ExportButtonProps {
  pdfUrl: string | null;
  sessionId: string | null;
}

export function ExportButton({ pdfUrl, sessionId }: ExportButtonProps) {
  const isReady = pdfUrl !== null;

  const handleExport = () => {
    if (!pdfUrl) return;

    // Trigger download
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `circuitmap-report-${sessionId || 'unknown'}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <button
      onClick={handleExport}
      disabled={!isReady}
      className={clsx(
        'flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all',
        'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500',
        isReady
          ? 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm'
          : 'bg-gray-200 text-gray-400 cursor-not-allowed'
      )}
    >
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
        />
      </svg>
      Export Report PDF
    </button>
  );
}
