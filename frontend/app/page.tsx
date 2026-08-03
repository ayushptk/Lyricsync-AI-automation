import Link from "next/link";
import { Button } from "../components/ui/Button";
import { Play, Sparkles, AudioLines, Music, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col bg-background selection:bg-accent selection:text-white pb-32">
      
      {/* Navigation Layer */}
      <nav className="fixed top-0 w-full h-[80px] z-50  flex items-center px-6 md:px-12">
        <div className="flex items-center justify-between w-full max-w-7xl mx-auto">
          <div className="font-heading font-semibold text-xl tracking-tighter">LyricSync<span className="text-accent">.</span></div>
          <div className="flex items-center gap-6">
            <Link href="/login" className="text-text-secondary hover:text-text-primary transition-colors text-sm font-medium">Log in</Link>
            <Link href="/upload">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

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
      <section className="relative z-20 max-w-7xl mx-auto px-6 py-[112px] w-full">
        <div className="flex flex-col gap-4 mb-16">
          <h2 className="font-heading text-3xl md:text-5xl font-medium tracking-tight">The Framework.</h2>
          <p className="text-text-secondary text-lg max-w-2xl">A structured, technical process for extracting and visualizing audio layers.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Card 1 */}
          <div className="bg-surface p-8 rounded-md border border-white/5 hover:scale-[1.03] transition-transform duration-700 ease-[cubic-bezier(.22,.61,.36,1)] group">
            <div className="w-12 h-12 rounded-full bg-background flex items-center justify-center mb-12 text-text-muted group-hover:text-accent transition-colors">
              <AudioLines className="w-5 h-5" />
            </div>
            <h3 className="font-heading font-medium text-xl mb-3 text-text-primary">01. Isolation</h3>
            <p className="text-text-secondary text-sm leading-[1.75]">Advanced AI models strip away noise and instrumentals, leaving a pristine vocal track ready for analysis.</p>
          </div>

          {/* Card 2 */}
          <div className="bg-surface p-8 rounded-md border border-white/5 hover:scale-[1.03] transition-transform duration-700 ease-[cubic-bezier(.22,.61,.36,1)] group">
            <div className="w-12 h-12 rounded-full bg-background flex items-center justify-center mb-12 text-text-muted group-hover:text-accent transition-colors">
              <Music className="w-5 h-5" />
            </div>
            <h3 className="font-heading font-medium text-xl mb-3 text-text-primary">02. Synchronization</h3>
            <p className="text-text-secondary text-sm leading-[1.75]">Whisper-powered word-level timestamping ensures your lyrics snap to the grid with millisecond precision.</p>
          </div>

          {/* Card 3 */}
          <div className="bg-surface p-8 rounded-md border border-white/5 hover:scale-[1.03] transition-transform duration-700 ease-[cubic-bezier(.22,.61,.36,1)] group">
            <div className="w-12 h-12 rounded-full bg-background flex items-center justify-center mb-12 text-text-muted group-hover:text-accent transition-colors">
              <Play className="w-5 h-5" />
            </div>
            <h3 className="font-heading font-medium text-xl mb-3 text-text-primary">03. Rendering</h3>
            <p className="text-text-secondary text-sm leading-[1.75]">Apply cinematic motion curves and high-contrast typography. Export directly to 4K MP4 for distribution.</p>
          </div>
        </div>
      </section>

      {/* Light Surface / Instructional Section */}
      <section className="w-full bg-light-surface text-light-text py-[112px]">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          <div className="flex flex-col gap-6">
            <h2 className="font-heading text-4xl md:text-5xl font-medium tracking-tight">Precision at scale.</h2>
            <p className="text-light-text/70 text-lg leading-[1.75] font-sans">
              Our sand theme ensures legibility for technical documentation and process-heavy workflows. 
              The system adapts to maintain professional contrast and reduce visual fatigue during extended sessions.
            </p>
            <div className="pt-4">
              <Button className="bg-[#11100e] text-[#f4f1ea] hover:bg-[#2a2825]" size="md">
                Read Documentation
              </Button>
            </div>
          </div>
          <div className="aspect-[16/10] bg-[#dfd9ce] rounded-md border border-black/5 flex items-center justify-center overflow-hidden">
             <img src="/tech-mock.png" alt="Technical abstract representation" className="w-full h-full object-cover" />
          </div>
        </div>
      </section>

      {/* Footer Section */}
      <footer className="w-full bg-background border-t border-white/5 pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-20">
            <div className="col-span-1 md:col-span-2">
              <h3 className="font-heading font-medium text-3xl tracking-tight mb-6">
                LyricSync<span className="text-accent">.</span>
              </h3>
              <p className="text-text-secondary text-sm max-w-sm leading-[1.75]">
                Northline Visual System integration for cinematic audio processing and lyric generation. Designed for scale and precision.
              </p>
            </div>
            
            <div>
              <h4 className="font-heading font-medium text-lg mb-6">Product</h4>
              <ul className="flex flex-col gap-4 text-sm text-text-secondary">
                <li><Link href="/features" className="hover:text-accent transition-colors">Features</Link></li>
                <li><Link href="/pricing" className="hover:text-accent transition-colors">Pricing</Link></li>
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

          <div className="flex flex-col md:flex-row items-center justify-between pt-8 border-t border-white/5 text-sm text-text-muted">
            <p>&copy; {new Date().getFullYear()} LyricSync. All rights reserved.</p>
            <div className="flex gap-6 mt-4 md:mt-0">
              <Link href="#" className="hover:text-text-primary transition-colors">Twitter</Link>
              <Link href="#" className="hover:text-text-primary transition-colors">GitHub</Link>
              <Link href="#" className="hover:text-text-primary transition-colors">Discord</Link>
            </div>
          </div>
        </div>
      </footer>

    </main>
  );
}
