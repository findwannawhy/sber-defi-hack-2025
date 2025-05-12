import React from 'react';
import { Button } from '@/shared/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { toast } from 'react-toastify';

interface DisplayVisualisationResultProps {
  htmlContent: string | null;
  isLoading: boolean;
  error: string | null;
  visualisationId: string | null;
}

export const DisplayVisualisationResult: React.FC<DisplayVisualisationResultProps> = ({
  htmlContent,
  isLoading,
  error,
  visualisationId
}) => {

  const handleDownload = () => {
    if (!htmlContent || !visualisationId) return;

    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `visualisation-${visualisationId}-${Date.now()}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.info("HTML файл скачан.");
  };

  return (
    <Card className="mt-6 flex flex-col flex-grow min-h-[600px] md:min-h-[800px]">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Результат визуализации</CardTitle>
          {htmlContent && !error && !isLoading && (
            <Button
              onClick={handleDownload}
              disabled={!htmlContent || isLoading}
            >
              Скачать HTML
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex flex-col flex-grow p-0 md:p-6 md:pt-0">
        {isLoading && (
          <p className="m-auto text-muted-foreground">Загрузка визуализации...</p>
        )}
        {error && !isLoading && (
          <p className="m-auto text-destructive">Не удалось загрузить результат визуализации.</p>
        )}
        {!isLoading && !error && !htmlContent && (
          <p className="m-auto text-muted-foreground">Здесь будет отображен результат визуализации после её выполнения.</p>
        )}
        {htmlContent && !error && !isLoading && (
          <iframe
            srcDoc={htmlContent}
            title={`Visualisation Result ${visualisationId || ''}`}
            className="w-full h-full border rounded-md flex-grow"
            sandbox="allow-scripts allow-same-origin"
          />
        )}
      </CardContent>
    </Card>
  );
}; 