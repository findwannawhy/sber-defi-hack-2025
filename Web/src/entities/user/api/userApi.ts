import { UserProfile } from "../model/types";
import { apiClient } from "@/shared/api/client";

export const fetchUserProfile = async (): Promise<UserProfile | null> => {
  try {
    const profile = await apiClient('/users/profile', { method: 'GET' });
    return profile as UserProfile;
  } catch (error: any) {
    if (error.message?.includes('Unauthorized after token refresh') || error.message?.includes('Session expired')) {
        throw error;
    }
    console.error("Error fetching user profile:", error);
    return null;
  }
}; 