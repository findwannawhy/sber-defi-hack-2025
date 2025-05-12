import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";

interface AuditResultViewerProps {
  auditResultUrl: string | null;
  isLoading: boolean;
  error: string | null;
}

export const AuditResultViewer: React.FC<AuditResultViewerProps> = ({
  auditResultUrl,
  isLoading,
  error
}) => {
  return (
    <Card className="mt-6 flex flex-col flex-grow min-h-[600px] md:min-h-[800px]">
      <CardHeader>
        <CardTitle>Результат аудита (PDF)</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col flex-grow p-0 md:p-6 md:pt-0">
        {isLoading && <p className="m-auto text-muted-foreground">Загрузка результата...</p>}
        {auditResultUrl && !isLoading && (
          <iframe
              src={auditResultUrl}
              className="w-full h-full border rounded-md flex-grow"
              title="Результат аудита PDF"
          >
              Ваш браузер не поддерживает отображение PDF. Вы можете <a href={auditResultUrl} download="audit_report.pdf" className="underline">скачать отчет</a>.
          </iframe>
        )}
        {!isLoading && !auditResultUrl && !error && (
            <p className="m-auto text-muted-foreground">Здесь будет отображен результат аудита после его выполнения.</p>
        )}
        {!isLoading && !auditResultUrl && error && (
            <p className="m-auto text-destructive">Не удалось загрузить результат аудита.</p>
        )}
      </CardContent>
    </Card>
  );
}; 