import { VITE_BACKEND_API_URL } from "@/shared/config";

// --- Токен ApiClient'a и утилиты из AuthContext --- 
let apiClientAccessToken: string | null = null;
let apiClientIsAuthorized: boolean = false;
let logout: () => void = () => {};
let setAccessToken: (token: string) => void = () => {};

// Передаём функцию для обновления токена ApiClient'a в AuthContext
export const updateApiClientAccessToken = (newAccessToken: string | null) => {
    apiClientAccessToken = newAccessToken;
};

export const updateApiClientIsAuthorized = (newIsAuthorized: boolean) => {
    apiClientIsAuthorized = newIsAuthorized;
};

// Принимаем утилиты из AuthContext
export const setAuthUtils = (
    accessTokenSetter: (token: string) => void,
    logoutHandler: () => void,
) => {
    setAccessToken = accessTokenSetter;
    logout = logoutHandler;
};

// Переменные для управления обновлением токена
let isTokenRefreshing = false;
let refreshTokenPromise: Promise<string | null> | null = null;

// Функция для обновления jwt токена по refresh токену
export const refreshToken = async (): Promise<string | null> => {
    try {
        const response = await fetch(VITE_BACKEND_API_URL + '/auth/refresh', {
            method: 'POST',
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            if (data.access_token) {
                setAccessToken(data.access_token);
                return data.access_token;
            }
        }

        logout();
        return null;
    } catch (error) {
        console.error('Ошибка обновления токена:', error);
        logout(); 
        return null;
    }
};

// Функция для обновления токена и повторного запроса
const refreshTokenAndRetry = async (endpoint: string, options: RequestInit, responseType?: ResponseType): Promise<any> => {
    if (!isTokenRefreshing) {
        isTokenRefreshing = true;
        refreshTokenPromise = refreshToken();
    }

    try {
        const newToken = await refreshTokenPromise;
        if (newToken) {
            const newOptions = { ...options };
            const newHeaders = new Headers(newOptions.headers || {});
            newHeaders.set('Authorization', 'Bearer ' + newToken);
            newOptions.headers = newHeaders;

            const retryResponse = await fetch(VITE_BACKEND_API_URL + endpoint, newOptions);

            if (!retryResponse.ok) {
                let errorDetail = 'HTTP ошибка при повторном запросе: ' + retryResponse.status + ' ' + retryResponse.statusText;
                try {
                    if (retryResponse.headers.get('Content-Type')?.includes('application/json')) {
                        const errorJson = await retryResponse.json();
                        errorDetail = errorJson.detail || JSON.stringify(errorJson);
                    } else {
                        const errorText = await retryResponse.text();
                        if (errorText) errorDetail = errorText;
                    }
                } catch (e) {
                    console.warn('Не удалось обработать тело ответа ошибки:', e);
                }

                if (retryResponse.status === 401) {
                    logout();
                    throw new Error('Unauthorized after token refresh.');
                }
                throw new Error(errorDetail);
            }

            if (retryResponse.status === 204) {
                if (responseType === 'pdf') {
                    throw new Error('Ожидался PDF, но сервер ответил статусом 204 No Content.');
                }
                return undefined;
            }

            switch (responseType) {
                case 'json':
                    return await retryResponse.json();
                case 'pdf':
                    const pdfBlob = await retryResponse.blob();
                    if (pdfBlob.size === 0) {
                        throw new Error('Сервер вернул пустой PDF.');
                    }
                    return URL.createObjectURL(pdfBlob);
                case 'html':
                case 'text':
                    return await retryResponse.text();
                default:
                    try {
                        return await retryResponse.json();
                    } catch (e) {
                        return await retryResponse.text();
                    }
            }
        }
        throw new Error('Не удалось обновить токен.');
    } finally {
        isTokenRefreshing = false;
        refreshTokenPromise = null;
    }
};

// Типы ожидаемых ответов
export type ResponseType = 'json' | 'pdf' | 'html' | 'text';

// Тип для тела запроса
type RequestBody = BodyInit | object | null;

// Тип для опций запроса
type ApiRequestOptions = Omit<RequestInit, 'body'> & { body?: RequestBody };

// Функция для API запросов
export const apiClient = async (
    endpoint: string, 
    options: ApiRequestOptions = {}, 
    authNeeded: boolean = true,
    responseType: ResponseType = 'json'
) => {
    const makeRequest = async (currentOptions: ApiRequestOptions) => {
        const token = apiClientAccessToken;
        const headers = new Headers(currentOptions.headers || {});
        if (authNeeded && token) {
            headers.set('Authorization', 'Bearer ' + token);
        }

        if (currentOptions.body && typeof currentOptions.body === 'object' && !(currentOptions.body instanceof Blob)) {
            headers.set('Content-Type', 'application/json');
            currentOptions.body = JSON.stringify(currentOptions.body);
        }
        
        return fetch(VITE_BACKEND_API_URL + endpoint, {
            ...currentOptions,
            headers: headers,
            credentials: 'include' 
        } as RequestInit);
    };

    try {
        let response = await makeRequest(options);

        if (response && response.status === 401 && authNeeded) {
            return await refreshTokenAndRetry(endpoint, options as RequestInit, responseType);
        }

        if (!response.ok) {
            let errorDetail = 'HTTP ошибка: ' + response.status + ' ' + response.statusText;
            const contentType = response.headers.get('Content-Type');
            try {
                if (contentType?.includes('application/json')) {
                    const errorJson = await response.json();
                    if (Array.isArray(errorJson)) {
                        errorDetail = errorJson.map(err => {
                            if (typeof err === 'string') return err;
                            if (err.detail) return err.detail;
                            if (err.message) return err.message;
                            if (err.loc) {
                                const field = err.loc[err.loc.length - 1];
                                return `${field}: ${err.msg || err.message || JSON.stringify(err)}`;
                            }
                            if (typeof err === 'object') {
                                return Object.entries(err)
                                    .map(([key, value]) => {
                                        if (typeof value === 'object') {
                                            return `${key}: ${JSON.stringify(value)}`;
                                        }
                                        return `${key}: ${value}`;
                                    })
                                    .join(', ');
                            }
                            return JSON.stringify(err);
                        }).join('; ');
                    } else if (errorJson.detail) {
                        if (typeof errorJson.detail === 'object') {
                            errorDetail = Object.entries(errorJson.detail)
                                .map(([key, value]) => {
                                    if (typeof value === 'object') {
                                        return `${key}: ${JSON.stringify(value)}`;
                                    }
                                    return `${key}: ${value}`;
                                })
                                .join('; ');
                        } else {
                            errorDetail = errorJson.detail;
                        }
                    } else if (errorJson.message) {
                        errorDetail = errorJson.message;
                    } else if (typeof errorJson === 'object') {
                        errorDetail = Object.entries(errorJson)
                            .map(([key, value]) => {
                                if (typeof value === 'object') {
                                    return `${key}: ${JSON.stringify(value)}`;
                                }
                                return `${key}: ${value}`;
                            })
                            .join('; ');
                    } else {
                        errorDetail = String(errorJson);
                    }
                } else {
                    const errorText = await response.text();
                    if (errorText) errorDetail = errorText;
                }
            } catch (e) {
                console.warn('Не удалось обработать тело ответа ошибки:', e);
            }

            switch (response.status) {
                case 400:
                    errorDetail = 'Некорректный запрос: ' + errorDetail;
                    break;
                case 401:
                    errorDetail = 'Требуется авторизация: ' + errorDetail;
                    break;
                case 403:
                    errorDetail = 'Доступ запрещен: ' + errorDetail;
                    break;
                case 404:
                    errorDetail = 'Ресурс не найден: ' + errorDetail;
                    break;
                case 422:
                    errorDetail = 'Ошибка валидации: ' + errorDetail;
                    break;
                case 500:
                    errorDetail = 'Внутренняя ошибка сервера: ' + errorDetail;
                    break;
            }

            throw new Error(errorDetail);
        }
        
        if (response.status === 204) { 
             if (responseType === 'pdf') {
                throw new Error('Ожидался PDF, но сервер ответил статусом 204 No Content.');
             }
             return undefined; 
        }

        switch (responseType) {
            case 'json':
                return await response.json();
            case 'pdf':
                const pdfBlob = await response.blob();
                if (pdfBlob.size === 0) {
                    throw new Error('Сервер вернул пустой PDF.');
                }
                return URL.createObjectURL(pdfBlob);
            case 'html':
            case 'text':
                return await response.text();
            default:
                return await response.text();
        }

    } catch (error) {
        if (error instanceof Error) {
            if (error.message.toLowerCase().includes('failed to fetch') || 
                error.message.toLowerCase().includes('networkerror') ||
                (error instanceof TypeError && error.message.toLowerCase().includes('load failed'))) {
                throw new Error('Ошибка сети или сервер недоступен.');
            }
            throw error;
        }
        throw new Error(String(error));
    }
};
