export interface UserProfile {
  id: number;
  email: string;
  name?: string;
  telegram_user_id?: number;
  is_verified: boolean;
  created_at: string;
} 