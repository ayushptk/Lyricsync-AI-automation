"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Download, Music, Video, FileText } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useEffect } from "react";

export default function JobDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuthStore();
  const jobId = params.id as string;

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => {
      // Mocking the job fetch since backend GET /api/jobs/{id} isn't strictly defined yet.
      // In a real app, this would hit the API.
      return {
        id: jobId,
        status: "completed", // Mock completed state for UI testing
        video_url: `http://localhost:8000/api/v1/video/${jobId}/download`,
        audio_url: `http://localhost:8000/api/v1/melody/${jobId}/download`,
        srt_url: `http://localhost:8000/api/v1/transcription/${jobId}/subtitles?format=srt`,
      };
    },
    refetchInterval: (data: any) => (data?.status === "completed" || data?.status === "failed" ? false : 5000),
    enabled: isAuthenticated && !!jobId,
  });

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
            Status: <span className="text-blue-400 capitalize">{job?.status}</span>
          </div>
        </div>

        {job?.status !== "completed" ? (
          <Card className="max-w-xl mx-auto mt-24 border-blue-900/30 shadow-[0_0_50px_rgba(37,99,235,0.1)]">
            <CardHeader className="text-center pb-2">
              <Video className="w-12 h-12 text-blue-500 mx-auto mb-4 animate-pulse" />
              <CardTitle>Processing Video...</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ProgressBar progress={65} label="Running AI Pipeline" />
              <p className="text-center text-sm text-slate-500 mt-6">
                Separating vocals, extracting MIDI, rendering piano, generating subtitles...
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <Card className="overflow-hidden border-slate-800">
                <div className="aspect-video bg-black flex items-center justify-center relative">
                  {/* Real implementation would use the video tag */}
                  <video 
                    controls 
                    className="w-full h-full object-contain"
                    poster="/grid.svg"
                  >
                    <source src={job.video_url} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                </div>
                <CardContent className="p-4 bg-slate-900/50 flex justify-between items-center">
                  <span className="font-medium">Final Karaoke Render</span>
                  <Button variant="outline" size="sm" onClick={() => window.open(job.video_url)}>
                    <Download className="w-4 h-4 mr-2" /> Download MP4
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Export Assets</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex justify-between items-center">
                    <div className="flex items-center">
                      <Music className="w-5 h-5 text-indigo-400 mr-3" />
                      <div>
                        <p className="font-medium text-sm text-slate-200">Piano Audio</p>
                        <p className="text-xs text-slate-500">Rendered via FluidSynth</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => window.open(job.audio_url)}>
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>

                  <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex justify-between items-center">
                    <div className="flex items-center">
                      <FileText className="w-5 h-5 text-green-400 mr-3" />
                      <div>
                        <p className="font-medium text-sm text-slate-200">Subtitles (SRT)</p>
                        <p className="text-xs text-slate-500">Word-level aligned</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => window.open(job.srt_url)}>
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
