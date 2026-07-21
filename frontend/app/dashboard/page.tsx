"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Link2, Plus, LogOut, Video } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";

interface Job {
  id: string;
  status: string;
  created_at: string;
  result_data?: any;
}

export default function DashboardPage() {
  const [url, setUrl] = useState("");
  const router = useRouter();
  const { user, setUser, isAuthenticated, isLoading } = useAuthStore();

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  // Fetch user's jobs (polling every 5 seconds)
  const { data: jobs, refetch } = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => {
      // Assuming a GET /api/jobs endpoint exists. If not, this is a placeholder.
      // Since we don't have a GET /api/jobs endpoint in the backend currently, 
      // we'll mock an empty array to prevent 404s until we implement it on the backend.
      try {
        const res = await api.get("/api/ingest/jobs");
        return res.data as Job[];
      } catch (err) {
        return [];
      }
    },
    refetchInterval: 5000, // Poll every 5s
    enabled: isAuthenticated,
  });

  const ingestMutation = useMutation({
    mutationFn: async (youtubeUrl: string) => {
      // Using project_id=1 for MVP as per backend default route
      const response = await api.post("/api/ingest/youtube?project_id=1", { url: youtubeUrl });
      return response.data;
    },
    onSuccess: () => {
      setUrl("");
      refetch();
    }
  });

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
    <div className="min-h-screen p-8 bg-slate-950 text-slate-100">
      <header className="flex justify-between items-center mb-12 max-w-6xl mx-auto">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
            LyricSync AI
          </h1>
          <p className="text-slate-400">Welcome, {user?.email}</p>
        </div>
        <Button variant="ghost" onClick={handleLogout}>
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </Button>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1">
          <Card className="sticky top-8">
            <CardHeader>
              <CardTitle>New Project</CardTitle>
              <CardDescription>Paste a YouTube URL to begin extraction</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Link2 className="h-5 w-5 text-slate-500" />
                  </div>
                  <Input
                    className="pl-10"
                    placeholder="https://youtube.com/watch?v=..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                </div>
                <Button type="submit" className="w-full" isLoading={ingestMutation.isPending}>
                  <Plus className="w-4 h-4 mr-2" />
                  Start Processing
                </Button>
                {ingestMutation.isError && (
                  <p className="text-sm text-red-500">Failed to submit job.</p>
                )}
              </form>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold mb-4">Recent Jobs</h2>
          {jobs?.length === 0 ? (
            <div className="p-12 border border-slate-800 border-dashed rounded-xl flex flex-col items-center justify-center text-slate-500">
              <Video className="w-12 h-12 mb-4 opacity-50" />
              <p>No jobs found. Paste a URL to get started.</p>
            </div>
          ) : (
            jobs?.map((job) => (
              <Card key={job.id} className="cursor-pointer hover:border-blue-500/50 transition-colors" onClick={() => router.push(`/dashboard/${job.id}`)}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-slate-200">Job {job.id.split("-")[0]}</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Status: <span className="text-blue-400 capitalize">{job.status}</span>
                    </p>
                  </div>
                  <div className="w-1/3">
                    <ProgressBar 
                      progress={job.status === "completed" ? 100 : job.status === "failed" ? 0 : 45} 
                      className={job.status === "failed" ? "opacity-50 grayscale" : ""} 
                    />
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
