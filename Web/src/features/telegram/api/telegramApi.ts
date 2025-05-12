import { StartLinkingResponse } from "../model/types";
import { UserProfile } from "@/entities/user/model/types";
import { apiClient } from "@/shared/api/client";

export const startTelegramLinking = async (): Promise<StartLinkingResponse> => {
    const response = await apiClient('/users/profile/telegram/start-linking', {
        method: 'POST',
    });
    return response as StartLinkingResponse;
};

export const unlinkTelegram = async (): Promise<UserProfile> => {
    const response = await apiClient('/users/profile/telegram', {
        method: 'DELETE',
    });
    return response as UserProfile;
}; 