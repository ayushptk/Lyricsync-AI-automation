import Link from "next/link";
import { Button } from "@/app/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/Card";
import { Plus, Video, Music, Clock, Play } from "lucide-react";

export default function Dashboard() {
  const mockProjects = [
    { id: 1, title: "Blinding Lights (Cover)", type: "Audio Upload", date: "2 days ago", status: "Completed", duration: "3:22" },
    { id: 2, title: "Lofi Hip Hop Mix", type: "YouTube URL", date: "1 week ago", status: "Completed", duration: "10:00" },
  ];

  return (
    <div className="min-h-screen bg-background p-6 md:p-12 max-w-7xl mx-auto">
      
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-12">
        <div>
          <h1 className="font-heading text-4xl font-bold tracking-tight mb-2">Projects</h1>
          <p className="text-zinc-400">Manage your generated lyric videos and audio stems.</p>
        </div>
        <Link href="/upload">
          <Button className="gap-2">
            <Plus className="w-5 h-5" />
            New Project
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <Card className="glass border-white/5">
          <CardHeader className="pb-2">
            <CardDescription>Available Credits</CardDescription>
            <CardTitle className="text-3xl">28</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-zinc-400">Pro Plan renews in 14 days</div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="font-heading font-semibold text-xl">Recent Activity</h2>
        
        {mockProjects.map(project => (
          <Link key={project.id} href={`/studio/${project.id}`}>
            <Card className="glass border-white/5 hover:border-blue-500/30 transition-colors cursor-pointer group">
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-400 group-hover:text-blue-400 transition-colors">
                    {project.type === "YouTube URL" ? <Video className="w-6 h-6" /> : <Music className="w-6 h-6" />}
                  </div>
                  <div>
                    <h3 className="font-medium text-foreground">{project.title}</h3>
                    <div className="flex items-center gap-2 text-xs text-zinc-500 mt-1">
                      <span>{project.type}</span>
                      <span>•</span>
                      <span>{project.date}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-zinc-400">
                  <div className="hidden sm:flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {project.duration}
                  </div>
                  <div className="px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-xs font-medium border border-green-500/20">
                    {project.status}
                  </div>
                  <Button variant="ghost" size="icon" className="group-hover:bg-blue-500/20 group-hover:text-blue-400">
                    <Play className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

    </div>
  );
}
