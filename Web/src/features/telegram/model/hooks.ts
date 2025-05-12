import { useMutation, useQueryClient } from '@tanstack/react-query';
import { startTelegramLinking, unlinkTelegram } from '../api/telegramApi';
import { StartLinkingResponse } from './types';
import { UserProfile } from '@/entities/user/model/types';
import { useAuth } from '@/app/providers/AuthContext';


export const useLinkTelegram = () => {
    return useMutation<StartLinkingResponse, Error>({
        mutationFn: startTelegramLinking,
    });
}; 

export const useUnlinkTelegram = () => {
    const queryClient = useQueryClient();
    const { contextAccessToken } = useAuth();

    return useMutation<UserProfile, Error>({
        mutationFn: unlinkTelegram,
        onSuccess: (updatedUserProfile) => {
            queryClient.invalidateQueries({ queryKey: ['userProfile', contextAccessToken] });
            queryClient.setQueryData(['userProfile', contextAccessToken], updatedUserProfile);
        }
    });
}; 