import { Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

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
    <Card className="overflow-hidden animate-fade-in">
      <CardContent className="p-4">
        <Button
          onClick={handleExport}
          disabled={!isReady}
          variant={isReady ? "success" : "secondary"}
          className="w-full h-12 text-sm font-semibold"
        >
          {isReady ? (
            <>
              <Download className="w-5 h-5" />
              Export Report PDF
            </>
          ) : (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Preparing PDF...
            </>
          )}
        </Button>

        {isReady && (
          <p className="text-xs text-center text-text-muted mt-2">
            Download your complete validation report
          </p>
        )}
      </CardContent>
    </Card>
  );
}
