import { useAuth } from "@/app/providers/AuthContext";
import { Button } from "@/shared/components/ui/button";

export function GoogleAuthButton() {
  const { login } = useAuth();

  return (
    <Button onClick={login} variant="default" size="sm">
      Войти через Google
    </Button>
  );
} 