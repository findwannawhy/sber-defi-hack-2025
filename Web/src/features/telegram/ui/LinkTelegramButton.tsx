import { useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { useUserProfile } from "@/entities/user/model/hooks";
import { useLinkTelegram } from "../model/hooks";
import { LinkTelegramDialog } from "./LinkTelegramDialog";
import { StartLinkingResponse } from "../model/types";
import { toast } from 'react-toastify';

export function LinkTelegramButton() {
  const { data: userProfile, isLoading: isProfileLoading, refetch: refetchProfile } = useUserProfile();
  const [isLinkDialogOpen, setIsLinkDialogOpen] = useState(false);
  const [linkData, setLinkData] = useState<StartLinkingResponse | null>(null);
  const [linkError, setLinkError] = useState<string | null>(null);

  const linkTelegramMutation = useLinkTelegram();

  const handleLinkClick = () => {
      setLinkData(null);
      setLinkError(null);
      setIsLinkDialogOpen(true);

      linkTelegramMutation.mutate(undefined, {
          onSuccess: (data) => {
              setLinkData(data);
              setLinkError(null);
          },
          onError: (error) => {
              setLinkError(error.message || "Произошла неизвестная ошибка.");
              setLinkData(null);
          },
      });
  };

  const handleCheckVerification = async () => {
    try {
      const { data: updatedProfile } = await refetchProfile();
      const isNowLinked = updatedProfile?.telegram_user_id != null && updatedProfile?.is_verified;
      
      if (isNowLinked) {
        setIsLinkDialogOpen(false);
      } else {
        toast.warning("Telegram еще не привязан.");
      }
    } catch (error) {
      toast.error("Не удалось проверить привязку Telegram. Попробуйте еще раз.");
    }
  };

  const isTelegramLinked = userProfile?.telegram_user_id != null && userProfile?.is_verified;

  if (isProfileLoading || isTelegramLinked || !userProfile) {
      return null;
  }

  return (
    <>
      <Button
        onClick={handleLinkClick}
        variant="secondary"
        size="sm"
        disabled={linkTelegramMutation.isPending}
      >
        {linkTelegramMutation.isPending ? "Генерация кода..." : "Привязать Telegram"}
      </Button>

      <LinkTelegramDialog
        isOpen={isLinkDialogOpen}
        onOpenChange={setIsLinkDialogOpen}
        linkData={linkData}
        linkError={linkError}
        isLoading={isProfileLoading}
        isGenerating={linkTelegramMutation.isPending}
        onCheckVerification={handleCheckVerification}
      />
    </>
  );
} 