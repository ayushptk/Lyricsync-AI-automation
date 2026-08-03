"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LogOut, Settings, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";

interface UserMenuProps {
  email: string | undefined;
  firstName: string;
}

export function UserMenu({ email, firstName }: UserMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();
  const { setUser } = useAuthStore();

  const handleLogout = () => {
    setUser(null);
    router.push("/login");
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 py-2 px-3 rounded-full hover:bg-white/5 border border-transparent hover:border-white/10 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
      >
        <div className="w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-medium border border-indigo-500/30">
          {firstName.charAt(0).toUpperCase()}
        </div>
        <div className="hidden md:flex items-center gap-2">
          <span className="text-sm font-medium text-slate-200">{firstName}</span>
          <svg className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div 
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -4, scale: 0.98 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 mt-2 w-56 bg-surface border border-white/10 rounded-lg shadow-2xl z-50 overflow-hidden"
            >
              <div className="p-4 border-b border-white/5 bg-white/[0.02]">
                <p className="text-sm font-medium text-slate-200 truncate">{firstName}</p>
                <p className="text-xs text-slate-400 truncate mt-0.5">{email}</p>
              </div>
              <div className="p-1">
                <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-slate-100 hover:bg-white/5 rounded-md transition-colors">
                  <User className="w-4 h-4 text-slate-400" />
                  Account
                </button>
                <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-slate-100 hover:bg-white/5 rounded-md transition-colors">
                  <Settings className="w-4 h-4 text-slate-400" />
                  Settings
                </button>
              </div>
              <div className="p-1 border-t border-white/5">
                <button 
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-md transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
