"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { onAuthStateChanged, User, GoogleAuthProvider, OAuthProvider, signInWithPopup, signOut as firebaseSignOut, Auth } from "firebase/auth";
import { getFirebaseAuth } from "../lib/firebase";

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
        } catch (error) {
            console.error("Error signing in with Google", error);
        }
    };

    const signInWithApple = async () => {
        if (!auth) return;
        try {
            const provider = new OAuthProvider('apple.com');
            provider.addScope('email');
            provider.addScope('name');
            await signInWithPopup(auth, provider);
        } catch (error) {
            console.error("Error signing in with Apple", error);
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
