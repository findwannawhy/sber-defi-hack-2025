import { Link } from "@tanstack/react-router";
import { useAuth } from "@/app/providers/AuthContext";
import { useUserProfile } from "@/entities/user/model/hooks";
import { GoogleAuthButton, LogoutButton } from "@/features/auth";
import { LinkTelegramButton, UnlinkTelegramButton } from "@/features/telegram";

export function Header() {
  const { contextAccessToken, isAuthLoading } = useAuth();
  const { data: userProfile, isLoading: isProfileLoading } = useUserProfile();
  const isAuthenticated = !isAuthLoading && contextAccessToken != null;
  const showProfileLoader = isAuthenticated && isProfileLoading;
  const isTelegramLinked = isAuthenticated && !isProfileLoading && userProfile?.telegram_user_id != null && userProfile?.is_verified;

  return (
    <div className="absolute top-0 left-0 right-0 p-2 flex items-center gap-4 bg-background z-11 border-b">
      <Link to="/" className="[&.active]:font-bold mr-2 ml-4">
        Home
      </Link>
      <Link to="/contracts" className="[&.active]:font-bold mr-2">
        Контракты
      </Link>
      <Link to="/audit" className="[&.active]:font-bold">
        Аудит
      </Link>
      <Link to="/visualisation" className="[&.active]:font-bold">
        Визуализация
      </Link>

      <div className="ml-auto flex items-center gap-2 mr-4">
        {isAuthLoading ? (
          <span className="text-sm text-muted-foreground">Загрузка сессии...</span>
        ) : isAuthenticated ? (
          <>
            {showProfileLoader ? (
              <span className="text-sm text-muted-foreground">Загрузка профиля...</span>
            ) : (
              <>
                {userProfile && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mr-2">
                    <span>{userProfile.email}</span>
                    {userProfile.telegram_user_id && <span>(TG: {userProfile.telegram_user_id})</span>}
                  </div>
                )}
                {isTelegramLinked ? <UnlinkTelegramButton /> : <LinkTelegramButton />}
              </>
            )}
            <LogoutButton />
          </>
        ) : (
          <GoogleAuthButton />
        )}
      </div>
    </div>
  );
}
