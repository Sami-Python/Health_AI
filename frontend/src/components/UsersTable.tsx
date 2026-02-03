
import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/utils";
import { Users, RefreshCw, Power, CheckCircle, XCircle } from "lucide-react";
import toast from "react-hot-toast";

interface UserData {
    uid: string;
    email: string;
    display_name?: string;
    disabled: boolean;
    metadata: {
        last_sign_in: number;
        creation_time: number;
    },
    garmin_connected: boolean;
}

export default function UsersTable() {
    const { user } = useAuth();
    const [users, setUsers] = useState<UserData[]>([]);
    const [loading, setLoading] = useState(true);
    const [processingUid, setProcessingUid] = useState<string | null>(null);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const token = await user?.getIdToken();
            if (!token) return;

            const res = await fetch(`${API_BASE_URL}/admin/users`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!res.ok) throw new Error("Failed to fetch users");

            const data = await res.json();
            setUsers(data.users || []);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load users");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, [user]);

    const handleForceLogout = async (uid: string, email: string) => {
        if (!confirm(`Are you sure you want to FORCE LOGOUT ${email}? This will revoke their tokens immediately.`)) return;

        setProcessingUid(uid);
        try {
            const token = await user?.getIdToken();
            const res = await fetch(`${API_BASE_URL}/admin/revoke-tokens/${uid}`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` }
            });

            if (!res.ok) throw new Error("Failed to revoke");
            toast.success(`User ${email} logged out successfully.`);
        } catch (e) {
            toast.error("Failed to force logout");
            console.error(e);
        } finally {
            setProcessingUid(null);
        }
    };

    if (loading) {
        return (
            <div className="space-y-4 animate-pulse">
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-16 bg-slate-900/50 rounded-xl border border-slate-800" />
                ))}
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-end">
                <button
                    onClick={fetchUsers}
                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
                >
                    <RefreshCw className="h-4 w-4" /> Refresh Users
                </button>
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
                        <tr>
                            <th className="p-4 font-medium">User</th>
                            <th className="p-4 font-medium">Status</th>
                            <th className="p-4 font-medium">Activity</th>
                            <th className="p-4 font-medium text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                        {users.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="p-8 text-center text-slate-500">
                                    No users found.
                                </td>
                            </tr>
                        ) : (
                            users.map((userData) => (
                                <tr key={userData.uid} className="hover:bg-slate-800/30 transition-colors">
                                    <td className="p-4 align-middle">
                                        <div className="flex flex-col">
                                            <span className="font-medium text-slate-200">{userData.email || "No Email"}</span>
                                            <span className="text-xs text-slate-500 font-mono">{userData.uid}</span>
                                        </div>
                                    </td>
                                    <td className="p-4 align-middle space-y-2">
                                        <div className="flex flex-col gap-2">
                                            {userData.disabled ? (
                                                <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-red-500/10 text-red-400 text-xs font-medium w-fit">
                                                    <XCircle className="h-3 w-3" /> Disabled
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-green-500/10 text-green-400 text-xs font-medium w-fit">
                                                    <CheckCircle className="h-3 w-3" /> Active
                                                </span>
                                            )}

                                            {userData.garmin_connected ? (
                                                <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-medium w-fit">
                                                    <CheckCircle className="h-3 w-3" /> Garmin Connected
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-slate-800 text-slate-500 text-xs font-medium w-fit">
                                                    <XCircle className="h-3 w-3" /> Garmin Disconnected
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="p-4 align-middle text-slate-400 text-xs">
                                        <div>Created: {new Date(userData.metadata.creation_time).toLocaleDateString()}</div>
                                        <div>Last Login: {userData.metadata.last_sign_in ? new Date(userData.metadata.last_sign_in).toLocaleDateString() : 'Never'}</div>
                                    </td>
                                    <td className="p-4 align-middle text-right">
                                        <button
                                            onClick={() => handleForceLogout(userData.uid, userData.email)}
                                            disabled={processingUid === userData.uid || userData.uid === user?.uid}
                                            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-xs font-medium"
                                            title="Revoke tokens and force logout"
                                        >
                                            <Power className="h-3 w-3" />
                                            {processingUid === userData.uid ? "Revoking..." : "Force Logout"}
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
