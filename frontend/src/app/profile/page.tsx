"use client";

import UserMenu from "@/components/UserMenu";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import ProfileForm from "@/components/ProfileForm";
import GarminCredentialsForm from "@/components/GarminCredentialsForm";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export default function ProfilePage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && !user) {
            router.push("/");
        }
    }, [user, loading, router]);

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
                <ProfileForm />
                <GarminCredentialsForm />
            </main>
        </div>
    );
}

