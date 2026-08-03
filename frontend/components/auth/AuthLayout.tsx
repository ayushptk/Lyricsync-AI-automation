"use client";

import { motion } from "framer-motion";
import { AuthBackground } from "./AuthBackground";
import { Waveform } from "./Waveform";
import Link from "next/link";
import { useState, useEffect } from "react";
import { create } from "zustand";

interface AuthUIStore {
  status: "idle" | "signing_in" | "syncing" | "ready" | "success";
  setStatus: (status: "idle" | "signing_in" | "syncing" | "ready" | "success") => void;
}

export const useAuthUIStore = create<AuthUIStore>((set) => ({
  status: "idle",
  setStatus: (status) => set({ status }),
}));

function AuthWaveformBridge() {
  const status = useAuthUIStore((state) => state.status);
  return <Waveform authStatus={status} />;
}

export function AuthLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return null; // Avoid hydration mismatch on initial animation

  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row bg-[#0a0a0c] text-white overflow-hidden relative selection:bg-indigo-500/30">
      <AuthBackground />
      
      {/* Left Side - Hero / Visualization */}
      <div className="relative w-full md:w-[55%] lg:w-[60%] h-[40vh] md:h-screen flex flex-col justify-between p-6 md:p-12 lg:p-16 z-10 border-b md:border-b-0 md:border-r border-white/5">
        
        {/* Logo */}
        <motion.div 
          initial={{ opacity: 0, y: 10, filter: "blur(4px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          transition={{ duration: 0.8, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="font-heading font-semibold text-xl tracking-tighter"
        >
          <Link href="/">
            LyricSync<span className="text-indigo-500">.</span>
          </Link>
        </motion.div>

        {/* Waveform Container */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.4 }}
          className="absolute inset-0 md:inset-y-0 md:left-0 w-full h-full flex items-center justify-center pointer-events-auto"
        >
          <AuthWaveformBridge />
        </motion.div>

        {/* Hero Text */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 pointer-events-none mt-auto"
        >
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-medium tracking-tight mb-2 font-heading">
            Turn music into karaoke magic.
          </h1>
          <p className="text-[14px] md:text-[15px] text-slate-400 max-w-md font-sans">
            Create professional karaoke videos with AI.
          </p>
        </motion.div>
      </div>

      {/* Right Side - Auth Panel */}
      <div className="w-full md:w-[45%] lg:w-[40%] min-h-[60vh] md:min-h-screen flex items-center justify-center p-6 md:p-12 relative z-10">
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-[400px]"
        >
          {children}
        </motion.div>
      </div>
    </div>
  );
}
