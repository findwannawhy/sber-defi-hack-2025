import { ReactNode } from 'react';
import { useAuth } from '@/app/providers/AuthContext';
import { useUserProfile } from '@/entities/user/model/hooks';

interface RequireAuthBannerProps {
  children: ReactNode;
}

export function RequireAuthBanner({ children }: RequireAuthBannerProps) {
  const { contextAccessToken, isAuthLoading } = useAuth();
  const { data: userProfile, isLoading: isProfileLoading } = useUserProfile();

  if (isAuthLoading || (contextAccessToken && isProfileLoading)) {
    return <div>Загрузка данных пользователя...</div>;
  }

  const isAuthenticated = contextAccessToken != null;
  const isTelegramLinked = isAuthenticated && userProfile?.telegram_user_id != null && userProfile?.is_verified;

  if (!isAuthenticated || !isTelegramLinked) {
    return (
      <div className="container mx-auto p-64 text-center">
        <h2 className="text-xl font-semibold">Доступ ограничен</h2>
        <p className="mt-2 text-gray-600">
          {isAuthenticated
            ? "Пожалуйста, привяжите и подтвердите ваш аккаунт Telegram для доступа к отслеживанию изменений контрактов."
            : "Пожалуйста, авторизуйтесь и привяжите аккаунт Telegram для доступа к отслеживанию изменений контрактов."}
        </p>
      </div>
    );
  }

  return <>{children}</>;
} 