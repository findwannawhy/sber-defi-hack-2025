import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { addContract, ContractCreate } from '@/entities/contract';
import { Label } from '@/shared/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/shared/components/ui/radio-group';
import { Input } from '@/shared/components/ui/input';
import { Button } from '@/shared/components/ui/button';
import { useAuth } from '@/app/providers/AuthContext';
import { PopularContracts } from '@/features/popular-contracts';

interface AddContractFormProps {
  onAdded?: () => void;
}

export const AddContractForm: React.FC<AddContractFormProps> = ({ onAdded }) => {
  const [address, setAddress] = useState('');
  const [network, setNetwork] = useState('mainnet');
  const queryClient = useQueryClient();
  const { contextAccessToken } = useAuth();

  const mutation = useMutation({
    mutationFn: (newContract: ContractCreate) => addContract(newContract),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts', contextAccessToken] });
      toast.success("Контракт добавлен");
      setAddress('');
      setNetwork('');
      onAdded?.();
    },
    onError: (error: Error) => {
      const errorMessage = `Ошибка добавления: ${error.message}`;
      toast.error(errorMessage);
    },
    onMutate: () => {
      if (!contextAccessToken) {
        toast.error("Необходимо авторизоваться для добавления контракта.");
        throw new Error("User not authenticated");
      }
    }
  });

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!address || !network) {
       toast.error("Необходимо указать адрес контракта и сеть.");
      return;
    }
    if (!contextAccessToken) {
      toast.error("Необходимо авторизоваться для добавления контракта.");
      return;
    }
    mutation.mutate({ address, network });
  };

  const handlePopularContractSelect = (selectedAddress: string, selectedNetwork: string) => {
    setAddress(selectedAddress);
    setNetwork(selectedNetwork);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <form onSubmit={handleSubmit} className="space-y-4 p-4 border rounded-lg">
        <h2 className="text-xl font-semibold">Добавить контракт</h2>
        <div>
          <Label htmlFor="contract-address" className="block text-sm font-medium mb-1">
            Адрес контракта
          </Label>
          <Input
            id="contract-address"
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Введите адрес контракта..."
            disabled={mutation.isPending}
            className=""
          />
        </div>
        <div>
          <Label className="block text-sm font-medium mb-2">Сеть</Label>
          <RadioGroup
            value={network}
            onValueChange={setNetwork}
            className="flex space-x-4"
            disabled={mutation.isPending}
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="mainnet" id="network-eth" />
              <Label htmlFor="network-eth">ETH Mainnet</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="base" id="network-base" />
              <Label htmlFor="network-base">Base</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="arbitrum" id="network-arbitrum" />
              <Label htmlFor="network-arbitrum">Arbitrum</Label>
            </div>
          </RadioGroup>
        </div>
        <Button
          type="submit"
          disabled={mutation.isPending}
          className="bg-emerald-500 hover:bg-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-700 text-white font-semibold py-2 px-6 rounded-lg shadow-md hover:shadow-lg transition duration-300 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {mutation.isPending ? 'Добавление...' : 'Добавить к отслеживанию'}
        </Button>
      </form>

      <div className="p-4 border rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Популярные контракты</h2>
        <PopularContracts
          onSelect={handlePopularContractSelect}
          disabled={mutation.isPending}
        />
      </div>
    </div>
  );
}; 