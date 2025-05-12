import React, { useState } from 'react';
import { AuditForm } from '@/features/audit-form';
import { toast } from 'react-toastify';
import { DisplayVisualisationResult } from '@/features/display-visualisation-result';
import { apiClient } from "@/shared/api/client";

export const VisualisationPage: React.FC = () => {
    const [htmlContent, setHtmlContent] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [visualisationId, setVisualisationId] = useState<string | null>(null);

    const handleRunVisualisation = async (address: string, network: string) => {
        setIsLoading(true);
        setError(null);
        setHtmlContent(null);
        setVisualisationId(null);

        try {
            const response = await apiClient('/visualise/run', {
                method: 'POST',
                body: {
                    network: network,
                    address: address,
                    source: "web",
                }
            }, true, 'text');

            const filename = response.headers?.get('X-Filename');
            if (filename) {
                setVisualisationId(filename);
            } else {
                console.warn("Заголовок 'X-Filename' не найден в ответе. Генерируем ID локально.");
                setVisualisationId(`${network}-${address.substring(0, 6)}..${address.substring(address.length - 4)}`);
            }

            setHtmlContent(response);
            toast.success(`Визуализация ${filename ? `"${filename}"` : ''} успешно создана.`);

        } catch (err: any) {
            console.error('Не удалось выполнить визуализацию:', err);
            const errorText = `Не удалось выполнить визуализацию: ${err.message || 'Неизвестная ошибка'}`;
            setError(errorText);
            toast.error(errorText);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="container mx-auto pt-20 pb-4 flex flex-col min-h-screen">
            <h1 className="text-2xl md:text-3xl font-bold mb-6 text-center md:text-left">Визуализация контрактов</h1>
            <AuditForm
                actionType="visualize"
                onRunAudit={handleRunVisualisation}
                isLoading={isLoading}
                error={null}
            />
            <DisplayVisualisationResult
                htmlContent={htmlContent}
                isLoading={isLoading}
                error={error}
                visualisationId={visualisationId}
            />
        </div>
    );
  };
  