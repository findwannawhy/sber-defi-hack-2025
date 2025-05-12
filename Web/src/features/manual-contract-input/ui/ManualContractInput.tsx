import React from 'react';
import { Label } from '@/shared/components/ui/label';
import { Input } from '@/shared/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/shared/components/ui/radio-group';

interface ManualContractInputProps {
  addressValue: string;
  onAddressChange: (value: string) => void;
  networkValue: string;
  onNetworkChange: (value: string) => void;
  disabled?: boolean;
  onAddressFocus?: () => void;
}

export const ManualContractInput: React.FC<ManualContractInputProps> = ({
  addressValue,
  onAddressChange,
  networkValue,
  onNetworkChange,
  disabled,
  onAddressFocus
}) => {
  return (
    <div className="p-4 border rounded-md bg-muted/50 space-y-4">
      <Label className="text-base font-semibold block mb-3">Ввести вручную</Label>
      <div className="space-y-2">
        <Label htmlFor="manual-address">Адрес контракта</Label>
        <Input
            id="manual-address"
            type="text"
            value={addressValue}
            onChange={(e) => onAddressChange(e.target.value)}
            placeholder="0x..."
            disabled={disabled}
            onFocus={onAddressFocus}
        />
      </div>
      <div className="space-y-2">
        <Label>Сеть</Label>
        <RadioGroup
            value={networkValue}
            className="flex items-center space-x-4 pt-1"
            disabled={disabled}
            onValueChange={onNetworkChange}
        >
            <div className="flex items-center space-x-2">
                <RadioGroupItem value="mainnet" id="manual-network-eth" />
                <Label htmlFor="manual-network-eth" className="font-normal">ETH Mainnet</Label>
            </div>
            <div className="flex items-center space-x-2">
                <RadioGroupItem value="base" id="manual-network-base" />
                <Label htmlFor="manual-network-base" className="font-normal">Base</Label>
            </div>
            <div className="flex items-center space-x-2">
                <RadioGroupItem value="arbitrum" id="manual-network-arbitrum" />
                <Label htmlFor="manual-network-arbitrum" className="font-normal">Arbitrum</Label>
            </div>
        </RadioGroup>
      </div>
    </div>
  );
}; 