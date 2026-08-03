"use client";

import { useRef } from "react";
import { motion, useInView, useScroll, useTransform } from "framer-motion";
import { ArrowRight, Zap, Mic2, Film, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { Button } from "./ui/Button";

/* ─────────────────────────────────────────────────────────
   Shared animation variants
──────────────────────────────────────────────────────────── */
const fadeUp = {
  hidden: { opacity: 0, y: 36 },
  visible: (delay = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.22, 0.61, 0.36, 1], delay },
  }),
};

const fadeLeft = {
  hidden: { opacity: 0, x: 48 },
  visible: (delay = 0) => ({
    opacity: 1,
    x: 0,
    transition: { duration: 0.8, ease: [0.22, 0.61, 0.36, 1], delay },
  }),
};

/* ─────────────────────────────────────────────────────────
   Feature pill
──────────────────────────────────────────────────────────── */
const Feature = ({
  icon: Icon,
  label,
  delay,
}: {
  icon: React.ElementType;
  label: string;
  delay: number;
}) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={inView ? "visible" : "hidden"}
      custom={delay}
      variants={fadeUp}
      className="flex items-center gap-3 text-light-text/80"
    >
      <CheckCircle2 className="h-4 w-4 shrink-0 text-[#c0180a]" />
      <span className="font-sans text-sm font-medium">{label}</span>
    </motion.div>
  );
};



/* ─────────────────────────────────────────────────────────
   Stat counter
──────────────────────────────────────────────────────────── */
const Stat = ({ value, label, delay }: { value: string; label: string; delay: number }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={inView ? "visible" : "hidden"}
      custom={delay}
      variants={fadeUp}
      className="flex flex-col"
    >
      <span className="font-heading text-3xl md:text-4xl font-semibold text-light-text tracking-tight">
        {value}
      </span>
      <span className="font-sans text-xs text-light-text/50 mt-1">{label}</span>
    </motion.div>
  );
};

/* ─────────────────────────────────────────────────────────
   Main export — "Precision at Scale" section
──────────────────────────────────────────────────────────── */
export default function PrecisionSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const textRef = useRef(null);
  const cardRef = useRef(null);

  const textInView = useInView(textRef, { once: true, margin: "-80px" });
  const cardInView = useInView(cardRef, { once: true, margin: "-80px" });

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start end", "end start"],
  });
  const cardY = useTransform(scrollYProgress, [0, 1], [40, -40]);

  return (
    <section
      ref={sectionRef}
      id="precision"
      className="w-full bg-light-surface text-light-text overflow-hidden"
      style={{ paddingTop: "clamp(72px, 9vw, 112px)", paddingBottom: "clamp(72px, 9vw, 112px)" }}
    >
      <div className="max-w-7xl mx-auto px-6">

        {/* ── Top stats row ── */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0 }}
          whileInView={{ opacity: 1, scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.22, 0.61, 0.36, 1] }}
          className="h-px bg-light-text/10 mb-14 origin-left"
        />
        <div className="grid grid-cols-3 gap-8 mb-20">
          <Stat value="< 2s"   label="stem isolation time"    delay={0}    />
          <Stat value="±4ms"   label="lyric sync accuracy"    delay={0.1}  />
          <Stat value="4K/60"  label="export quality ceiling" delay={0.2}  />
        </div>

        {/* ── Main two-column layout ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">

          {/* LEFT — copy */}
          <div ref={textRef} className="flex flex-col gap-8">

            {/* eyebrow */}
            <motion.div
              initial="hidden"
              animate={textInView ? "visible" : "hidden"}
              custom={0}
              variants={fadeUp}
              className="flex items-center gap-2"
            >
              <Zap className="h-4 w-4 text-[#c0180a]" />
              <span className="font-heading text-xs font-semibold tracking-[0.18em] text-light-text/50 uppercase">
                Built for Creators
              </span>
            </motion.div>

            {/* headline */}
            <motion.h2
              initial="hidden"
              animate={textInView ? "visible" : "hidden"}
              custom={0.08}
              variants={fadeUp}
              className="font-heading text-4xl md:text-5xl font-semibold tracking-tight leading-[1.08]"
            >
              Lyric precision<br />
              <span className="text-[#c0180a]">at production scale.</span>
            </motion.h2>

            {/* body */}
            <motion.p
              initial="hidden"
              animate={textInView ? "visible" : "hidden"}
              custom={0.16}
              variants={fadeUp}
              className="text-light-text/65 text-[17px] leading-[1.75] font-sans max-w-[440px]"
            >
              LyricSync isolates vocal stems, maps every syllable with millisecond accuracy, and
              renders cinematic lyric videos ready for YouTube — all in under a minute.
            </motion.p>

            {/* feature list */}
            <div className="flex flex-col gap-3 pt-1">
              <Feature icon={Mic2}   label="AI stem isolation via Demucs"            delay={0.22} />
              <Feature icon={Zap}    label="Word-level timestamping with Whisper"     delay={0.28} />
              <Feature icon={Film}   label="Cinematic 4K MP4 export"                  delay={0.34} />
            </div>

            {/* CTA */}
            <motion.div
              initial="hidden"
              animate={textInView ? "visible" : "hidden"}
              custom={0.42}
              variants={fadeUp}
              className="pt-2"
            >
              <Link href="/upload">
                <Button
                  size="md"
                  className="group bg-[#11100e] text-[#f4f1ea] hover:bg-[#2a2825] flex items-center gap-2"
                >
                  Start Creating
                  <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                </Button>
              </Link>
            </motion.div>
          </div>

          {/* RIGHT — tech-mock.png with parallax */}
          <motion.div
            ref={cardRef}
            initial="hidden"
            animate={cardInView ? "visible" : "hidden"}
            custom={0.1}
            variants={fadeLeft}
            style={{ y: cardY }}
            className="relative"
          >
            {/* Subtle red glow behind the image */}
            <div className="absolute -inset-6 bg-[#c0180a]/8 rounded-3xl blur-2xl pointer-events-none" />

            {/* Image */}
            <motion.div
              className="relative overflow-hidden rounded-2xl border border-black/8 shadow-[0_32px_64px_rgba(0,0,0,0.14)]"
              whileHover={{ scale: 1.015 }}
              transition={{ duration: 0.5, ease: [0.22, 0.61, 0.36, 1] }}
            >
              <img
                src="/tech-mock.png"
                alt="LyricSync workspace preview"
                className="w-full h-full object-cover block"
                draggable={false}
              />
              {/* Subtle gradient overlay at bottom for depth */}
              <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/10 to-transparent pointer-events-none rounded-b-2xl" />
              {/* Low-opacity LyricSync watermark */}
              <div className="absolute inset-0 flex items-end justify-start p-5 pointer-events-none select-none">
                <span
                  className="font-heading font-semibold tracking-tight"
                  style={{ fontSize: "clamp(1.3rem, 2.5vw, 2rem)", color: "rgba(244,241,234,0.55)", letterSpacing: "-0.025em" }}
                >
                  LyricSync<span style={{ color: "rgba(192,24,10,0.70)" }}>.</span>
                </span>
              </div>
            </motion.div>

            
          </motion.div>
        </div>

        {/* ── Bottom divider ── */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0 }}
          whileInView={{ opacity: 1, scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.22, 0.61, 0.36, 1] }}
          className="h-px bg-light-text/10 mt-20 origin-right"
        />
      </div>
    </section>
  );
}
