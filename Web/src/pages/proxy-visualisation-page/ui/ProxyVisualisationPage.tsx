import React, { useState, useEffect } from 'react';
import { DisplayVisualisationResult } from '@/features/display-visualisation-result';
import { VITE_BACKEND_API_URL } from "@/shared/config";

interface ProxyVisualisationPageProps {
  id: string;
}

export const ProxyVisualisationPage: React.FC<ProxyVisualisationPageProps> = ({ id }) => {
    const [htmlContent, setHtmlContent] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setIsLoading(true);
        setError(null);
        setHtmlContent(null);

        if (!id) {
            setError('Ошибка: ID визуализации не предоставлен.');
            setIsLoading(false);
            return;
        }

        const apiUrl = `${VITE_BACKEND_API_URL}/visualise/html/${id}`;

        const fetchVisualization = async () => {
            try {
                const response = await fetch(apiUrl);

                if (!response.ok) {
                    let errorMsg = `Ошибка загрузки: ${response.status}`;
                    try {
                        const errorData = await response.json();
                        errorMsg += ` - ${errorData.detail || 'Нет деталей'}`;
                    } catch (e) {
                        try {
                            const textError = await response.text();
                            if (textError) {
                                errorMsg += ` - ${textError}`;
                            }
                        } catch (textE) {
                        }
                    }
                    throw new Error(errorMsg);
                }

                const fetchedHtml = await response.text();
                setHtmlContent(fetchedHtml);

            } catch (err: any) {
                console.error('Не удалось загрузить визуализацию:', err);
                setError(`Не удалось загрузить визуализацию: ${err.message || 'Неизвестная ошибка'}`);
            } finally {
                setIsLoading(false);
            }
        };

        fetchVisualization();

    }, [id]);

    return (
        <div className="w-full p-10 pt-16">
            <div className="container mx-auto px-4 py-3 mb-4 border-b">
                <div className="flex justify-between items-center">
                    <h1 className="text-xl md:text-2xl font-bold">Proxy Visualisation: {id}</h1>
                </div>
            </div>
            <DisplayVisualisationResult
                htmlContent={htmlContent}
                isLoading={isLoading}
                error={error}
                visualisationId={id}
            />
        </div>
    );
};
  