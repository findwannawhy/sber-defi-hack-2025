import React from 'react';
import { ContractRead } from '@/entities/contract/model/types';  
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";

interface ContractCardProps {
  contract: ContractRead;
  actions?: React.ReactNode;
}

export const ContractCard: React.FC<ContractCardProps> = ({ contract, actions }) => {
  return (
    <Card className="mb-4">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>{contract.name || 'Unnamed Contract'}</CardTitle>
            <CardDescription>{contract.network}</CardDescription>
          </div>
          {actions && <div className="ml-4 flex-shrink-0">{actions}</div>}
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground break-all">{contract.address}</p>
      </CardContent>
    </Card>
  );
}; 