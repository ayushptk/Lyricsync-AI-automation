"use client";

import React from "react";
import { motion } from "framer-motion";
import { PlaySquare, Activity, Zap } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
  delay?: number;
}

export function StatCard({ title, value, icon, description, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      whileHover={{ y: -2 }}
      className="group relative bg-surface-elevated/50 backdrop-blur-md border border-white/[0.06] hover:border-white/10 rounded-2xl p-5 transition-all duration-300"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/0 via-transparent to-indigo-500/0 group-hover:from-indigo-500/5 transition-colors duration-500 rounded-2xl" />
      
      <div className="relative z-10 flex flex-col h-full justify-between gap-4">
        <div className="flex justify-between items-start">
          <h3 className="text-xs font-semibold text-slate-400 tracking-wider uppercase">{title}</h3>
          <div className="p-2 rounded-xl bg-white/[0.03] text-indigo-400 group-hover:text-indigo-300 group-hover:bg-white/[0.06] transition-colors duration-300">
            {icon}
          </div>
        </div>
        
        <div>
          <div className="text-3xl font-bold text-slate-100 tracking-tight">
            {value}
          </div>
          <div className="text-xs text-slate-500 mt-1 min-h-[16px]">
            {description}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

interface StatsGridProps {
  totalJobs: number;
  processingJobs: number;
}

export function StatsGrid({ totalJobs, processingJobs }: StatsGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10 w-full">
      <StatCard
        title="Total Videos"
        value={totalJobs}
        description={totalJobs === 0 ? "No videos generated yet" : "Across all projects"}
        icon={<PlaySquare className="w-5 h-5" />}
        delay={0.15}
      />
      <StatCard
        title="Processing"
        value={processingJobs}
        description={processingJobs > 0 ? "Currently active jobs" : "All queues clear"}
        icon={<Activity className="w-5 h-5" />}
        delay={0.25}
      />
      <StatCard
        title="Credits Remaining"
        value="Unlimited"
        description="Pro Plan Active"
        icon={<Zap className="w-5 h-5" />}
        delay={0.35}
      />
    </div>
  );
}
