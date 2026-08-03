import Link from "next/link";
import { Button } from "../components/ui/Button";
import { Play, Sparkles, AudioLines, Music, ArrowRight } from "lucide-react";
import FrameworkSection from "../components/FrameworkSection";
import PrecisionSection from "../components/PrecisionSection";
import NavBar from "../components/NavBar";

export default function Home() {
  return (
    <main className="min-h-screen bg-background selection:bg-accent selection:text-white ">
      
      {/* Navigation Layer */}
      <NavBar />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden">
        {/* Background Layer */}
        <div className="absolute inset-0 z-0">
           <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-transparent to-background z-10" />
           <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent z-10 h-full" />
           <video 
             src="/0803.mp4" 
             autoPlay 
             loop 
             muted 
             playsInline
             className="w-full h-full object-cover opacity-60 scale-[1.03]"
           />
        </div>

        {/* Foreground Content */}
        <div className="z-20 max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-12 gap-8 w-full mt-12">
          <div className="md:col-span-8 flex flex-col items-start gap-8">
            

            <h1 className="font-heading text-5xl md:text-7xl lg:text-[80px] font-medium tracking-[-0.025em] text-text-primary leading-[1.1] opacity-0 animate-[reveal_700ms_cubic-bezier(.22,.61,.36,1)_100ms_forwards]">
              Turn audio into <br/>
              <span className="text-text-muted">visual tension.</span>
            </h1>
            
            <p className="text-lg text-text-secondary max-w-xl leading-[1.75] font-sans opacity-0 animate-[reveal_700ms_cubic-bezier(.22,.61,.36,1)_200ms_forwards]">
              A cinematic approach to lyric video creation. Isolate stems, map syllables, and export with professional-grade motion design. Built for high-contrast aesthetic.
            </p>

            <div className="flex flex-col sm:flex-row items-center gap-4 mt-4 opacity-0 animate-[reveal_700ms_cubic-bezier(.22,.61,.36,1)_300ms_forwards]">
              <Link href="/upload">
                <Button size="lg" className="group">
                  Start Creating
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Process Section */}
      <FrameworkSection />

      {/* Precision / Feature Section — animated with Framer Motion */}
      <PrecisionSection />

      {/* Footer Section */}
      <footer id="footer" className="w-full bg-background border-t border-white/5 pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-20">
            <div className="col-span-1 md:col-span-2">
              <h3 className="font-heading font-medium text-3xl tracking-tight mb-6">
                LyricSync<span className="text-accent">.</span>
              </h3>
              <p className="text-text-secondary text-sm max-w-sm leading-[1.75]">
                LyricSync integration for cinematic audio processing and lyric generation. Designed for scale and precision.
              </p>
            </div>
            
            <div>
              <h4 className="font-heading font-medium text-lg mb-6">Product</h4>
              <ul className="flex flex-col gap-4 text-sm text-text-secondary">
                <li><Link href="/features" className="hover:text-accent transition-colors">Features</Link></li>
                <li><Link href="/showcase" className="hover:text-accent transition-colors">Showcase</Link></li>
                <li><Link href="/changelog" className="hover:text-accent transition-colors">Changelog</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-heading font-medium text-lg mb-6">Legal</h4>
              <ul className="flex flex-col gap-4 text-sm text-text-secondary">
                <li><Link href="/terms" className="hover:text-accent transition-colors">Terms of Service</Link></li>
                <li><Link href="/privacy" className="hover:text-accent transition-colors">Privacy Policy</Link></li>
                <li><Link href="/contact" className="hover:text-accent transition-colors">Contact Us</Link></li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col md:flex-row items-center justify-between pt-8 border-t border-white/5 text-sm text-text-muted relative z-10">
            <p>&copy; {new Date().getFullYear()} LyricSync. All rights reserved.</p>
            <div className="flex gap-6 mt-4 md:mt-0">
              <Link href="#" className="hover:text-text-primary transition-colors">Twitter</Link>
              <Link href="#" className="hover:text-text-primary transition-colors">GitHub</Link>
              <Link href="#" className="hover:text-text-primary transition-colors">Discord</Link>
            </div>
          </div>

          {/* Large Modern Footer Text */}
          <div className="w-full flex justify-center pt-16 pb-4 overflow-hidden select-none pointer-events-none">
            <h1 className="font-heading font-bold text-[18vw] leading-[0.8] tracking-tighter text-[#f4f1ea] opacity-30">
              LyricSync<span className="text-[#f04a23]">.</span>
            </h1>
          </div>
        </div>
      </footer>

    </main>
  );
}
