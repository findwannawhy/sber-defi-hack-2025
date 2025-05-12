import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchContracts, ContractRead } from '@/entities/contract';
import { Label } from '@/shared/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { useAuth } from '@/app/providers/AuthContext';

interface SelectExistingContractProps {
  selectedContractId: string | null;
  onContractChange: (id: string | null, contract: ContractRead | null) => void;
  disabled?: boolean;
}

export const SelectExistingContract: React.FC<SelectExistingContractProps> = ({
  selectedContractId,
  onContractChange,
  disabled
}) => {
  const { contextAccessToken } = useAuth();

  const { data: contracts, isLoading: isLoadingContracts, error: contractsError } = useQuery<ContractRead[]>({ 
    queryKey: ['contracts', contextAccessToken],
    queryFn: () => fetchContracts(),
    enabled: !!contextAccessToken,
    staleTime: 5 * 60 * 1000,
  });

  const handleValueChange = (value: string) => {
      const idValue = value === "" ? null : value;
      const contract = contracts?.find(c => String(c.id) === idValue) ?? null;
      onContractChange(idValue, contract);
  };

  return (
    <div className="p-4 border rounded-md bg-muted/50 space-y-4">
      <Label className="text-base font-semibold block mb-3">Выбрать существующий</Label>
      <div className="space-y-2">
        <Label htmlFor="existing-contract">
          Отслеживаемый контракт
        </Label>
        <Select
            value={selectedContractId ?? ""}
            onValueChange={handleValueChange}
            disabled={isLoadingContracts || disabled}
        >
            <SelectTrigger id="existing-contract">
                <SelectValue placeholder="Выберите контракт..." />
            </SelectTrigger>
            <SelectContent>
                {isLoadingContracts && <SelectItem value="loading" disabled>Загрузка...</SelectItem>}
                {contractsError && <SelectItem value="error" disabled>Ошибка загрузки</SelectItem>}
                {contracts?.map((contract) => (
                    <SelectItem key={contract.id} value={String(contract.id)}>
                        {contract.network} - {contract.name}
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
        {isLoadingContracts && <p className="text-sm text-muted-foreground mt-1">Загрузка списка контрактов...</p>}
        {contractsError && <p className="text-sm text-destructive mt-1">Ошибка загрузки контрактов: {contractsError.message}</p>}
      </div>
    </div>
  );
}; 