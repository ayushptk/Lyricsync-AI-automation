import Link from "next/link";
import { Button } from "./components/ui/Button";
import { Play, Sparkles, AudioLines, Music } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 relative overflow-hidden bg-background">
      
      {/* Abstract Background Effects */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-600/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-600/20 blur-[120px] pointer-events-none" />

      <div className="z-10 max-w-5xl mx-auto text-center flex flex-col items-center gap-8">
        
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm font-medium text-zinc-300 mb-4 animate-in slide-in-from-bottom-4 duration-700">
          <Sparkles className="w-4 h-4 text-accent-500" />
          <span>LyricSync AI v1.0 is here</span>
        </div>

        <h1 className="font-heading text-5xl md:text-7xl font-bold tracking-tight text-balance leading-tight animate-in slide-in-from-bottom-8 duration-700 delay-100">
          Turn any song into a<br />
          <span className="text-gradient">Stunning Lyric Video</span>
        </h1>
        
        <p className="text-lg md:text-xl text-zinc-400 max-w-2xl text-balance animate-in slide-in-from-bottom-8 duration-700 delay-200">
          Instantly isolate vocals, extract melodies, transcribe lyrics, and generate a dynamic, synchronized video ready for YouTube or TikTok.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 mt-4 animate-in slide-in-from-bottom-8 duration-700 delay-300">
          <Link href="/upload">
            <Button size="lg" className="gap-2 group">
              Start Creating Free
              <Play className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button variant="glass" size="lg">
              View Dashboard
            </Button>
          </Link>
        </div>

        {/* Mock Editor Canvas Preview */}
        <div className="mt-16 w-full max-w-4xl aspect-video rounded-2xl glass border border-white/10 p-2 shadow-2xl relative overflow-hidden group animate-in zoom-in-95 duration-1000 delay-500">
          <div className="absolute inset-0 bg-gradient-to-tr from-blue-900/40 to-purple-900/40 opacity-50 transition-opacity group-hover:opacity-70" />
          <div className="w-full h-full rounded-xl bg-zinc-950 flex flex-col items-center justify-center relative overflow-hidden border border-white/5">
             <h2 className="text-4xl md:text-6xl font-bold font-heading uppercase tracking-widest text-white shadow-black drop-shadow-2xl z-20">
               <span className="text-blue-400">FEEL</span> THE BEAT
             </h2>
             
             {/* Fake Audio Waveform Bottom */}
             <div className="absolute bottom-0 left-0 w-full h-32 flex items-end justify-center gap-1 p-4 opacity-50">
                {[...Array(40)].map((_, i) => (
                  <div key={i} className="w-2 bg-blue-500 rounded-t-sm" style={{ height: `${Math.max(10, Math.random() * 100)}%`, transition: 'height 0.2s ease' }} />
                ))}
             </div>
          </div>
        </div>

        {/* Feature Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-20 text-left animate-in fade-in duration-1000 delay-700">
          
          <div className="glass p-6 rounded-2xl">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4 text-blue-400">
              <AudioLines className="w-6 h-6" />
            </div>
            <h3 className="font-heading font-semibold text-xl mb-2 text-foreground">Pro Stem Separation</h3>
            <p className="text-zinc-400 text-sm">Powered by advanced AI to isolate crisp vocals and instrumentals without the muddy artifacts.</p>
          </div>

          <div className="glass p-6 rounded-2xl">
            <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-4 text-purple-400">
              <Music className="w-6 h-6" />
            </div>
            <h3 className="font-heading font-semibold text-xl mb-2 text-foreground">Millisecond Sync</h3>
            <p className="text-zinc-400 text-sm">Whisper-powered word-level timestamping ensures your lyrics match the vocals perfectly.</p>
          </div>

          <div className="glass p-6 rounded-2xl">
            <div className="w-12 h-12 rounded-xl bg-pink-500/20 flex items-center justify-center mb-4 text-pink-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="font-heading font-semibold text-xl mb-2 text-foreground">Motion Canvas</h3>
            <p className="text-zinc-400 text-sm">Customize fonts, colors, aspect ratios, and animations. Export directly to 4K MP4.</p>
          </div>

        </div>

      </div>
    </main>
  );
}
