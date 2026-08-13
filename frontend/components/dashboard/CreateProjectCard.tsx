"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Link2, CheckCircle2, AlertCircle, X,
  Download, Wand2, Volume2,
  FileText, Captions, Film, PlaySquare, Loader2,
  Waves
} from "lucide-react";
import type { Job } from "@/app/dashboard/page";

// ─── Pipeline stage definitions ────────────────────────────────────────────
const PIPELINE_STAGES = [
  { id: "download",    label: "Download Audio",       icon: Download,  start: 5,   end: 15  },
  { id: "prepare",     label: "Prepare Audio",         icon: Waves,     start: 15,  end: 25  },
  { id: "separate",    label: "Separate Vocals",        icon: Wand2,     start: 25,  end: 50  },
  { id: "normalize",   label: "Normalize Loudness",     icon: Volume2,   start: 50,  end: 65  },
  { id: "transcribe",  label: "Transcribe Lyrics",      icon: FileText,  start: 65,  end: 82  },
  { id: "subtitles",   label: "Generate Subtitles",     icon: Captions,  start: 82,  end: 85  },
  { id: "render",      label: "Render Video",           icon: Film,      start: 85,  end: 100 },
] as const;

type StageStatus = "pending" | "active" | "done" | "error";

function getStageStatus(progress: number, jobStatus: string, stageStart: number, stageEnd: number): StageStatus {
  if (jobStatus === "failed") {
    if (progress >= stageEnd) return "done";
    if (progress >= stageStart) return "error";
    return "pending";
  }
  if (jobStatus === "completed" || progress >= stageEnd) return "done";
  if (progress >= stageStart) return "active";
  return "pending";
}

function parseLogLines(rawLog: string | null | undefined): { text: string; isError: boolean }[] {
  if (!rawLog) return [];
  return rawLog
    .split("\n")
    .map(l => l.trim())
    .filter(l => l.length > 0)
    .map(l => ({ text: l, isError: l.startsWith("⚠ ERROR:") || l.startsWith("ERROR:") }));
}

interface CreateProjectCardProps {
  url: string;
  setUrl: (url: string) => void;
  aspectRatio: string;
  setAspectRatio: (val: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onAutomationSubmit: (e: React.MouseEvent) => void;
  isPending: boolean;
  isAutomationPending: boolean;
  activeJob?: Job | null;
  onClearActiveJob?: () => void;
}



export function CreateProjectCard({
  url, setUrl, aspectRatio, setAspectRatio,
  onSubmit, onAutomationSubmit,
  isPending, isAutomationPending,
  activeJob, onClearActiveJob,
}: CreateProjectCardProps) {
  const [isFocused, setIsFocused] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  const isValidYoutube = url.includes("youtube.com") || url.includes("youtu.be");
  const showSuccess = url.length > 0 && isValidYoutube;
  const showError   = url.length > 0 && !isValidYoutube;

  const progress  = activeJob?.progress ?? 0;
  const jobStatus = activeJob?.status ?? "queued";
  const logLines  = parseLogLines(activeJob?.error_log);
  const isFinished = jobStatus === "completed" || jobStatus === "failed";
  const isFailed   = jobStatus === "failed";

  const barColor = isFailed
    ? "from-rose-600 to-rose-400"
    : jobStatus === "completed"
    ? "from-emerald-600 to-emerald-400"
    : "from-indigo-600 to-violet-500";

  // Auto-scroll log to bottom on new entries
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logLines.length]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.35, ease: "easeOut" }}
      className="bg-surface-elevated/40 backdrop-blur-xl border border-white/[0.08] rounded-3xl p-6 md:p-8 shadow-2xl relative overflow-hidden"
    >
      {/* Ambient glow */}
      <div className={`absolute inset-0 bg-indigo-500/5 transition-opacity duration-700 pointer-events-none ${
        (activeJob && !isFailed) || showSuccess ? "opacity-100" : "opacity-0"
      }`} />

      <div className="relative z-10">
        <h2 className="text-xl font-semibold text-slate-100">Create a new karaoke video</h2>
        <p className="text-sm text-slate-400 mt-1 mb-6">Paste a YouTube link and let LyricSync handle the rest.</p>

        <form onSubmit={onSubmit} className="space-y-5">
          {/* URL Input */}
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Link2 className={`w-5 h-5 transition-colors duration-300 ${
                isFocused ? "text-indigo-400" : showSuccess ? "text-emerald-400" : "text-slate-500"
              }`} />
            </div>
            <input
              type="text"
              className={`w-full pl-12 pr-12 py-4 bg-black/40 border transition-all duration-300 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-4 ${
                isFocused ? "border-indigo-500/50 ring-indigo-500/10"
                : showSuccess ? "border-emerald-500/30"
                : showError ? "border-rose-500/30"
                : "border-white/[0.08]"
              }`}
              placeholder="https://youtube.com/watch?v=..."
              value={url}
              onChange={e => setUrl(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              required
              disabled={isPending || isAutomationPending || !!activeJob}
            />
            <AnimatePresence>
              {showSuccess && (
                <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                </motion.div>
              )}
              {showError && (
                <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                  <AlertCircle className="w-5 h-5 text-rose-400" />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Aspect Ratio */}
          <div className="flex gap-4">
            {(["16:9", "9:16"] as const).map(ratio => (
              <button key={ratio} type="button"
                onClick={() => setAspectRatio(ratio)}
                disabled={!!activeJob}
                className={`flex-1 py-3 rounded-xl border text-sm font-medium transition-all ${
                  aspectRatio === ratio ? "bg-yellow-600/20 border-yellow-600/50 text-yellow-200" : "bg-black/20 border-white/10 text-slate-400 hover:bg-white/5"
                } ${activeJob ? "opacity-40 cursor-not-allowed" : ""}`}
              >
                {ratio === "16:9" ? "Standard (16:9)" : "TikTok / Shorts (9:16)"}
              </button>
            ))}
          </div>

          {/* URL ready hint */}
          <AnimatePresence>
            {showSuccess && !isPending && !isAutomationPending && !activeJob && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 rounded-lg">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  YouTube URL detected and ready for processing.
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── ACTIVE JOB PROGRESS PANEL ── */}
          <AnimatePresence>
            {activeJob && (
              <motion.div
                key="progress-panel"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className={`rounded-2xl border overflow-hidden ${
                  isFailed ? "border-rose-500/30 bg-rose-950/20"
                  : jobStatus === "completed" ? "border-emerald-500/30 bg-emerald-950/20"
                  : "border-indigo-500/30 bg-black/40"
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between px-5 pt-4 pb-3">
                  <div className="flex items-center gap-2">
                    {jobStatus === "completed" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : isFailed ? (
                      <AlertCircle className="w-4 h-4 text-rose-400" />
                    ) : (
                      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }}>
                        <Loader2 className="w-4 h-4 text-indigo-400" />
                      </motion.div>
                    )}
                    <span className={`text-sm font-semibold ${
                      isFailed ? "text-rose-300" : jobStatus === "completed" ? "text-emerald-300" : "text-indigo-300"
                    }`}>
                      {jobStatus === "completed" ? "Pipeline Complete ✓"
                        : isFailed ? "Pipeline Failed"
                        : jobStatus === "queued" ? "Queued — waiting to start..."
                        : "Processing Pipeline"}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold font-mono text-slate-200">{Math.round(progress)}%</span>
                    {isFinished && (
                      <button type="button" onClick={onClearActiveJob}
                        className="text-slate-500 hover:text-white bg-white/5 hover:bg-white/10 rounded-full p-1 transition-all">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Animated progress bar */}
                <div className="px-5 mb-4">
                  <div className="h-2.5 bg-black/50 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full rounded-full bg-gradient-to-r ${barColor}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                    />
                  </div>
                </div>

                {/* Step timeline */}
                <div className="px-5 mb-4 grid grid-cols-1 gap-1.5">
                  {PIPELINE_STAGES.map((stage, idx) => {
                    const status = getStageStatus(progress, jobStatus, stage.start, stage.end);
                    const Icon = stage.icon;
                    return (
                      <div key={stage.id}
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-500 ${
                          status === "active" ? "bg-indigo-500/10 border border-indigo-500/20"
                          : status === "error" ? "bg-rose-500/10 border border-rose-500/20"
                          : status === "done" ? "opacity-60"
                          : "opacity-25"
                        }`}
                      >
                        {/* Status bubble */}
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${
                          status === "done" ? "bg-emerald-500/20 text-emerald-400"
                          : status === "active" ? "bg-indigo-500/30 text-indigo-300"
                          : status === "error" ? "bg-rose-500/20 text-rose-400"
                          : "bg-white/5 text-slate-600"
                        }`}>
                          {status === "done" ? <CheckCircle2 className="w-3.5 h-3.5" />
                           : status === "active" ? (
                            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}>
                              <Loader2 className="w-3.5 h-3.5" />
                            </motion.div>
                          ) : status === "error" ? <AlertCircle className="w-3.5 h-3.5" />
                           : <span>{idx + 1}</span>}
                        </div>
                        {/* Stage icon */}
                        <Icon className={`w-3.5 h-3.5 shrink-0 ${
                          status === "done" ? "text-emerald-400"
                          : status === "active" ? "text-indigo-400"
                          : status === "error" ? "text-rose-400"
                          : "text-slate-600"
                        }`} />
                        {/* Label */}
                        <span className={`text-xs font-medium flex-1 ${
                          status === "done" ? "text-slate-300"
                          : status === "active" ? "text-indigo-200"
                          : status === "error" ? "text-rose-300"
                          : "text-slate-600"
                        }`}>{stage.label}</span>
                        {/* Progress range badge */}
                        <span className="text-[10px] text-slate-600 font-mono">{stage.start}–{stage.end}%</span>
                      </div>
                    );
                  })}
                </div>

                {/* Live log terminal */}
                {logLines.length > 0 && (
                  <div className="mx-5 mb-5 bg-black/60 border border-white/[0.05] rounded-xl overflow-hidden">
                    {/* Terminal title bar */}
                    <div className="flex items-center gap-2 px-3 py-2 border-b border-white/[0.05] bg-white/[0.02]">
                      <div className="flex gap-1">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500/70" />
                        <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/70" />
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono ml-1">pipeline.log</span>
                    </div>
                    {/* Log lines */}
                    <div className="p-3 max-h-40 overflow-y-auto font-mono text-[11px] leading-5 space-y-0.5 scroll-smooth">
                      {logLines.map((line, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -4 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.2 }}
                          className={line.isError ? "text-rose-400" : "text-slate-400"}
                        >
                          <span className="text-slate-600 mr-2 select-none">{String(i + 1).padStart(2, "0")}│</span>
                          {line.text}
                        </motion.div>
                      ))}
                      <div ref={logEndRef} />
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── ACTION BUTTONS (shown only when no active job) ── */}
          {!activeJob && (
            <div className="flex flex-col gap-3">
              <button
                type="submit"
                disabled={!showSuccess || isPending || isAutomationPending}
                className={`relative w-full h-[52px] rounded-xl font-medium flex items-center justify-center transition-all duration-300 overflow-hidden ${
                  showSuccess && !isPending && !isAutomationPending
                    ? "bg-accent hover:bg-accent-hover text-white shadow-[0_4px_20px_-4px_rgba(202,138,4,0.5)] hover:-translate-y-0.5 hover:shadow-[0_8px_24px_-4px_rgba(202,138,4,0.6)] active:translate-y-0 active:scale-[0.98]"
                    : "bg-white/5 text-slate-500 border border-white/5 cursor-not-allowed"
                }`}
              >
                {isPending ? (
                  <div className="flex items-center gap-2">
                    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}>
                      <Loader2 className="w-4 h-4" />
                    </motion.div>
                    <span>Preparing your project...</span>
                  </div>
                ) : <span>Start Processing</span>}
              </button>

              <button
                type="button"
                onClick={onAutomationSubmit}
                disabled={!showSuccess || isPending || isAutomationPending}
                className={`relative w-full h-[52px] rounded-xl font-medium flex items-center justify-center gap-2 transition-all duration-300 overflow-hidden ${
                  showSuccess && !isPending && !isAutomationPending
                    ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_4px_20px_-4px_rgba(79,70,229,0.5)] hover:-translate-y-0.5 hover:shadow-[0_8px_24px_-4px_rgba(79,70,229,0.6)] active:translate-y-0 active:scale-[0.98]"
                    : "bg-white/5 text-slate-500 border border-white/5 cursor-not-allowed"
                }`}
              >
                {isAutomationPending ? (
                  <div className="flex items-center gap-2">
                    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}>
                      <Loader2 className="w-4 h-4" />
                    </motion.div>
                    <span>Starting automation...</span>
                  </div>
                ) : (
                  <>
                    <PlaySquare className="w-4 h-4" />
                    <span>Generate &amp; Upload to YouTube</span>
                  </>
                )}
              </button>
            </div>
          )}
        </form>
      </div>
    </motion.div>
  );
}
