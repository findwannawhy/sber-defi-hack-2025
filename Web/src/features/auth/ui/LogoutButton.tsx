import { useAuth } from "@/app/providers/AuthContext";
import { Button } from "@/shared/components/ui/button";

export function LogoutButton() {
  const { logout } = useAuth();

  return (
    <Button onClick={logout} variant="outline" size="sm">
      Выйти
    </Button>
  );
} 