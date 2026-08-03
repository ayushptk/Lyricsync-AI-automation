"use client";

import React from "react";
import { motion } from "framer-motion";
import { Waveform } from "@/components/auth/Waveform"; // Reusing the waveform from auth as requested

export function EmptyProjects() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4, ease: "easeOut" }}
      className="p-12 md:p-16 border border-white/[0.05] bg-surface-elevated/20 backdrop-blur-sm rounded-3xl flex flex-col items-center justify-center text-center shadow-inner relative overflow-hidden"
    >
      {/* Subtle ambient light */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-indigo-500/5 rounded-full blur-[80px] pointer-events-none" />
      
      <div className="relative z-10 w-full flex flex-col items-center">
        {/* Use the brand waveform for empty state, properly sized */}
        <div className="h-24 w-32 mb-6 opacity-60">
           <Waveform authStatus="syncing" />
        </div>
        
        <h3 className="text-xl font-semibold text-slate-200 mb-2">No karaoke videos yet</h3>
        <p className="text-slate-500 max-w-sm mb-8">
          Your next karaoke video starts here. Paste a YouTube link and let LyricSync do the heavy lifting.
        </p>
        
        {/* Optional empty state CTA - can just visually point to the main input above */}
        <div className="text-sm text-indigo-400/80 font-medium animate-pulse flex flex-col items-center gap-2">
          <svg className="w-5 h-5 rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
          Use the form above to create your first video
        </div>
      </div>
    </motion.div>
  );
}
