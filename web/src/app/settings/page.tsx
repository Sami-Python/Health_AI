"use client";

import UserMenu from "@/components/UserMenu";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, Trash2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/utils";

export default function SettingsPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [isDeleting, setIsDeleting] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    useEffect(() => {
        if (!loading && !user) {
            router.push("/");
        }
    }, [user, loading, router]);

    const handleDeleteAccount = async () => {
        if (!user) return;
        setIsDeleting(true);
        setDeleteError(null);

        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_BASE_URL}/account`, {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${token}`,
                },
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Failed to delete account");
            }

            // Success: storage and auth user are gone.
            // Client side signout might be needed to clear context, 
            // but the token is now invalid anyway.
            // We force a hard reload or redirect to allow AuthContext to detect null.
            window.location.href = "/";

        } catch (err: any) {
            setDeleteError(err.message);
            setIsDeleting(false);
            setShowConfirm(false);
        }
    };

    if (loading || !user) return null;

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">
            {/* Header */}
            <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-4 py-3">
                <div className="mx-auto flex max-w-5xl items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Link href="/" className="flex items-center gap-1 text-slate-400 hover:text-white transition-colors">
                            <ChevronLeft className="h-5 w-5" />
                            <span className="hidden sm:inline-block font-medium text-sm">Dashboard</span>
                        </Link>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
                            Settings
                        </h1>
                    </div>
                    <UserMenu />
                </div>
            </header>

            <main className="mx-auto max-w-5xl p-4 md:p-8 space-y-8">

                {/* General Settings Section (Placeholder for future) */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
                    <h2 className="text-lg font-semibold text-white mb-4">General</h2>
                    <p className="text-slate-400 text-sm">App preferences are currently managed automatically (Dark Mode, Metric Units).</p>
                </div>

                {/* Danger Zone */}
                <div className="rounded-xl border border-red-900/50 bg-red-950/10 p-6">
                    <h2 className="text-lg font-semibold text-red-500 mb-2 flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5" />
                        Danger Zone
                    </h2>
                    <p className="text-slate-400 text-sm mb-6 max-w-xl">
                        Deleting your account is permanent. All your data (workouts, goals, profile) and your login credentials will be permanently removed. This action cannot be undone.
                    </p>

                    <Button
                        variant="destructive"
                        onClick={() => setShowConfirm(true)}
                        className="bg-red-600 hover:bg-red-700 text-white"
                    >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete Account
                    </Button>
                </div>
            </main>

            {/* Confirmation Modal */}
            {showConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
                    <div className="w-full max-w-md rounded-xl border border-red-900/50 bg-slate-900 p-6 shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="flex flex-col items-center text-center gap-4">
                            <div className="p-3 bg-red-900/20 rounded-full">
                                <AlertTriangle className="h-8 w-8 text-red-500" />
                            </div>
                            <h3 className="text-xl font-bold text-white">Are you absolutely sure?</h3>
                            <p className="text-slate-400 text-sm">
                                This action cannot be undone. This will permanently delete your account and remove your data from our servers.
                            </p>

                            {deleteError && (
                                <div className="w-full p-2 bg-red-950/50 border border-red-900 rounded text-red-200 text-sm">
                                    Error: {deleteError}
                                </div>
                            )}

                            <div className="flex gap-3 w-full mt-2">
                                <Button
                                    variant="outline"
                                    onClick={() => setShowConfirm(false)}
                                    className="flex-1 border-slate-700 hover:bg-slate-800 text-slate-300"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    variant="destructive"
                                    onClick={handleDeleteAccount}
                                    disabled={isDeleting}
                                    className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                                >
                                    {isDeleting ? 'Deleting...' : 'Yes, Delete Account'}
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
