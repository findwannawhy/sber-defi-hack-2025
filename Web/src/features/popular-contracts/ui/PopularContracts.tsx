import React, { useState } from 'react';
import { Button } from '@/shared/components/ui/button';

export interface PopularContract {
  name: string;
  address: string;
  network: string;
  borderColor: string;
}

interface PopularContractsProps {
  onSelect: (address: string, network: string) => void;
  disabled: boolean;
  selectedAddress?: string | null;
}

export const PopularContracts: React.FC<PopularContractsProps> = ({ 
  onSelect, 
  disabled,
  selectedAddress: externalSelectedAddress 
}) => {
  const [internalSelectedAddress, setInternalSelectedAddress] = useState<string | null>(null);
  
  const selectedAddress = externalSelectedAddress !== undefined ? externalSelectedAddress : internalSelectedAddress;

  const popularContracts: PopularContract[] = [
    {
      name: "USDC (ETH)",
      address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      network: "mainnet",
      borderColor: "border-blue-500"
    },
    {
      name: "Uniswap V3 Router (ETH)",
      address: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
      network: "mainnet",
      borderColor: "border-pink-500"
    },
    {
      name: "Aave V3 Pool (ETH)",
      address: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
      network: "mainnet",
      borderColor: "border-indigo-500"
    },
    {
      name: "Compound V3 USDC (ETH)",
      address: "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
      network: "mainnet",
      borderColor: "border-emerald-500"
    },
    // --- Arbitrum ---
    {
      name: "ARB Token (ARB)",
      address: "0x912ce59144191c1204e64559fe8253a0e49e6548",
      network: "arbitrum",
      borderColor: "border-orange-500"
    },
    {
      name: "Aave V3 Pool (ARB)",
      address: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
      network: "arbitrum",
      borderColor: "border-indigo-500"
    },
    // --- Base ---
    {
      name: "USDC (Base)",
      address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      network: "base",
      borderColor: "border-blue-500"
    },
    {
      name: "cbBTC (Base)",
      address: "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
      network: "base",
      borderColor: "border-amber-500"
    },
    {
      name: "weETH (Base)",
      address: "0x04C0599Ae5A44757c0af6F9eC3b93da8976c150A",
      network: "base",
      borderColor: "border-violet-500"
    }
  ];

  const handleContractSelect = (contract: PopularContract) => {
    setInternalSelectedAddress(contract.address);
    onSelect(contract.address, contract.network);
  };

  const getButtonStyles = (contract: PopularContract) => {
    const baseStyles = "text-sm border-2 cursor-pointer transition-colors duration-200";
    const isSelected = selectedAddress === contract.address;
    
    const colorMap: { [key: string]: string } = {
      'border-blue-500': 'bg-blue-500/10',
      'border-pink-500': 'bg-pink-500/10',
      'border-indigo-500': 'bg-indigo-500/10',
      'border-emerald-500': 'bg-emerald-500/10',
      'border-orange-500': 'bg-orange-500/10',
      'border-amber-500': 'bg-amber-500/10',
      'border-violet-500': 'bg-violet-500/10'
    };

    const hoverMap: { [key: string]: string } = {
      'border-blue-500': 'hover:bg-blue-500/10',
      'border-pink-500': 'hover:bg-pink-500/10',
      'border-indigo-500': 'hover:bg-indigo-500/10',
      'border-emerald-500': 'hover:bg-emerald-500/10',
      'border-orange-500': 'hover:bg-orange-500/10',
      'border-amber-500': 'hover:bg-amber-500/10',
      'border-violet-500': 'hover:bg-violet-500/10'
    };
    
    return `${baseStyles} ${contract.borderColor} ${hoverMap[contract.borderColor]} ${isSelected ? colorMap[contract.borderColor] : ''}`;
  };

  return (
    <div className="flex flex-wrap gap-2 mb-6">
      {popularContracts.map((contract) => (
        <Button
          key={contract.address}
          variant="outline"
          onClick={() => handleContractSelect(contract)}
          disabled={disabled}
          className={getButtonStyles(contract)}
        >
          {contract.name}
        </Button>
      ))}
    </div>
  );
}; 