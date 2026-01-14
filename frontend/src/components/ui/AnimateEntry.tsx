"use client";

import { motion } from "framer-motion";

interface AnimateEntryProps {
    children: React.ReactNode;
    delay?: number;
    className?: string;
}

export default function AnimateEntry({ children, delay = 0, className = "" }: AnimateEntryProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: delay, ease: "easeOut" }}
            className={className}
        >
            {children}
        </motion.div>
    );
}
