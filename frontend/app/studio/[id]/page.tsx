"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/app/components/ui/Button";
import { Play, Pause, SkipBack, Monitor, Smartphone, Download, Settings, ChevronLeft, Type } from "lucide-react";
import { Permanent_Marker } from "next/font/google";

const permanentMarker = Permanent_Marker({
  weight: "400",
  subsets: ["latin"],
});

export default function StudioEditor() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [aspectRatio, setAspectRatio] = useState<"16:9" | "9:16">("16:9");

  // Mock lyric data
  const lyrics = [
    { text: "I said, ooh, I'm blinded by the lights", start: 2.1, end: 4.5 },
    { text: "No, I can't sleep until I feel your touch", start: 4.8, end: 8.2 },
    { text: "I said, ooh, I'm drowning in the night", start: 8.5, end: 11.0 },
  ];

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden text-foreground">
      
      {/* Left / Center Area: Canvas & Timeline */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-white/10 relative">
        
        {/* Top Header */}
        <header className="h-14 border-b border-white/10 flex items-center justify-between px-4 bg-zinc-900/50">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full">
                <ChevronLeft className="w-5 h-5" />
              </Button>
            </Link>
            <span className="font-heading font-semibold text-sm">Blinding Lights - Project Editor</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="bg-zinc-800 rounded-lg p-1 flex">
              <button 
                onClick={() => setAspectRatio("16:9")}
                className={`p-1.5 rounded-md transition-colors ${aspectRatio === "16:9" ? "bg-zinc-700 text-white" : "text-zinc-400 hover:text-white"}`}
              >
                <Monitor className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setAspectRatio("9:16")}
                className={`p-1.5 rounded-md transition-colors ${aspectRatio === "9:16" ? "bg-zinc-700 text-white" : "text-zinc-400 hover:text-white"}`}
              >
                <Smartphone className="w-4 h-4" />
              </button>
            </div>
            <Button size="sm" className="gap-2 ml-4">
              <Download className="w-4 h-4" /> Export
            </Button>
          </div>
        </header>

        {/* Canvas Area */}
        <div className="flex-1 bg-zinc-950 p-4 md:p-8 flex items-center justify-center relative overflow-hidden bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:24px_24px]">
          
          <div 
            className={`relative bg-black rounded-lg shadow-2xl overflow-hidden transition-all duration-500 flex items-center justify-center ring-1 ring-white/10 ${aspectRatio === "16:9" ? "w-full max-w-4xl aspect-video" : "h-full aspect-[9/16]"}`}
          >
            {/* Mock Video Background */}
            <div className="absolute inset-0 bg-[url('/karaoke_bg.png')] bg-cover bg-center"></div>
            
            {/* Mock Visualizer Waveform Background */}
            <div className="absolute bottom-0 left-0 w-full h-1/2 flex items-end justify-center gap-1 p-8 opacity-20">
               {[...Array(30)].map((_, i) => (
                  <div key={i} className="flex-1 bg-blue-500 rounded-t-sm" style={{ height: `${isPlaying ? Math.max(10, Math.random() * 100) : 10}%`, transition: 'height 0.1s ease' }} />
               ))}
            </div>

            {/* Rendered Text */}
            <div className="z-10 text-center px-8">
              <h1 
                className={`text-4xl md:text-6xl uppercase text-white tracking-wider ${permanentMarker.className}`}
                style={{
                  textShadow: "2px 2px 4px rgba(0, 0, 0, 0.8), 0px 0px 10px rgba(0, 0, 0, 0.5)"
                }}
              >
                {lyrics[0].text}
              </h1>
            </div>
          </div>
        </div>

        {/* Timeline Editor */}
        <div className="h-64 border-t border-white/10 bg-zinc-900 flex flex-col">
          {/* Transport Controls */}
          <div className="h-12 border-b border-white/5 flex items-center px-4 gap-4 bg-zinc-900">
             <Button variant="ghost" size="icon" onClick={() => setCurrentTime(0)}>
               <SkipBack className="w-4 h-4" />
             </Button>
             <Button variant="ghost" size="icon" onClick={() => setIsPlaying(!isPlaying)}>
               {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
             </Button>
             <div className="text-sm font-mono text-zinc-400">
               00:02:14 / 00:03:22
             </div>
          </div>
          
          {/* Tracks Area */}
          <div className="flex-1 relative overflow-x-auto p-4 space-y-4">
             {/* Playhead Mock */}
             <div className="absolute top-0 bottom-0 left-32 w-[2px] bg-red-500 z-10">
               <div className="w-3 h-3 rounded-full bg-red-500 -ml-[5px] -mt-1 shadow-md shadow-red-500/50"></div>
             </div>

             {/* Vocal Track */}
             <div className="flex h-16 bg-zinc-950 rounded-md border border-white/5 overflow-hidden group hover:border-white/20 transition-colors">
               <div className="w-24 bg-zinc-800/50 border-r border-white/5 flex items-center justify-center text-xs text-zinc-400 font-medium p-2 shrink-0">Vocals</div>
               <div className="flex-1 relative bg-gradient-to-r from-blue-900/10 to-transparent">
                  {/* Mock Waveform */}
                  <div className="absolute inset-y-2 left-4 right-4 bg-[url('https://www.transparenttextures.com/patterns/black-scales.png')] opacity-20"></div>
               </div>
             </div>

             {/* Instrumental Track */}
             <div className="flex h-16 bg-zinc-950 rounded-md border border-white/5 overflow-hidden group hover:border-white/20 transition-colors">
               <div className="w-24 bg-zinc-800/50 border-r border-white/5 flex items-center justify-center text-xs text-zinc-400 font-medium p-2 shrink-0">Melody</div>
               <div className="flex-1 relative bg-gradient-to-r from-purple-900/10 to-transparent">
                  <div className="absolute inset-y-2 left-4 right-4 bg-[url('https://www.transparenttextures.com/patterns/black-scales.png')] opacity-10"></div>
               </div>
             </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar: Lyrics & Settings */}
      <div className="w-80 bg-zinc-900 flex flex-col border-l border-white/10 z-20">
        <div className="h-14 border-b border-white/10 flex items-center px-4 font-heading font-semibold">
          Inspector
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          
          {/* Sync Tab */}
          <div>
            <div className="flex items-center gap-2 mb-4 text-zinc-300">
              <Type className="w-4 h-4" />
              <h3 className="font-semibold text-sm">Transcribed Lyrics</h3>
            </div>
            
            <div className="space-y-2">
              {lyrics.map((line, idx) => (
                <div key={idx} className={`p-3 rounded-lg border text-sm transition-colors cursor-pointer ${idx === 0 ? "bg-blue-500/10 border-blue-500/30 text-blue-100" : "bg-black/20 border-white/5 text-zinc-400 hover:bg-black/40"}`}>
                  <p className="mb-2 leading-relaxed">{line.text}</p>
                  <div className="flex items-center justify-between font-mono text-[10px] text-zinc-500">
                    <span>{line.start}s</span>
                    <span className="w-full h-[1px] bg-white/5 mx-2"></span>
                    <span>{line.end}s</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Canvas Settings */}
          <div>
            <div className="flex items-center gap-2 mb-4 text-zinc-300 mt-8 pt-6 border-t border-white/10">
              <Settings className="w-4 h-4" />
              <h3 className="font-semibold text-sm">Visualizer Settings</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-zinc-500 mb-1 block">Animation Style</label>
                <select className="w-full bg-black/50 border border-white/10 rounded-md h-9 text-sm px-2 text-zinc-300">
                  <option>Karaoke Highlight</option>
                  <option>Kinetic Bounce</option>
                  <option>Fade In/Out</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-zinc-500 mb-1 block">Font Family</label>
                <select className="w-full bg-black/50 border border-white/10 rounded-md h-9 text-sm px-2 text-zinc-300">
                  <option>Permanent Marker</option>
                  <option>Inter</option>
                  <option>Outfit (Heading)</option>
                  <option>Bebas Neue</option>
                </select>
              </div>
            </div>
          </div>

        </div>
      </div>
      
    </div>
  );
}
