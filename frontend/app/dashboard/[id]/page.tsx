"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Download, Music, Video, FileText, AlertTriangle, Copy, Check, Terminal, RotateCcw } from "lucide-react";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";

export default function JobDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();
  const jobId = params.id as string;
  const [copied, setCopied] = useState(false);

  // Map progress percentage to current pipeline step
  const getStepLabel = (progress: number): string => {
    if (progress < 15) return "Step 1/8 — Downloading Audio";
    if (progress < 25) return "Step 2/8 — Preprocessing Audio";
    if (progress < 50) return "Step 3/8 — Separating Vocals (Demucs)";
    if (progress < 60) return "Step 4/8 — Extracting Melody";
    if (progress < 70) return "Step 5/8 — Rendering Piano Audio";
    if (progress < 80) return "Step 6/8 — Transcribing with Faster-Whisper";
    if (progress < 85) return "Step 7/8 — Generating Subtitles";
    if (progress < 100) return "Step 8/8 — Rendering Final Video";
    return "Complete";
  };

  const getStepDescription = (progress: number): string => {
    if (progress < 15) return "Fetching audio stream from YouTube...";
    if (progress < 25) return "Normalizing volume, converting to 16kHz WAV, trimming silence...";
    if (progress < 50) return "Running Demucs AI model to isolate vocals. This step is CPU-intensive and may take several minutes...";
    if (progress < 60) return "Using Basic Pitch to convert vocals to MIDI notes...";
    if (progress < 70) return "Rendering MIDI to piano audio with FluidSynth...";
    if (progress < 80) return "Running Faster-Whisper for word-level transcription...";
    if (progress < 85) return "Creating SRT, LRC, and ASS subtitle files...";
    if (progress < 100) return "Compositing final karaoke video with FFmpeg...";
    return "Processing complete!";
  };

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => {
      const res = await api.get(`/api/v1/jobs/${jobId}`);
      const jobData = res.data;
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      return {
        ...jobData,
        video_url: `${apiBase}/api/v1/video/${jobId}/download`,
        audio_url: `/api/v1/melody/${jobId}/audio`,
        srt_url: `/api/v1/transcription/${jobId}/subtitles?format=srt`,
      };
    },
    refetchInterval: (query: any) => {
      const data = query?.state?.data;
      return (data?.status === "completed" || data?.status === "failed") ? false : 3000;
    },
    enabled: isAuthenticated && !!jobId,
  });

  const handleCopyLog = () => {
    if (job?.error_log) {
      navigator.clipboard.writeText(job.error_log);
      setCopied(true);
      toast.success("Full error log copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleAuthDownload = async (url: string, defaultFilename: string) => {
    try {
      const response = await api.get(url, { responseType: 'blob' });
      
      // Try to get filename from Content-Disposition header
      let filename = defaultFilename;
      const disposition = response.headers['content-disposition'];
      if (disposition && disposition.indexOf('filename=') !== -1) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches != null && matches[1]) { 
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      
      const blob = new Blob([response.data]);
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      try {
        // When responseType='blob', error bodies are also blobs — parse them
        const errData = err?.response?.data;
        if (errData instanceof Blob) {
          const text = await errData.text();
          const json = JSON.parse(text);
          toast.error(json.detail || 'Download failed.');
        } else {
          toast.error(err?.response?.data?.detail || 'Download failed. File may not be available yet.');
        }
      } catch {
        toast.error('Download failed. File may not be available yet.');
      }
    }
  };

  if (isLoading || !isAuthenticated || jobLoading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">Loading...</div>;
  }

  return (
    <div className="min-h-screen p-8 bg-slate-950 text-slate-100">
      <div className="max-w-6xl mx-auto">
        <Button variant="ghost" onClick={() => router.push("/dashboard")} className="mb-8">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>

        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
              Project Details
            </h1>
            <p className="text-slate-400 mt-2">ID: {jobId}</p>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 px-4 py-2 rounded-full text-sm font-medium">
            Status: <span className={job?.status === "failed" ? "text-red-400 capitalize" : "text-blue-400 capitalize"}>{job?.status}</span>
          </div>
        </div>

        {job?.status === "failed" ? (
          <div className="space-y-6">
            {/* Failure Overview Banner */}
            <Card className="border-red-900/50 bg-red-950/20 shadow-[0_0_50px_rgba(225,29,72,0.15)]">
              <CardHeader className="flex flex-row items-center gap-4 pb-2">
                <div className="p-3 rounded-full bg-red-500/10 border border-red-500/20 text-red-400">
                  <AlertTriangle className="w-8 h-8" />
                </div>
                <div>
                  <CardTitle className="text-xl text-red-300">Processing Failed at {Math.round(job?.progress ?? 0)}% Progress</CardTitle>
                  <p className="text-sm text-red-400/80 mt-1">
                    The pipeline encountered an unrecoverable error during step execution. Review full depth log details below.
                  </p>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <ProgressBar progress={job?.progress ?? 0} className="bg-red-950/40 [&>div]:bg-red-500" />
              </CardContent>
            </Card>

            {/* Diagnostic Terminal View */}
            <Card className="border-slate-800 bg-slate-900/80 backdrop-blur-md">
              <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800/80 pb-4">
                <div className="flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-indigo-400" />
                  <CardTitle className="text-lg text-slate-200">Full Execution & Diagnostic Traceback</CardTitle>
                </div>
                {job?.error_log && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleCopyLog}
                    className="border-slate-700 hover:bg-slate-800 text-slate-300"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4 mr-2 text-emerald-400" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4 mr-2" />
                        Copy Error Log
                      </>
                    )}
                  </Button>
                )}
              </CardHeader>
              <CardContent className="pt-6">
                {job?.error_log ? (
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 font-mono text-xs text-slate-300 max-h-[500px] overflow-y-auto leading-relaxed scrollbar-thin scrollbar-thumb-slate-800">
                    {job.error_log.split("\n").map((line: string, idx: number) => {
                      const isErrorLine = line.includes("ERROR:") || line.includes("Download failed") || line.includes("Exception") || line.includes("Error:") || line.includes("Failed");
                      const isTraceback = line.includes("Traceback") || line.startsWith("  File ");
                      const isStep = line.includes("Step ") || line.includes("Starting ");

                      return (
                        <div 
                          key={idx} 
                          className={`py-0.5 whitespace-pre-wrap break-words ${
                            isErrorLine 
                              ? "text-rose-400 font-semibold bg-rose-950/30 px-1 rounded" 
                              : isTraceback 
                              ? "text-slate-400 pl-2" 
                              : isStep 
                              ? "text-indigo-300 font-medium" 
                              : "text-slate-300"
                          }`}
                        >
                          {line || "\u00A0"}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm italic">No error details available.</p>
                )}
              </CardContent>
            </Card>

            {/* Action Toolbar */}
            <div className="flex gap-4 justify-end pt-2">
              <Button variant="outline" onClick={() => router.push("/dashboard")}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
              </Button>
              <Button className="bg-indigo-600 hover:bg-indigo-500" onClick={() => router.push("/dashboard")}>
                <RotateCcw className="w-4 h-4 mr-2" /> Try Another Video
              </Button>
            </div>
          </div>
        ) : job?.status !== "completed" ? (
          <Card className="max-w-xl mx-auto mt-24 border-blue-900/30 shadow-[0_0_50px_rgba(37,99,235,0.1)]">
            <CardHeader className="text-center pb-2">
              <Video className="w-12 h-12 mx-auto mb-4 text-blue-500 animate-pulse" />
              <CardTitle>Processing Video...</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ProgressBar progress={job?.progress ?? 0} label={getStepLabel(job?.progress ?? 0)} />
              <p className="text-center text-sm text-slate-500 mt-6">
                {getStepDescription(job?.progress ?? 0)}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <Card className="overflow-hidden border-slate-800">
                <div className="aspect-video bg-black flex items-center justify-center relative">
                  {job.has_video ? (
                    <video 
                      controls 
                      className="w-full h-full object-contain"
                      poster="/grid.svg"
                    >
                      <source src={job.video_url} type="video/mp4" />
                      Your browser does not support the video tag.
                    </video>
                  ) : (
                    <div className="text-center text-slate-500 p-8">
                      <Video className="w-12 h-12 mx-auto mb-3 opacity-40" />
                      <p className="text-sm">Video rendering was skipped or unavailable.</p>
                      <p className="text-xs mt-1 text-slate-600">The audio track is still available for download.</p>
                    </div>
                  )}
                </div>
                <CardContent className="p-4 bg-slate-900/50 flex justify-between items-center">
                  <span className="font-medium">Final Karaoke Render</span>
                  {job.has_video && (
                    <Button variant="outline" size="sm" onClick={() => window.open(job.video_url)}>
                      <Download className="w-4 h-4 mr-2" /> Download MP4
                    </Button>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Export Assets</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {job.has_audio ? (
                    <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex justify-between items-center">
                      <div className="flex items-center">
                        <Music className="w-5 h-5 text-indigo-400 mr-3" />
                        <div>
                          <p className="font-medium text-sm text-slate-200">Instrumental Audio</p>
                          <p className="text-xs text-slate-500">Backing track / Piano</p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => handleAuthDownload(job.audio_url, 'instrumental.wav')}>
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800/50 flex items-center gap-3 text-slate-600">
                      <Music className="w-5 h-5 opacity-40" />
                      <p className="text-xs">Audio not available</p>
                    </div>
                  )}

                  {job.has_subtitles ? (
                    <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex justify-between items-center">
                      <div className="flex items-center">
                        <FileText className="w-5 h-5 text-green-400 mr-3" />
                        <div>
                          <p className="font-medium text-sm text-slate-200">Subtitles (SRT)</p>
                          <p className="text-xs text-slate-500">Word-level aligned</p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => handleAuthDownload(job.srt_url, 'vocals_subtitles.srt')}>
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800/50 flex items-center gap-3 text-slate-600">
                      <FileText className="w-5 h-5 opacity-40" />
                      <p className="text-xs">Subtitles not available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
