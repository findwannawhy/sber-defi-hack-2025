import { AddContractForm } from '@/features/contract';
import { ContractsList } from '@/features/contracts-list';

export const ContractsPage: React.FC = () => {
  return (
    <div className="container mx-auto pt-20 pb-4 flex flex-col min-h-screen">
      <h1 className="text-2xl md:text-3xl font-bold mb-6 text-center md:text-left">Управление отслеживаемыми контрактами</h1>
      <AddContractForm />
      <ContractsList />
    </div>
  );
}; 