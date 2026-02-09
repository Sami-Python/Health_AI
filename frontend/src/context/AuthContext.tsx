"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { onAuthStateChanged, User, GoogleAuthProvider, OAuthProvider, signInWithPopup, signOut as firebaseSignOut, Auth, setPersistence, browserLocalPersistence, browserSessionPersistence } from "firebase/auth";
import { doc, onSnapshot, setDoc, getFirestore } from "firebase/firestore";
import { getFirebaseAuth, getFirebaseDb } from "../lib/firebase";
import toast from "react-hot-toast";

interface AuthContextType {
    user: User | null;
    loading: boolean;
    signInWithGoogle: (rememberMe?: boolean) => Promise<void>;
    signInWithApple: (rememberMe?: boolean) => Promise<void>;
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
            // TEST MODE BYPASS
            // Check process.env (build time) OR window property (runtime/test injection)
            const isTestMode = process.env.NEXT_PUBLIC_ENABLE_TEST_AUTH === 'true' ||
                (window as any)._TEST_MODE_AUTH === true;

            if (isTestMode) {
                console.log("⚠️ TEST MODE: Authentication Bypassed");
                setUser({
                    uid: "test-user-id",
                    email: "test@example.com",
                    displayName: "Test User",
                    emailVerified: true,
                    isAnonymous: false,
                    metadata: {},
                    providerData: [],
                    refreshToken: "",
                    tenantId: null,
                    delete: async () => { },
                    getIdToken: async () => "mock-token",
                    getIdTokenResult: async () => ({
                        token: "mock-token",
                        claims: {},
                        authTime: new Date().toISOString(),
                        issuedAtTime: new Date().toISOString(),
                        expirationTime: new Date().toISOString(),
                        signInProvider: "google.com",
                        signInSecondFactor: null
                    }),
                    reload: async () => { },
                    toJSON: () => ({}),
                    phoneNumber: null,
                    photoURL: null
                } as any);
                setLoading(false);
                return;
            }

            const firebaseAuth = getFirebaseAuth();
            setAuth(firebaseAuth);

            const unsubscribe = onAuthStateChanged(firebaseAuth, (currentUser) => {
                setUser(currentUser);
                setLoading(false);
            });

            return () => unsubscribe();
        }
    }, []);

    // Session Management Listener
    useEffect(() => {
        if (user && typeof window !== "undefined") {
            const db = getFirebaseDb();
            const userRef = doc(db, "users", user.uid);
            const uid = user.uid;

            // 1. Get or Create Local Session ID
            let localSessionId = localStorage.getItem(`session_${uid}`);

            // If we have a user but no session ID (e.g. first load after clear cache),
            // we must claim this session to prevent immediate logout loop if we enforced strict checking.
            // But usually signIn sets this. If auto-login, we might need one.
            if (!localSessionId) {
                // If auto-logged in but no session ID, assume this is a valid session and claim it?
                // Or generate one.
                localSessionId = crypto.randomUUID();
                localStorage.setItem(`session_${uid}`, localSessionId);
                // We should update Firestore to reflect this is the new active session
                setDoc(userRef, { activeSessionId: localSessionId }, { merge: true }).catch(err => console.error("Failed to update session", err));
            }

            // 2. Listen to Firestore
            const unsubscribeSession = onSnapshot(userRef, (snapshot) => {
                const data = snapshot.data();
                if (data?.activeSessionId && data.activeSessionId !== localSessionId) {
                    console.warn(`Session Mismatch! Remote: ${data.activeSessionId}, Local: ${localSessionId}`);
                    toast.error("You have been logged out because a new session was started on another device.");
                    signOut(); // Force logout
                }
            });

            return () => unsubscribeSession();
        }
    }, [user]);

    const signInWithGoogle = async (rememberMe: boolean = true) => {
        // TEST MODE BYPASS
        const isTestMode = process.env.NEXT_PUBLIC_ENABLE_TEST_AUTH === 'true' ||
            (typeof window !== 'undefined' && (window as any)._TEST_MODE_AUTH === true);

        if (isTestMode) {
            toast.success("Successfully signed in with Google (Test Mode)!");
            return;
        }

        if (!auth) return;
        try {
            await setPersistence(auth, rememberMe ? browserLocalPersistence : browserSessionPersistence);
            const provider = new GoogleAuthProvider();
            const result = await signInWithPopup(auth, provider);

            // Session Management: Start new session
            if (result.user) {
                const sessionId = crypto.randomUUID();
                localStorage.setItem(`session_${result.user.uid}`, sessionId);
                const db = getFirebaseDb();
                await setDoc(doc(db, "users", result.user.uid), { activeSessionId: sessionId }, { merge: true });
            }

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

    const signInWithApple = async (rememberMe: boolean = true) => {
        if (!auth) return;
        try {
            await setPersistence(auth, rememberMe ? browserLocalPersistence : browserSessionPersistence);
            const provider = new OAuthProvider('apple.com');
            provider.addScope('email');
            provider.addScope('name');
            const result = await signInWithPopup(auth, provider);

            // Session Management: Start new session
            if (result.user) {
                const sessionId = crypto.randomUUID();
                localStorage.setItem(`session_${result.user.uid}`, sessionId);
                const db = getFirebaseDb();
                await setDoc(doc(db, "users", result.user.uid), { activeSessionId: sessionId }, { merge: true });
            }

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
