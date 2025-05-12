import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from '@/shared/components/ui/button';
import { SelectExistingContract } from '@/features/select-existing-contract';
import { ManualContractInput } from '@/features/manual-contract-input';
import { useAuth } from '@/app/providers/AuthContext';
import { ContractRead, fetchContracts } from '@/entities/contract';
import { toast } from 'react-toastify';
import { useUserProfile } from '@/entities/user/model/hooks';
import { PopularContracts } from '@/features/popular-contracts/index';

interface AuditFormProps {
  onRunAudit: (address: string, network: string) => void;
  isLoading: boolean;
  error: string | null;
  actionType: 'audit' | 'visualize';
}

export const AuditForm: React.FC<AuditFormProps> = ({
  onRunAudit,
  isLoading,
  error,
  actionType
}) => {
  const { contextAccessToken } = useAuth();
  const { data: userProfile } = useUserProfile();
  const isAuthenticated = contextAccessToken != null;
  const isTelegramLinked = isAuthenticated && userProfile?.telegram_user_id != null && userProfile?.is_verified;

  const [manualAddress, setManualAddress] = useState('');
  const [selectedNetwork, setSelectedNetwork] = useState('mainnet');
  const [selectedContractId, setSelectedContractId] = useState<string | null>(null);

  const handleContractSelectionChange = (id: string | null, contract: ContractRead | null) => {
      setSelectedContractId(id);
      if (contract) {
          setManualAddress(contract.address);
          setSelectedNetwork(contract.network);
      } else {
          setManualAddress('');
          setSelectedNetwork('mainnet');
      }
  }

  const resetExistingSelection = () => {
      if (isAuthenticated) {
          setSelectedContractId(null);
      }
  }

  const handleManualAddressChange = (value: string) => {
      setManualAddress(value);
      resetExistingSelection();
  };

  const handleManualNetworkChange = (value: string) => {
      setSelectedNetwork(value);
      resetExistingSelection();
  };

  const handlePopularContractSelect = (address: string, network: string) => {
      setManualAddress(address);
      setSelectedNetwork(network);
      resetExistingSelection();
  };

  const handleTriggerAudit = () => {
      const address = selectedContractId
          ? contracts?.find((c: ContractRead) => String(c.id) === selectedContractId)?.address ?? manualAddress
          : manualAddress;
      const network = selectedContractId
          ? contracts?.find((c: ContractRead) => String(c.id) === selectedContractId)?.network ?? selectedNetwork
          : selectedNetwork;

      if (!address || !network) {
          toast.error("Необходимо указать адрес контракта и сеть.");
          return;
      }
      onRunAudit(address, network);
  };

  const { data: contracts } = useQuery<ContractRead[]>({ 
    queryKey: ['contracts', contextAccessToken],
    queryFn: () => fetchContracts(),
    enabled: !!contextAccessToken,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl font-bold">
          {actionType === 'audit' ? 'Параметры аудита' : 'Параметры визуализации'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`grid grid-cols-1 ${isAuthenticated && isTelegramLinked ? 'md:grid-cols-2' : ''} gap-6 mb-6`}>
          {isAuthenticated && isTelegramLinked && (
            <SelectExistingContract
              selectedContractId={selectedContractId}
              onContractChange={handleContractSelectionChange}
              disabled={isLoading}
            />
          )}
          <ManualContractInput
            addressValue={manualAddress}
            onAddressChange={handleManualAddressChange}
            networkValue={selectedNetwork}
            onNetworkChange={handleManualNetworkChange}
            disabled={isLoading}
            onAddressFocus={resetExistingSelection}
          />
        </div>

        <PopularContracts
          onSelect={handlePopularContractSelect}
          disabled={isLoading}
          selectedAddress={selectedContractId ? null : manualAddress}
        />

        <Button
            onClick={handleTriggerAudit}
            disabled={isLoading}
            className="bg-emerald-500 hover:bg-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-700 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
            {isLoading
              ? (actionType === 'audit' ? 'Выполнение аудита...' : 'Генерация визуализации...')
              : (actionType === 'audit' ? 'Запустить аудит' : 'Построить визуализацию')
            }
        </Button>
        {error && <p className="text-sm text-destructive mt-2 text-center">Ошибка: {error}</p>}
      </CardContent>
    </Card>
  );
}; 