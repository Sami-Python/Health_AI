"use client";

import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
    const { user, loading, signOut } = useAuth();
    const router = useRouter();
    const [data, setData] = useState<any>(null);
    const [fetchError, setFetchError] = useState<string | null>(null);

    useEffect(() => {
        if (!loading && !user) {
            router.push("/login");
        }
    }, [user, loading, router]);

    useEffect(() => {
        const fetchData = async () => {
            if (user) {
                try {
                    const token = await user.getIdToken();
                    const res = await fetch("http://localhost:8001/goals", {
                        headers: {
                            Authorization: `Bearer ${token}`
                        }
                    });

                    if (!res.ok) {
                        throw new Error(`Failed to fetch: ${res.status}`);
                    }

                    const jsonData = await res.json();
                    setData(jsonData);
                } catch (err: any) {
                    setFetchError(err.message);
                }
            }
        };

        fetchData();
    }, [user]);

    if (loading || !user) {
        return <div className="flex h-screen items-center justify-center">Loading...</div>;
    }

    return (
        <div className="min-h-screen bg-slate-950 p-8 text-white">
            <div className="mx-auto max-w-4xl space-y-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Dashboard</h1>
                        <p className="text-slate-400">Welcome, {user.displayName}</p>
                    </div>
                    <Button variant="outline" onClick={() => signOut()}>Sign Out</Button>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
                    <h2 className="mb-4 text-xl font-semibold">Your Active Goals (Backend Data)</h2>

                    {fetchError ? (
                        <div className="text-red-400">Error fetching data: {fetchError}</div>
                    ) : data ? (
                        <pre className="overflow-auto rounded bg-black p-4 text-xs text-green-400">
                            {JSON.stringify(data, null, 2)}
                        </pre>
                    ) : (
                        <div className="animate-pulse text-slate-500">Fetching secured data...</div>
                    )}
                </div>
            </div>
        </div>
    );
}
