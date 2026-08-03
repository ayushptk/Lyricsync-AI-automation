"use client";

import React, { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { TvMinimalPlay } from 'lucide-react';
import { Guitar } from 'lucide-react';
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger, useGSAP);
}

export default function FrameworkSection() {
  const sectionRef = useRef<HTMLElement>(null);

  useGSAP(() => {
    if (!sectionRef.current) return;

    /* -------------------------------------------------------
     * Main scroll animation timeline
     * ----------------------------------------------------- */
    const timeline = gsap.timeline({
      scrollTrigger: {
        trigger: sectionRef.current,
        start: "top top",
        end: "+=4000",
        pin: true,
        scrub: 1,
        anticipatePin: 1,
        invalidateOnRefresh: true,
      },
    });

    /* INITIAL STATE */
    gsap.set(".full-image-overlay", { opacity: 1 });
    gsap.set(".card-wrapper", { transformPerspective: 2000 });
    gsap.set(
      [".card-inner-left", ".card-inner-center", ".card-inner-right"],
      { transformStyle: "preserve-3d" }
    );

    /* STEP 1 — Zoom full image */
    timeline.to(".hero-container", {
      scale: 1.035,
      duration: 1,
      ease: "power2.inOut",
    });

    /* STEP 2 — Fade full image */
    timeline.to(
      ".full-image-overlay",
      { opacity: 0, duration: 0.4, ease: "power2.inOut" },
      "+=0.15"
    );

    /* STEP 3 — Fan cards out */
    timeline
      .to(
        ".card-left",
        { xPercent: -28, yPercent: 6, rotateZ: -10, z: 50, duration: 1.25, ease: "power2.inOut" },
        "<"
      )
      .to(
        ".card-center",
        { yPercent: -6, z: 80, duration: 1.25, ease: "power2.inOut" },
        "<"
      )
      .to(
        ".card-right",
        { xPercent: 28, yPercent: 6, rotateZ: 10, z: 50, duration: 1.25, ease: "power2.inOut" },
        "<"
      );

    /* STEP 4 — Drop shadow */
    timeline.to(
      ".card-wrapper",
      { filter: "drop-shadow(0px 28px 32px rgba(0,0,0,0.65))", duration: 0.5, ease: "power2.out" },
      "<"
    );

    /* STEP 5 — 3D flip */
    timeline
      .to(".card-inner-left",   { rotateY: 180, duration: 1.4, ease: "power3.inOut" }, "+=0.25")
      .to(".card-inner-center", { rotateY: 180, duration: 1.4, ease: "power3.inOut" }, "-=1")
      .to(".card-inner-right",  { rotateY: 180, duration: 1.4, ease: "power3.inOut" }, "-=1");

    /* STEP 6 — Heading reveal */
    timeline.to(
      ".final-text",
      { opacity: 1, y: 0, duration: 0.8, ease: "power3.out" },
      "-=0.9"
    );

    /* Floating loop */
    const floatingAnimation = gsap.to(".card-wrapper", {
      y: "-=8",
      duration: 2.8,
      ease: "sine.inOut",
      yoyo: true,
      repeat: -1,
      stagger: { amount: 0.7, from: "center" },
      paused: true,
    });

    ScrollTrigger.create({
      trigger: sectionRef.current,
      start: "top top",
      end: "+=4000",
      onUpdate: (self) => {
        if (self.progress > 0.92) floatingAnimation.play();
        else floatingAnimation.pause();
      },
    });
  }, { scope: sectionRef });

  /* =========================================================
   *  ICON SVGs — adapted for LyricSync
   * ======================================================= */

  /** Audio waveform / stem isolation icon — left silver card */
  const IsolationIcon = () => (
    <svg width="30" height="22" viewBox="0 0 30 22" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ opacity: 0.55 }}>
      <line x1="1"  y1="11" x2="1"  y2="11" stroke="#11100e" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="5"  y1="7"  x2="5"  y2="15" stroke="#11100e" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="9"  y1="3"  x2="9"  y2="19" stroke="#11100e" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="13" y1="8"  x2="13" y2="14" stroke="#11100e" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="17" y1="5"  x2="17" y2="17" stroke="#11100e" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="21" y1="9"  x2="21" y2="13" stroke="#11100e" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="25" y1="6"  x2="25" y2="16" stroke="#11100e" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="29" y1="11" x2="29" y2="11" stroke="#11100e" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );




  return (
    <section
      id="framework"
      ref={sectionRef}
      className="relative z-20 flex h-screen w-full flex-col items-center justify-center overflow-hidden bg-background text-text-primary [perspective:2000px] border-y border-white/5"
    >
      {/* Background gradient */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-transparent to-background z-10" />
      </div>

      {/* =====================================================
          HEADING (revealed after flip)
      ====================================================== */}
      <div className="final-text relative z-30 mb-10 w-full -translate-y-4 px-4 text-center opacity-0 -top-10">
        <h2 className="font-heading text-2xl md:text-2xl lg:text-[44px] font-medium tracking-tight mb-4">
          The <span className="text-accent italic">Framework</span>.
        </h2>
        <p className="text-text-secondary text-sm md:text-sm lg:text-[16px] max-w-2xl mx-auto font-sans leading-[1.75]">
          A structured, technical process for extracting and visualizing audio layers.
        </p>
      </div>

      {/* =====================================================
          CARD STAGE
          Cards are grouped tightly together in the center,
          just like the reference image — three portrait cards
          sitting side-by-side with minimal gap.
      ====================================================== */}
      <div
        className="hero-container relative z-10 overflow-visible [perspective:2000px]"
        style={{
          /* Three portrait cards side-by-side, each ~240px wide, 2px gap */
          width: "clamp(480px, 55vw, 760px)",
          height: "clamp(320px, 42vh, 480px)",
        }}
      >
        {/* Full-image overlay (fades out on scroll) */}
        <div className="full-image-overlay pointer-events-none absolute inset-0 z-30 overflow-hidden rounded-[18px] border border-white/10">
          <img
            src="Serviceimage.png"
            alt="LyricSync service overview"
            className="h-full w-full object-cover"
            draggable={false}
          />
        </div>

        {/* =================================================
            LEFT CARD — Silver / Light Gray
            "Isolation" — vocal stem extraction
        ================================================== */}
        <div className="card-wrapper card-left absolute left-0 top-0 h-full w-1/3">
          <div
            className="card-inner-left relative h-full w-full"
            style={{ transformStyle: "preserve-3d" }}
          >
            {/* Front: image slice */}
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: "url('/Serviceimage.png')",
                backgroundSize: "300% 100%",
                backgroundPosition: "0% 50%",
                backfaceVisibility: "hidden",
                borderRadius: "18px 0 0 18px",
              }}
            />

            {/* Back: silver card — matches reference left card */}
            <div
              className="absolute inset-0 flex flex-col justify-between overflow-hidden"
              style={{
                backfaceVisibility: "hidden",
                transform: "rotateY(180deg)",
                backgroundColor: "#c8c5c0",
                borderRadius: "22px",
                padding: "clamp(18px, 2vw, 28px)",
              }}
            >
              {/* Icon top-left */}
              <div><IsolationIcon /></div>

              {/* Title + body anchored to bottom */}
              <div style={{ display: "flex", flexDirection: "column", gap: "40px" }}>
                <h3
                  className="font-heading font-semibold leading-[1.1]"
                  style={{
                    color: "#11100e",
                    fontSize: "clamp(1.2rem, 2vw, 1.8rem)",
                  }}
                >
                  Stem<br />Isolation
                </h3>
                <p
                  className="font-sans font-light leading-relaxed"
                  style={{
                    color: "rgba(17,16,14,0.6)",
                    fontSize: "clamp(0.75rem, 0.95vw, 0.88rem)",
                  }}
                >
                  AI-powered models strip noise and instrumentals, delivering a pristine vocal track ready for lyric mapping.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* =================================================
            CENTER CARD — Vivid Red Gradient
            "Synchronization" — word-level timestamping
        ================================================== */}
        <div className="card-wrapper card-center absolute left-1/3 top-0 h-full w-1/3">
          <div
            className="card-inner-center relative h-full w-full"
            style={{ transformStyle: "preserve-3d" }}
          >
            {/* Front: image slice */}
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: "url('/Serviceimage.png')",
                backgroundSize: "300% 100%",
                backgroundPosition: "50% 50%",
                backfaceVisibility: "hidden",
              }}
            />

            {/* Back: red gradient card — matches reference center card */}
            <div
              className="absolute inset-0 flex flex-col justify-between overflow-hidden"
              style={{
                backfaceVisibility: "hidden",
                transform: "rotateY(180deg)",
                background: "linear-gradient(165deg, #e8291a 0%, #c0180a 55%, #8b0f06 100%)",
                borderRadius: "22px",
                padding: "clamp(18px, 2vw, 28px)",
              }}
            >
              {/* Icon top-left */}
              <div><Guitar /></div>

              {/* Title + body anchored to bottom */}
              <div style={{ display: "flex", flexDirection: "column", gap: "40px" }}>
                <h3
                  className="font-heading font-semibold leading-[1.1]"
                  style={{
                    color: "#ffffff",
                    fontSize: "clamp(1.2rem, 2vw, 1.8rem)",
                  }}
                >
                  Lyric<br />Sync
                </h3>
                <p
                  className="font-sans font-light leading-relaxed"
                  style={{
                    color: "rgba(255,255,255,0.75)",
                    fontSize: "clamp(0.75rem, 0.95vw, 0.88rem)",
                  }}
                >
                  Whisper-powered word-level timestamping snaps every syllable to the grid with millisecond precision.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* =================================================
            RIGHT CARD — Dark Charcoal
            "Rendering" — 4K cinematic export
        ================================================== */}
        <div className="card-wrapper card-right absolute left-2/3 top-0 h-full w-1/3">
          <div
            className="card-inner-right relative h-full w-full"
            style={{ transformStyle: "preserve-3d" }}
          >
            {/* Front: image slice */}
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: "url('/Serviceimage.png')",
                backgroundSize: "300% 100%",
                backgroundPosition: "100% 50%",
                backfaceVisibility: "hidden",
                borderRadius: "0 18px 18px 0",
              }}
            />

            {/* Back: dark charcoal card — matches reference right card */}
            <div
              className="absolute inset-0 flex flex-col justify-between overflow-hidden"
              style={{
                backfaceVisibility: "hidden",
                transform: "rotateY(180deg)",
                backgroundColor: "#1a1a1a",
                borderRadius: "22px",
                padding: "clamp(18px, 2vw, 28px)",
              }}
            >
              {/* Icon top-left */}
              <div> <TvMinimalPlay /></div>

              {/* Title + body anchored to bottom */}
              <div style={{ display: "flex", flexDirection: "column", gap: "40px" }}>
                <h3
                  className="font-heading font-semibold leading-[1.1]"
                  style={{
                    color: "#ffffff",
                    fontSize: "clamp(1.2rem, 2vw, 1.8rem)",
                  }}
                >
                  4K<br />Render
                </h3>
                <p
                  className="font-sans font-light leading-relaxed"
                  style={{
                    color: "rgba(255,255,255,0.75)",
                    fontSize: "clamp(0.75rem, 0.95vw, 0.88rem)",
                  }}
                >
                  Cinematic motion curves and high-contrast typography, exported directly to 4K MP4 for distribution.
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
