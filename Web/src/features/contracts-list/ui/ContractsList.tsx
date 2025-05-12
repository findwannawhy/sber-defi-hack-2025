import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchContracts, ContractRead } from '@/entities/contract';
import { ContractCard } from '@/entities/contract';
import { DeleteContractButton } from '@/features/contract';
import { useAuth } from '@/app/providers/AuthContext';

export const ContractsList: React.FC = () => {
  const { contextAccessToken } = useAuth();
  
  const { data: contracts, isLoading, error } = useQuery<ContractRead[], Error>({
    queryKey: ['contracts', contextAccessToken],
    queryFn: () => fetchContracts(),
    enabled: !!contextAccessToken,
  });

  if (!contextAccessToken && !isLoading) {
    return <div>Пожалуйста, войдите, чтобы увидеть список контрактов.</div>;
  }

  if (isLoading) {
    return <div>Загрузка списка контрактов...</div>;
  }

  if (error) {
    return <div className="text-red-600">Ошибка загрузки: {error.message}</div>;
  }

  if (!contracts || contracts.length === 0) {
    return <div>Нет добавленных контрактов.</div>;
  }

  return (
    <>
      {contracts.map((contract) => (
        <ContractCard
          key={contract.id}
          contract={contract}
          actions={
            <DeleteContractButton
              contractId={contract.id}
            />
          }
        />
      ))}
    </>
  );
}; 