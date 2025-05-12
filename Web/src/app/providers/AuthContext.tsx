import React, { createContext, useState, useEffect, useContext, ReactNode, useCallback } from 'react';
import { setAuthUtils, updateApiClientAccessToken, apiClient, refreshToken, updateApiClientIsAuthorized } from '@/shared/api/client';
import { VITE_BACKEND_API_URL } from "@/shared/config";

const GOOGLE_LOGIN_URL = `${VITE_BACKEND_API_URL}/auth/login`;

interface AuthContextType {
  contextAccessToken: string | null;
  contextIsAuthorized: boolean;
  login: () => void;
  logout: () => void;
  isAuthLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [contextAccessToken, setContextAccessToken] = useState<string | null>(null);
  const [contextIsAuthorized, setContextIsAuthorized] = useState<boolean>(false);
  const [isAuthLoading, setIsAuthLoading] = useState<boolean>(true);

  // Функция: Установка аксесс токена в контексте и в apiClient
  const setAccessToken = useCallback((newToken: string | null) => {
    setContextAccessToken(newToken);
    updateApiClientAccessToken(newToken); 
  }, []); 

  // Функция: Установка авторизации в контексте и в apiClient
  const setIsAuthorized = useCallback((newIsAuthorized: boolean) => {
    setContextIsAuthorized(newIsAuthorized);
    updateApiClientIsAuthorized(newIsAuthorized);
  }, []);

  // Хук: Попытка восстановить сессию при загрузке страницы
  useEffect(() => {
    const initializeAuthSession = async () => {
      try {
        const refreshedToken = await refreshToken();
        setIsAuthorized(true);

        if (!refreshedToken) {
          setAccessToken(null);
          setIsAuthorized(false);
        }

      } catch (error) {
        setAccessToken(null);
        setIsAuthorized(false);
      } finally {
        setIsAuthLoading(false);
      }
    };

    initializeAuthSession();
  }, []);
  
  // Функция: Вход в аккаунт гугл
  const login = useCallback(() => {
    window.location.href = GOOGLE_LOGIN_URL;
  }, []);

  // Функция: Выход из аккаунта гугл
  const logout = useCallback(async () => {
    try {
      await apiClient('/auth/logout', { method: 'POST' }, true);
    } catch (error) {
      console.error('[AuthContext] Logout API call failed:', error);
    } finally {
      setAccessToken(null);
      setIsAuthorized(false);
    }
  }, [setAccessToken, setIsAuthorized]); 

  // Передаём утилиты в apiClient
  setAuthUtils(setAccessToken, logout);

  // Передаем утилиты в дочерние компоненты
  const value = { contextAccessToken, contextIsAuthorized, isAuthLoading, login, logout };
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Хук для использования контекста, чтобы не писать везде useContext(AuthContext) + проверка
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 