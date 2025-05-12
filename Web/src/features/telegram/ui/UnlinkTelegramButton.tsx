import { Button } from "@/shared/components/ui/button";
import { useUserProfile } from "@/entities/user/model/hooks";
import { useUnlinkTelegram } from "../model/hooks";
import { Loader2 } from "lucide-react";

export function UnlinkTelegramButton() {

  const { data: userProfile, isLoading: isProfileLoading } = useUserProfile();
  const unlinkTelegramMutation = useUnlinkTelegram();

  const isTelegramLinked = !isProfileLoading && userProfile?.telegram_user_id != null && userProfile?.is_verified;

  const handleUnlinkClick = () => {
    unlinkTelegramMutation.mutate();
  };

  if (isProfileLoading || !isTelegramLinked) {
    return null;
  }

  return (
    <Button
      onClick={handleUnlinkClick}
      variant="outline"
      size="sm"
      disabled={unlinkTelegramMutation.isPending}
      title="Отвязать аккаунт Telegram"
    >
      {unlinkTelegramMutation.isPending ? (
        <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Отвязка...</>
      ) : (
        "Отвязать Telegram"
      )}
    </Button>
  );
} 