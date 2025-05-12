import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from "@/shared/components/ui/dialog";
import { Button } from "@/shared/components/ui/button";
import { Copy } from "lucide-react";
import { StartLinkingResponse } from "../model/types";
import { toast } from 'react-toastify';

interface LinkTelegramDialogProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  linkData: StartLinkingResponse | null;
  linkError: string | null;
  isLoading: boolean;
  isGenerating: boolean;
  onCheckVerification: () => void;
}

export function LinkTelegramDialog({
  isOpen,
  onOpenChange,
  linkData,
  linkError,
  isLoading,
  isGenerating,
  onCheckVerification
}: LinkTelegramDialogProps) {

  const copyToClipboard = (text: string) => {
    if (!navigator.clipboard) {
      toast.error("Копирование в буфер обмена не поддерживается в вашем браузере.");
      return;
    }
    navigator.clipboard.writeText(text).then(() => {
      toast.success("Код скопирован в буфер обмена!");
    }).catch(_ => {
      toast.error("Не удалось скопировать код.");
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Привязка Telegram Аккаунта</DialogTitle>
          <DialogDescription>
            {isGenerating ? "Генерация кода, пожалуйста, подождите..." : ""}
            {linkError && <p className="text-red-500 mt-2">Ошибка: {linkError}</p>}
            {linkData && !linkError && !isGenerating && (
                <>
                    Отправьте следующий код боту <b>{linkData.bot_username}</b> в Telegram, чтобы завершить привязку.
                </>
            )}
          </DialogDescription>
        </DialogHeader>

        {linkData && !linkError && !isGenerating && (
          <div className="mt-4 p-3 bg-muted rounded-md flex items-center justify-between">
            <code className="text-lg font-mono">{linkData.code}</code>
            <Button variant="ghost" size="icon" onClick={() => copyToClipboard(linkData.code)} title="Копировать код">
                <Copy className="h-4 w-4" />
            </Button>
          </div>
        )}

        <DialogFooter className="mt-4">
             <DialogClose asChild>
                 <Button type="button" variant="outline">
                     Закрыть
                 </Button>
             </DialogClose>
             {linkData && !linkError && !isGenerating && (
                 <Button
                     type="button"
                     variant="default"
                     onClick={onCheckVerification}
                     disabled={isLoading}
                  >
                     {isLoading ? "Проверка..." : "Я отправил код, проверить"}
                 </Button>
             )}
         </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 