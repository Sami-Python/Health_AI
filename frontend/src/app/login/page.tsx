"use client";

import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Image from "next/image";
import { Apple } from "lucide-react";

export default function LoginPage() {
    const { user, signInWithGoogle, signInWithApple, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (user) {
            router.push("/dashboard");
        }
    }, [user, router]);

    if (loading) {
        return <div className="flex h-screen items-center justify-center">Loading...</div>;
    }

    return (
        <div className="flex h-screen w-full flex-col items-center justify-center bg-slate-950 text-white">
            <div className="flex flex-col items-center space-y-6 rounded-xl border border-slate-800 bg-slate-900/50 p-12 shadow-xl backdrop-blur-sm">
                <h1 className="text-3xl font-bold tracking-tighter">Health AI Login</h1>
                <p className="text-slate-400">Sign in to access your dashboard</p>

                <Button
                    onClick={() => signInWithGoogle()}
                    size="lg"
                    className="w-full font-bold"
                >
                    Sign in with Google
                </Button>

                <Button
                    onClick={() => signInWithApple()}
                    size="lg"
                    variant="outline"
                    className="w-full font-bold bg-black hover:bg-gray-900 text-white border-gray-700"
                >
                    <Apple className="mr-2 h-5 w-5" />
                    Sign in with Apple
                </Button>
            </div>
        </div>
    );
}
