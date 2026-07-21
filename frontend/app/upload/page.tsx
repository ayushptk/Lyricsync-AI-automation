"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/app/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/Card";
import { Link as LinkIcon, UploadCloud, Loader2 } from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    setIsProcessing(true);
    // Simulate API call to /api/ingest
    setTimeout(() => {
      // Redirect to a mock studio session
      router.push("/studio/mock-123");
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 relative overflow-hidden">
      
      {/* Background blur */}
      <div className="absolute top-1/4 left-1/4 w-[50%] h-[50%] rounded-full bg-blue-600/10 blur-[120px] pointer-events-none" />

      <div className="z-10 w-full max-w-2xl">
        <div className="text-center mb-10">
          <h1 className="font-heading text-4xl font-bold tracking-tight mb-4">Start a New Project</h1>
          <p className="text-zinc-400 text-lg">Paste a YouTube URL or drop an audio file to extract stems and lyrics.</p>
        </div>

        <div className="grid gap-6">
          <Card className="glass border-white/10 shadow-xl shadow-black/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LinkIcon className="w-6 h-6 text-red-500" />
                Import from YouTube
              </CardTitle>
              <CardDescription>We will download the highest quality audio automatically.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUrlSubmit} className="flex gap-2">
                <input 
                  type="url" 
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="flex-1 h-12 rounded-xl bg-black/40 border border-white/10 px-4 text-foreground placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  value={url}
                  onChange={e => setUrl(e.target.value)}
                  required
                />
                <Button type="submit" size="lg" disabled={isProcessing} className="w-32">
                  {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Import"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="relative flex items-center py-4">
            <div className="flex-grow border-t border-white/10"></div>
            <span className="flex-shrink-0 mx-4 text-zinc-500 text-sm font-medium">OR</span>
            <div className="flex-grow border-t border-white/10"></div>
          </div>

          <Card className="bg-zinc-900/50 border-white/5 border-dashed border-2 hover:bg-zinc-900/80 transition-colors cursor-pointer group">
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <UploadCloud className="w-8 h-8 text-blue-400" />
              </div>
              <h3 className="font-medium text-lg text-foreground mb-1">Click or drag audio file to upload</h3>
              <p className="text-zinc-500 text-sm">Supports .mp3, .wav, .m4a up to 100MB</p>
            </CardContent>
          </Card>
        </div>
      </div>

    </div>
  );
}
