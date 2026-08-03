"use client";

import React from "react";
import { motion } from "framer-motion";
import { Trash2, Video, CheckCircle2, AlertCircle } from "lucide-react";
import { ProcessingCard } from "./ProcessingCard";

interface ProjectCardProps {
  job: any;
  onDelete: (e: React.MouseEvent, projectId: string) => void;
  isDeleting: boolean;
  onClick: () => void;
}

export function ProjectCard({ job, onDelete, isDeleting, onClick }: ProjectCardProps) {
  // Use custom processing card for active processing state
  if (job.status === "processing" || job.status === "queued") {
    return (
      <ProcessingCard 
        job={job} 
        onDelete={onDelete} 
        isDeleting={isDeleting} 
        onClick={onClick} 
      />
    );
  }

  const isCompleted = job.status === "completed";
  const isFailed = job.status === "failed";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      onClick={onClick}
      className="group relative cursor-pointer bg-surface-elevated/40 backdrop-blur-sm border border-white/[0.06] hover:border-white/[0.12] rounded-2xl overflow-hidden transition-all duration-300 shadow-lg"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-white/[0.01] to-transparent group-hover:from-white/[0.03] transition-colors" />

      <div className="relative p-5 flex flex-col sm:flex-row sm:items-center gap-5">
        
        {/* Placeholder Thumbnail (In a real app, this might be a youtube thumbnail) */}
        <div className="w-24 h-16 sm:w-32 sm:h-20 bg-black/40 rounded-lg border border-white/[0.05] flex items-center justify-center shrink-0 overflow-hidden relative group-hover:border-white/10 transition-colors">
          <Video className="w-6 h-6 text-slate-700 group-hover:text-slate-500 transition-colors" />
          {isCompleted && (
             <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/20 to-transparent" />
          )}
        </div>

        {/* Project Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors truncate">
            {job.project_id ? `Project ${job.project_id.split("-")[0]}` : "Untitled Project"}
          </h3>
          <p className="text-sm text-slate-500 mt-0.5 truncate capitalize">
            {job.job_type ? job.job_type.replace('_', ' ') : "Karaoke Video"}
          </p>

          <div className="flex items-center gap-2 mt-3">
            {isCompleted && (
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-md">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Completed
              </span>
            )}
            {isFailed && (
              <span className="flex items-center gap-1.5 text-xs font-medium text-rose-400 bg-rose-500/10 px-2 py-1 rounded-md">
                <AlertCircle className="w-3.5 h-3.5" />
                Failed
              </span>
            )}
            
            <span className="text-xs text-slate-600 ml-1">
              • {job.created_at ? new Date(job.created_at).toLocaleDateString() : "Just now"}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="sm:pl-4 sm:border-l border-white/[0.06] flex items-center shrink-0">
           <button
             onClick={(e) => onDelete(e, job.project_id)}
             disabled={isDeleting}
             className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors group/delete"
             title="Delete Project"
           >
             {isDeleting ? (
               <div className="w-4 h-4 rounded-full border-2 border-rose-500 border-t-transparent animate-spin" />
             ) : (
               <Trash2 className="w-4 h-4 group-hover/delete:scale-110 transition-transform" />
             )}
           </button>
        </div>
      </div>
    </motion.div>
  );
}
