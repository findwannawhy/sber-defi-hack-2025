import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { AuditForm } from '@/features/audit-form';
import { AuditResultViewer } from '@/features/audit-result-viewer';
import { apiClient } from '../../../shared/api/client';

export const AuditPage: React.FC = () => {
    const [auditResultUrl, setAuditResultUrl] = useState<string | null>(null);
    const [isLoadingAudit, setIsLoadingAudit] = useState(false);
    const [auditError, setAuditError] = useState<string | null>(null);

    const handleRunAudit = async (address: string, network: string) => {
        setIsLoadingAudit(true);
        setAuditError(null);
        setAuditResultUrl(null);

        try {
            const result = await apiClient(
                '/audit/run',
                {
                    method: 'POST',
                    body: JSON.stringify({ address, network }),
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/pdf',
                    },
                },
                false,
                'pdf'
            );

            if (typeof result === 'string') {
                setAuditResultUrl(result);
                toast.success("Аудит успешно завершен.");
            } else {
                console.error('apiClient не вернул строку URL для PDF ответа, или вернул undefined:', result);
                throw new Error('Неожиданный ответ от сервера при запросе PDF-аудита.');
            }

        } catch (error: any) {
            let errorMessage = 'Ошибка при выполнении аудита.';
            if (error instanceof Error) {
                errorMessage = error.message;
            } else {
                errorMessage = String(error);
            }

            setAuditError(errorMessage);
            toast.error(errorMessage);
        } finally {
            setIsLoadingAudit(false);
        }
    };

    return (
      <div className="container mx-auto pt-20 pb-4 flex flex-col min-h-screen">
        <h1 className="text-2xl md:text-3xl font-bold mb-6 text-center md:text-left">Проверка контрактов на уязвимости</h1>

        <AuditForm 
            actionType="audit"
            onRunAudit={handleRunAudit}
            isLoading={isLoadingAudit}
            error={auditError}
        />

        <AuditResultViewer 
            auditResultUrl={auditResultUrl}
            isLoading={isLoadingAudit}
            error={auditError}
        />
      </div>
    );
};
  