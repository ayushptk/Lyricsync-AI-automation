import React from "react";
import { cn } from "./Button";
import { motion } from "framer-motion";

interface ProgressBarProps {
  progress: number;
  label?: string;
  className?: string;
}

export function ProgressBar({ progress, label, className }: ProgressBarProps) {
  const boundedProgress = Math.min(100, Math.max(0, progress));
  
  return (
    <div className={cn("w-full flex flex-col gap-2", className)}>
      {label && (
        <div className="flex justify-between text-xs font-medium text-slate-300">
          <span>{label}</span>
          <span>{Math.round(boundedProgress)}%</span>
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800 shadow-inner">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-600 to-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.5)]"
          initial={{ width: 0 }}
          animate={{ width: `${boundedProgress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
