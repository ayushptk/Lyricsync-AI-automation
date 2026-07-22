"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Link2, Plus, LogOut, Video, Activity, Clock, Zap, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { StatCard } from "@/components/ui/StatCard";

interface Job {
  id: string;
  project_id: string;
  job_type: string;
  status: string;
  progress: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  error_log?: string;
}

const getETA = (progress: number) => {
  if (progress === 0 || progress === 100) return null;
  const totalEstimatedTimeSeconds = 300;
  const remainingPercent = (100 - progress) / 100;
  const secondsLeft = Math.round(totalEstimatedTimeSeconds * remainingPercent);
  
  if (secondsLeft > 60) {
    return `~${Math.ceil(secondsLeft / 60)} mins left`;
  }
  return `~${secondsLeft} secs left`;
}

export default function DashboardPage() {
  const [url, setUrl] = useState("");
  const [fakeProgress, setFakeProgress] = useState(0);
  const router = useRouter();
  const { user, setUser, isAuthenticated, isLoading } = useAuthStore();

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  // Fetch user's jobs (polling every 5 seconds)
  const { data: jobsResponse, refetch } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      const res = await api.get("/api/v1/jobs");
      return res.data;
    },
    refetchInterval: 5000, // Poll every 5s for now (future SSE)
    enabled: isAuthenticated,
  });

  const jobs: Job[] = jobsResponse?.items || [];
  const totalJobs = jobsResponse?.total || 0;
  
  // Calculate stats
  const completedJobs = jobs.filter(j => j.status === "completed").length;
  const processingJobs = jobs.filter(j => j.status === "processing").length;

  const ingestMutation = useMutation({
    mutationFn: async (youtubeUrl: string) => {
      // Dynamic project creation via the backend by omitting project_id
      const response = await api.post("/api/v1/ingest/youtube", { 
        url: youtubeUrl,
        project_title: "New Lyric Video" 
      });
      return response.data;
    },
    onSuccess: (data) => {
      setUrl("");
      refetch();
      toast.success("Project started successfully!");
    },
    onError: (error: any) => {
      const errorMsg = typeof error?.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : error?.response?.data?.detail?.[0]?.msg
        || error.message 
        || "An unexpected error occurred.";
      toast.error(`Failed: ${errorMsg}`);
    }
  });

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (ingestMutation.isPending) {
      setFakeProgress(0);
      interval = setInterval(() => {
        setFakeProgress((prev) => {
          if (prev >= 95) return prev;
          return prev + Math.floor(Math.random() * 10) + 1;
        });
      }, 500);
    } else if (ingestMutation.isSuccess) {
      setFakeProgress(100);
    } else if (ingestMutation.isError) {
      setFakeProgress(0);
    }
    return () => clearInterval(interval);
  }, [ingestMutation.isPending, ingestMutation.isSuccess, ingestMutation.isError]);

  const deleteMutation = useMutation({
    mutationFn: async (projectId: string) => {
      await api.delete(`/api/v1/projects/${projectId}`);
    },
    onSuccess: () => {
      refetch();
    }
  });

  const handleDelete = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this project and all its data? This cannot be undone.")) {
      deleteMutation.mutate(projectId);
    }
  };

  const handleLogout = () => {
    setUser(null);
    router.push("/login");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.includes("youtube.com") || url.includes("youtu.be")) {
      ingestMutation.mutate(url);
    }
  };

  if (isLoading || !isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 relative overflow-hidden">
      {/* Background Glow Effects */}
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-indigo-500/20 to-transparent pointer-events-none" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[30rem] h-[30rem] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="relative z-10 p-8">
        <header className="flex justify-between items-center mb-12 max-w-6xl mx-auto">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
              LyricSync AI
            </h1>
            <p className="text-slate-400 mt-1">Welcome back, <span className="text-slate-300 font-medium">{user?.email}</span></p>
          </div>
          <Button variant="ghost" onClick={handleLogout} className="hover:bg-white/5 transition-colors">
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </header>

        <main className="max-w-6xl mx-auto space-y-8">
          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard 
              title="Total Videos" 
              value={totalJobs} 
              icon={<Video className="w-5 h-5" />} 
            />
            <StatCard 
              title="Processing" 
              value={processingJobs} 
              icon={<Activity className="w-5 h-5" />} 
            />
            <StatCard 
              title="Credits Remaining" 
              value="Unlimited" 
              icon={<Zap className="w-5 h-5" />} 
              description="Pro Plan Active"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <Card className="sticky top-8 bg-white/[0.02] border-white/10 backdrop-blur-md shadow-2xl">
                <CardHeader>
                  <CardTitle className="text-xl">New Project</CardTitle>
                  <CardDescription>Paste a YouTube URL to extract vocals and generate lyrics</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="relative group">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Link2 className="h-5 w-5 text-slate-400 group-focus-within:text-indigo-400 transition-colors" />
                      </div>
                      <Input
                        className="pl-10 bg-black/20 border-white/10 focus:border-indigo-500/50 transition-colors placeholder:text-slate-600"
                        placeholder="https://youtube.com/watch?v=..."
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        required
                      />
                    </div>
                    <Button 
                      type="submit" 
                      className="w-full bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_20px_-5px_rgba(99,102,241,0.5)] transition-all" 
                      isLoading={ingestMutation.isPending}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Start Processing
                    </Button>
                    {ingestMutation.isPending && (
                      <div className="pt-2">
                        <ProgressBar progress={fakeProgress} label="Initializing Project..." />
                      </div>
                    )}
                  </form>
                </CardContent>
              </Card>
            </div>

            <div className="lg:col-span-2 space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-200 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-indigo-400" />
                  Recent Activity
                </h2>
              </div>
              
              {jobs.length === 0 ? (
                <div className="p-16 border border-white/5 bg-white/[0.02] backdrop-blur-sm rounded-2xl flex flex-col items-center justify-center text-slate-500 shadow-inner">
                  <Video className="w-16 h-16 mb-6 opacity-20" />
                  <p className="text-lg">No processing jobs found</p>
                  <p className="text-sm mt-2 opacity-60">Paste a YouTube URL to create your first LyricSync video.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {jobs.map((job) => (
                    <Card 
                      key={job.id} 
                      className="cursor-pointer bg-white/[0.02] border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.04] backdrop-blur-sm transition-all duration-300 group" 
                      onClick={() => router.push(`/dashboard/${job.id}`)}
                    >
                      <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-slate-200 truncate group-hover:text-indigo-300 transition-colors">
                            Project {job.project_id.split("-")[0]}
                          </h3>
                          <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                            <span className="flex items-center gap-1">
                              <span className={`w-2 h-2 rounded-full ${job.status === 'completed' ? 'bg-emerald-500' : job.status === 'failed' ? 'bg-rose-500' : 'bg-amber-500 animate-pulse'}`}></span>
                              <span className="capitalize">{job.status}</span>
                            </span>
                            <span>&bull;</span>
                            <span className="capitalize">{job.job_type.replace('_', ' ')}</span>
                          </div>
                        </div>
                        <div className="w-full sm:w-1/3 flex items-center gap-4">
                          <div className="flex-1">
                            <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                              <span>Progress</span>
                              <span className="flex gap-2">
                                {job.status === "processing" && job.progress > 0 && job.progress < 100 && (
                                  <span className="text-indigo-400">{getETA(job.progress)}</span>
                                )}
                                <span>{Math.round(job.progress)}%</span>
                              </span>
                            </div>
                            <ProgressBar 
                              progress={job.progress} 
                              className={job.status === "failed" ? "opacity-50 grayscale" : "bg-white/5 [&>div]:bg-gradient-to-r [&>div]:from-indigo-500 [&>div]:to-purple-500"} 
                            />
                            {job.error_log && (
                              <div className="mt-2 text-[10px] text-slate-400 font-mono leading-tight max-h-16 overflow-y-auto bg-black/20 p-2 rounded border border-white/5 scrollbar-thin scrollbar-thumb-white/10">
                                {job.error_log.split('\n').map((line, i) => (
                                  <div key={i}>{line}</div>
                                ))}
                              </div>
                            )}
                          </div>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-slate-500 hover:text-red-400 hover:bg-red-500/10 z-10 shrink-0"
                            onClick={(e) => handleDelete(e, job.project_id)}
                            disabled={deleteMutation.isPending}
                          >
                            {deleteMutation.isPending && deleteMutation.variables === job.project_id ? (
                               <div className="w-4 h-4 rounded-full border-2 border-red-500 border-t-transparent animate-spin" />
                            ) : (
                               <Trash2 className="w-4 h-4" />
                            )}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
