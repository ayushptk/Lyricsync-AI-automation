"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";

// UI Components
import { DashboardBackground } from "@/components/dashboard/DashboardBackground";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { CreateProjectCard } from "@/components/dashboard/CreateProjectCard";
import { ProjectList } from "@/components/dashboard/ProjectList";
import { EmptyProjects } from "@/components/dashboard/EmptyProjects";
import { Clock } from "lucide-react";
import { motion } from "framer-motion";

export interface Job {
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

export default function DashboardPage() {
  const [url, setUrl] = useState("");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [trackedJobId, setTrackedJobId] = useState<string | null>(null);
  const [isWaitingForAutoJob, setIsWaitingForAutoJob] = useState(false);
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuthStore();

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  // Fetch user's jobs (polling every 3 seconds for smoother updates)
  const { data: jobsResponse, refetch } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      const res = await api.get("/api/v1/jobs");
      return res.data;
    },
    refetchInterval: 3000, 
    enabled: isAuthenticated,
  });

  const jobs: Job[] = jobsResponse?.items || [];
  const totalJobs = jobsResponse?.total || 0;
  
  // Calculate stats
  const processingJobs = jobs.filter(j => j.status === "processing" || j.status === "queued");

  // Track the job that was just started for detailed UI feedback
  useEffect(() => {
    if (isWaitingForAutoJob && jobs.length > 0) {
      // Find the most recently created job
      const newestJob = jobs[0];
      const createdAtStr = newestJob.created_at.endsWith("Z") ? newestJob.created_at : `${newestJob.created_at}Z`;
      const isRecent = new Date().getTime() - new Date(createdAtStr).getTime() < 30000; // created within 30s
      if (isRecent && (newestJob.status === "queued" || newestJob.status === "processing")) {
         setTrackedJobId(newestJob.id);
         setIsWaitingForAutoJob(false);
      }
    }
  }, [jobs, isWaitingForAutoJob]);

  // The active job is either the one we explicitly started tracking, or just the latest processing job if we lost track
  const activeJob = trackedJobId 
    ? jobs.find(j => j.id === trackedJobId) 
    : (processingJobs.length > 0 ? processingJobs[0] : null);

  const ingestMutation = useMutation({
    mutationFn: async ({ youtubeUrl, ratio }: { youtubeUrl: string, ratio: string }) => {
      const response = await api.post("/api/v1/ingest/youtube", { 
        url: youtubeUrl,
        project_title: "New Lyric Video",
        aspect_ratio: ratio
      });
      return response.data;
    },
    onSuccess: (data) => {
      setUrl("");
      if (data.job_id) {
        setTrackedJobId(data.job_id);
      }
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

  const automationMutation = useMutation({
    mutationFn: async ({ youtubeUrl }: { youtubeUrl: string }) => {
      const response = await api.post("/api/automation/youtube", { 
        youtube_url: youtubeUrl
      });
      return response.data;
    },
    onSuccess: (data) => {
      setUrl("");
      if (data.success && data.job_id) {
        setTrackedJobId(data.job_id);
        refetch();
        toast.success(data.message || "Automation started!");
      } else if (data.success) {
        setIsWaitingForAutoJob(true);
        toast.success(data.message || "Automation started!");
      } else {
        toast.error(data.message || "Automation failed");
      }
    },
    onError: (error: any) => {
      const errorMsg = typeof error?.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : error?.response?.data?.detail?.[0]?.msg
        || error?.response?.data?.message
        || error.message 
        || "An unexpected error occurred.";
      toast.error(`Automation failed: ${errorMsg}`);
    }
  });

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.includes("youtube.com") || url.includes("youtu.be")) {
      setTrackedJobId(null); // reset tracking
      ingestMutation.mutate({ youtubeUrl: url, ratio: aspectRatio });
    }
  };

  const handleAutomationSubmit = (e: React.MouseEvent) => {
    e.preventDefault();
    if (url.includes("youtube.com") || url.includes("youtu.be")) {
      setTrackedJobId(null); // reset tracking
      automationMutation.mutate({ youtubeUrl: url });
    }
  };

  // Allow user to dismiss the tracked job when it finishes or fails
  const handleClearTrackedJob = () => {
    setTrackedJobId(null);
  };

  if (isLoading || !isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-background text-text-primary relative overflow-y-auto overflow-x-hidden selection:bg-indigo-500/30 selection:text-indigo-200">
      <DashboardBackground />

      <div className="relative z-10 p-6 md:p-8 lg:p-12 w-full max-w-[1500px] mx-auto min-h-screen flex flex-col">
        <DashboardHeader user={user} />

        <main className="flex-1 w-full max-w-[1400px] mx-auto pb-24">
          <StatsGrid totalJobs={totalJobs} processingJobs={processingJobs.length} />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
            
            {/* LEFT COLUMN: 38% equivalent in grid (e.g. col-span-5) */}
            <div className="lg:col-span-5 flex flex-col gap-8">
              <CreateProjectCard 
                url={url}
                setUrl={setUrl}
                aspectRatio={aspectRatio}
                setAspectRatio={setAspectRatio}
                onSubmit={handleSubmit}
                onAutomationSubmit={handleAutomationSubmit}
                isPending={ingestMutation.isPending || isWaitingForAutoJob}
                isAutomationPending={automationMutation.isPending || isWaitingForAutoJob}
                activeJob={activeJob}
                onClearActiveJob={handleClearTrackedJob}
              />
            </div>

            {/* RIGHT COLUMN: 62% equivalent (col-span-7) */}
            <div className="lg:col-span-7 flex flex-col">
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.35, ease: "easeOut" }}
                className="flex items-center justify-between mb-6"
              >
                <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-indigo-400" />
                  Recent Projects
                </h2>
                {jobs.length > 0 && (
                  <button className="text-sm font-medium text-slate-400 hover:text-indigo-400 transition-colors group">
                    View all <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
                  </button>
                )}
              </motion.div>

              {jobs.length === 0 ? (
                <EmptyProjects />
              ) : (
                <ProjectList 
                  jobs={jobs}
                  onDelete={handleDelete}
                  deletingProjectId={deleteMutation.isPending ? deleteMutation.variables as string : null}
                />
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
