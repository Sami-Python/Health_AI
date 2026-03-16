import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";

export interface GarminStatus {
    connected: boolean;
    username: string | null;
    garmin_mfa_required?: boolean;
}

export function useGarminStatus() {
    const { user } = useAuth();
    const [status, setStatus] = useState<GarminStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = useCallback(async () => {
        if (!user) {
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            const token = await user.getIdToken();
            const res = await fetchWithRetry(`${API_BASE_URL}/garmin/status`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                setStatus(data);
                setError(null);
            } else {
                throw new Error("Failed to fetch status");
            }
        } catch (e: any) {
            console.error("Failed to fetch Garmin status", e);
            setError(e.message);
            // Default to not connected on error to avoid blocking UI
            setStatus({ connected: false, username: null, garmin_mfa_required: false });
        } finally {
            setLoading(false);
        }
    }, [user]);

    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    return { status, loading, error, refreshStatus: fetchStatus };
}
