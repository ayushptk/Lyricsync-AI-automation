"use client";

import React, { useMemo } from "react";
import { motion } from "framer-motion";
import { Trash2 } from "lucide-react";

interface ProcessingCardProps {
  job: any;
  onDelete: (e: React.MouseEvent, projectId: string) => void;
  isDeleting: boolean;
  onClick: () => void;
}

export function ProcessingCard({ job, onDelete, isDeleting, onClick }: ProcessingCardProps) {
  // Derive stage from progress
  const progress = job.progress || 0;
  
  const stageInfo = useMemo(() => {
    if (progress < 10) return { label: "INITIALIZING", subtext: "Setting up environment..." };
    if (progress < 30) return { label: "DOWNLOADING", subtext: "Fetching high-quality audio..." };
    if (progress < 60) return { label: "AUDIO ANALYSIS", subtext: "Separating vocals & instruments..." };
    if (progress < 85) return { label: "TRANSCRIBING", subtext: "Syncing lyrics to vocals..." };
    if (progress < 100) return { label: "RENDERING", subtext: "Generating cinematic video..." };
    return { label: "FINALIZING", subtext: "Almost ready..." };
  }, [progress]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={onClick}
      className="group relative cursor-pointer bg-surface-elevated/80 backdrop-blur-xl border border-indigo-500/20 rounded-2xl overflow-hidden shadow-[0_8px_32px_-8px_rgba(99,102,241,0.15)] transition-all duration-300"
    >
      {/* Animated Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-indigo-500/5 bg-[length:200%_auto] animate-[gradient_4s_linear_infinite]" />
      
      {/* Top subtle highlight */}
      <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-indigo-400/50 to-transparent" />

      <div className="relative p-5 sm:p-6 flex flex-col gap-5">
        <div className="flex justify-between items-start gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-slate-100 truncate">
              {job.project_id ? `Project ${job.project_id.split("-")[0]}` : "Processing Video"}
            </h3>
            
            <div className="flex items-center gap-2 mt-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
              </span>
              <span className="text-xs font-semibold text-indigo-400 tracking-wider uppercase">
                {stageInfo.label}
              </span>
            </div>
          </div>
          
          <button
             onClick={(e) => onDelete(e, job.project_id)}
             disabled={isDeleting}
             className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors group/delete shrink-0"
             title="Cancel Processing"
           >
             {isDeleting ? (
               <div className="w-4 h-4 rounded-full border-2 border-rose-500 border-t-transparent animate-spin" />
             ) : (
               <Trash2 className="w-4 h-4 group-hover/delete:scale-110 transition-transform" />
             )}
          </button>
        </div>

        {/* Progress Section */}
        <div>
           {/* Custom progress bar instead of generic one */}
           <div className="flex justify-between text-xs text-slate-400 mb-2">
             <span>{stageInfo.subtext}</span>
             <span className="font-mono text-indigo-300">{Math.round(progress)}%</span>
           </div>
           
           <div className="h-1.5 w-full bg-black/50 rounded-full overflow-hidden shadow-inner relative">
             {/* Base progress */}
             <motion.div
               className="absolute top-0 left-0 h-full bg-indigo-500"
               initial={{ width: 0 }}
               animate={{ width: `${progress}%` }}
               transition={{ duration: 0.5, ease: "easeOut" }}
             />
             {/* Processing highlight effect */}
             <div className="absolute top-0 left-0 h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full animate-[shimmer_1.5s_infinite]" />
           </div>
        </div>

      </div>
    </motion.div>
  );
}
