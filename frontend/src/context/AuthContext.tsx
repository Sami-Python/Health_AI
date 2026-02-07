"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { onAuthStateChanged, User, GoogleAuthProvider, OAuthProvider, signInWithPopup, signOut as firebaseSignOut, Auth } from "firebase/auth";
import { getFirebaseAuth } from "../lib/firebase";
import toast from "react-hot-toast";

interface AuthContextType {
    user: User | null;
    loading: boolean;
    signInWithGoogle: () => Promise<void>;
    signInWithApple: () => Promise<void>;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [auth, setAuth] = useState<Auth | null>(null);

    // Initialize Firebase Auth on client-side only
    useEffect(() => {
        if (typeof window !== "undefined") {
            const firebaseAuth = getFirebaseAuth();
            setAuth(firebaseAuth);

            const unsubscribe = onAuthStateChanged(firebaseAuth, (currentUser) => {
                setUser(currentUser);
                setLoading(false);
            });

            return () => unsubscribe();
        }
    }, []);

    const signInWithGoogle = async () => {
        if (!auth) return;
        try {
            const provider = new GoogleAuthProvider();
            await signInWithPopup(auth, provider);
            toast.success("Successfully signed in with Google!");
        } catch (error: any) {
            console.error("Error signing in with Google", error);
            let errorMessage = "Failed to sign in with Google.";

            if (error.code === 'auth/popup-closed-by-user') {
                errorMessage = "Sign-in cancelled.";
            } else if (error.code === 'auth/cancelled-popup-request') {
                errorMessage = "Sign-in cancelled.";
            } else if (error.code === 'auth/invalid-api-key') {
                errorMessage = "Invalid API Key. Please check your Google Cloud Console configuration.";
            } else if (error.code === 'auth/unauthorized-domain') {
                errorMessage = "Unauthorized domain. Please add this domain to your Firebase Auth settings.";
            } else if (error.message) {
                errorMessage = error.message;
            }

            toast.error(errorMessage);
        }
    };

    const signInWithApple = async () => {
        if (!auth) return;
        try {
            const provider = new OAuthProvider('apple.com');
            provider.addScope('email');
            provider.addScope('name');
            await signInWithPopup(auth, provider);
            toast.success("Successfully signed in with Apple!");
        } catch (error: any) {
            console.error("Error signing in with Apple", error);
            let errorMessage = "Failed to sign in with Apple.";

            if (error.code === 'auth/popup-closed-by-user') {
                errorMessage = "Sign-in cancelled.";
            } else if (error.code === 'auth/cancelled-popup-request') {
                errorMessage = "Sign-in cancelled.";
            } else if (error.message) {
                errorMessage = error.message;
            }

            toast.error(errorMessage);
        }
    };

    const signOut = async () => {
        if (!auth) return;
        try {
            await firebaseSignOut(auth);
        } catch (error) {
            console.error("Error signing out", error);
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, signInWithGoogle, signInWithApple, signOut }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};
