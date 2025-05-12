import { useQuery } from '@tanstack/react-query';
import { fetchUserProfile } from '../api/userApi';
import { UserProfile } from './types';
import { useAuth } from '@/app/providers/AuthContext';

export const useUserProfile = () => {
  const { contextAccessToken, contextIsAuthorized, isAuthLoading } = useAuth();

  return useQuery<UserProfile | null>({
      queryKey: ['userProfile', contextAccessToken],
      queryFn: fetchUserProfile,
      enabled: !isAuthLoading && contextIsAuthorized,
      staleTime: 5 * 60 * 1000,
      retry: (failureCount, error: any) => {
        if (error.message?.includes('Unauthorized after token refresh') || error.message?.includes('Session expired')) {
            return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: true,
  });
}; 