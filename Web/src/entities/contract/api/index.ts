import { ContractRead, ContractCreate } from '../model/types';
import { apiClient } from '@/shared/api/client';

// Функция для получения списка контрактов
export const fetchContracts = async (): Promise<ContractRead[]> => {
  return apiClient('/contracts');
};

// Функция для добавления нового контракта
export const addContract = async (contractData: ContractCreate): Promise<ContractRead> => {
  return apiClient('/contracts/add', {
    method: 'POST',
    body: contractData,
  });
};

// Функция для удаления контракта
export const deleteContract = async (contractId: number): Promise<void> => {
  return apiClient(`/contracts/${contractId}`, {
    method: 'DELETE',
  });
}; 