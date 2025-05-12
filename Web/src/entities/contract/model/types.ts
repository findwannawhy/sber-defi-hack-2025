export interface ContractRead {
  id: number;
  address: string;
  network: string;
  name: string | null;
  user_id: number;
}

export interface ContractCreate {
  address: string;
  network: string;
} 