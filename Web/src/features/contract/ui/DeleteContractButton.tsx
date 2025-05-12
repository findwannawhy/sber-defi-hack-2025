import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteContract } from '@/entities/contract';
import { toast } from 'react-toastify';
import { Button } from "@/shared/components/ui/button";
import { useAuth } from '@/app/providers/AuthContext';

interface DeleteContractButtonProps {
  contractId: number;
  onDeleted?: () => void;
}

export const DeleteContractButton: React.FC<DeleteContractButtonProps> = ({ contractId, onDeleted }) => {
  const queryClient = useQueryClient();
  const { contextAccessToken } = useAuth();

  const mutation = useMutation({
    mutationFn: () => deleteContract(contractId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts', contextAccessToken] });
      toast.success("Контракт удален успешно");
      onDeleted?.();
    },
    onError: (error: Error) => {
      const errorMessage = `Ошибка удаления контракта: ${error.message}`;
      toast.error(errorMessage);
    },
    onMutate: () => {
      if (!contextAccessToken) {
        toast.error("Необходимо авторизоваться для удаления контракта.");
        throw new Error("User not authenticated");
      }
    }
  });

  const handleClick = () => {
    if (!contextAccessToken) {
      toast.error("Необходимо авторизоваться для удаления контракта.");
      return;
    }
    mutation.mutate();
  }

  return (
    <Button
      variant="outline"
      onClick={handleClick}
      disabled={mutation.isPending || !contextAccessToken}
      className="font-semibold py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
    >
      {mutation.isPending ? 'Удаление...' : 'Удалить'}
    </Button>
  );
}; 