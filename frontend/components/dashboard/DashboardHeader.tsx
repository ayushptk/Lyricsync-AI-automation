"use client";

import React from "react";
import { motion } from "framer-motion";
import { UserMenu } from "./UserMenu";

interface DashboardHeaderProps {
  user: {
    email?: string;
    // other user props
  } | null;
}

export function DashboardHeader({ user }: DashboardHeaderProps) {
  // Derive first name from email or generic
  const firstName = user?.email?.split("@")[0] || "User";
  // Capitalize first letter
  const formattedName = firstName.charAt(0).toUpperCase() + firstName.slice(1);

  return (
    <header className="flex justify-between items-center mb-10 max-w-[1400px] mx-auto w-full pt-4">
      <div className="flex flex-col">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="flex items-center gap-3"
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            LyricSync AI
          </h1>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1, ease: "easeOut" }}
          className="mt-3"
        >
          <h2 className="text-2xl font-semibold text-slate-100">
            Good evening, {formattedName}
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Ready to create your next karaoke video?
          </p>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="flex items-center gap-6"
      >
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.02] border border-white/[0.05]">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
          <span className="text-xs font-medium text-slate-300">System Operational</span>
        </div>
        
        <UserMenu email={user?.email} firstName={formattedName} />
      </motion.div>
    </header>
  );
}
