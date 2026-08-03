"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link2, CheckCircle2, AlertCircle } from "lucide-react";

interface CreateProjectCardProps {
  url: string;
  setUrl: (url: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isPending: boolean;
}

export function CreateProjectCard({ url, setUrl, onSubmit, isPending }: CreateProjectCardProps) {
  const [isFocused, setIsFocused] = useState(false);

  // Basic youtube url validation for UI feedback
  const isValidYoutube = url.includes("youtube.com") || url.includes("youtu.be");
  const showSuccess = url.length > 0 && isValidYoutube;
  const showError = url.length > 0 && !isValidYoutube;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.35, ease: "easeOut" }}
      className="bg-surface-elevated/40 backdrop-blur-xl border border-white/[0.08] rounded-3xl p-6 md:p-8 shadow-2xl relative overflow-hidden"
    >
      {/* Subtle background glow when valid */}
      <div 
        className={`absolute inset-0 bg-indigo-500/5 transition-opacity duration-700 ${showSuccess ? 'opacity-100' : 'opacity-0'}`} 
      />

      <div className="relative z-10">
        <h2 className="text-xl font-semibold text-slate-100">Create a new karaoke video</h2>
        <p className="text-sm text-slate-400 mt-1 mb-8">Paste a YouTube link and let LyricSync handle the rest.</p>

        <form onSubmit={onSubmit} className="space-y-5">
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Link2 
                className={`w-5 h-5 transition-colors duration-300 ${
                  isFocused ? 'text-indigo-400' : showSuccess ? 'text-emerald-400' : 'text-slate-500'
                }`} 
              />
            </div>
            
            <input
              type="text"
              className={`w-full pl-12 pr-12 py-4 bg-black/40 border transition-all duration-300 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-4 ${
                isFocused 
                  ? 'border-indigo-500/50 ring-indigo-500/10' 
                  : showSuccess 
                    ? 'border-emerald-500/30' 
                    : showError
                      ? 'border-rose-500/30'
                      : 'border-white/[0.08]'
              }`}
              placeholder="https://youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              required
              disabled={isPending}
            />

            <AnimatePresence>
              {showSuccess && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none"
                >
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                </motion.div>
              )}
              {showError && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none"
                >
                  <AlertCircle className="w-5 h-5 text-rose-400" />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          <AnimatePresence>
            {showSuccess && !isPending && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 rounded-lg">
                  <CheckCircle2 className="w-4 h-4" />
                  YouTube URL detected and ready for processing.
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <button
            type="submit"
            disabled={!showSuccess || isPending}
            className={`relative w-full h-[52px] rounded-xl font-medium flex items-center justify-center transition-all duration-300 overflow-hidden ${
              showSuccess && !isPending
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-[0_4px_20px_-4px_rgba(99,102,241,0.5)] hover:-translate-y-0.5 hover:shadow-[0_8px_24px_-4px_rgba(99,102,241,0.6)] active:translate-y-0 active:scale-[0.98]' 
                : 'bg-white/5 text-slate-500 border border-white/5 cursor-not-allowed'
            }`}
          >
            {isPending ? (
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <motion.div 
                    animate={{ scaleY: [1, 2, 1] }} 
                    transition={{ repeat: Infinity, duration: 1, delay: 0 }}
                    className="w-1 h-3 bg-white/80 rounded-full" 
                  />
                  <motion.div 
                    animate={{ scaleY: [1, 2.5, 1] }} 
                    transition={{ repeat: Infinity, duration: 1, delay: 0.2 }}
                    className="w-1 h-3 bg-white/80 rounded-full" 
                  />
                  <motion.div 
                    animate={{ scaleY: [1, 1.5, 1] }} 
                    transition={{ repeat: Infinity, duration: 1, delay: 0.4 }}
                    className="w-1 h-3 bg-white/80 rounded-full" 
                  />
                </div>
                <span>Preparing your project...</span>
              </div>
            ) : (
              <span>Start Processing</span>
            )}
          </button>
        </form>
      </div>
    </motion.div>
  );
}
