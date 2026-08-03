"use client";

import { useEffect, useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useTransitionStore, usePageTransition } from "./usePageTransition";

/* ─────────────────────────────────────────────────────────
   BLOCK DEFINITIONS
   5 vertical columns alternating origins from top and bottom.
──────────────────────────────────────────────────────────── */
const BLOCKS = [
  { left: "0%", origin: "top" },
  { left: "20%", origin: "bottom" },
  { left: "40%", origin: "top" },
  { left: "60%", origin: "bottom" },
  { left: "80%", origin: "top" },
] as const;

const BLOCK_COLOR = "#c5834c";
const COVER_DURATION = 0.5;  
const REVEAL_DURATION = 0.5; 
const STAGGER = 0.08;        
const EASE: [number, number, number, number] = [0.76, 0, 0.24, 1];

/* ─────────────────────────────────────────────────────────
   Single block
──────────────────────────────────────────────────────────── */
function Block({
  left,
  origin,
  coverDelay,
  revealDelay,
  phase,
  prefersReduced,
}: {
  left: string;
  origin: "top" | "bottom";
  coverDelay: number;
  revealDelay: number;
  phase: "cover" | "covered" | "reveal" | "idle";
  prefersReduced: boolean;
}) {
  const isCovering = phase === "cover" || phase === "covered";
  const targetScale = isCovering ? 1 : 0;
  const delay = isCovering ? coverDelay : revealDelay;
  const duration = isCovering ? COVER_DURATION : REVEAL_DURATION;

  // Change origin for reveal so it exits in the same direction it entered
  const currentOrigin = isCovering 
    ? origin 
    : (origin === "top" ? "bottom" : "top");

  if (prefersReduced) return null;

  return (
    <motion.div
      aria-hidden="true"
      style={{
        position: "absolute",
        left,
        top: 0,
        width: "20.2%", // 20.2% to prevent sub-pixel gaps between columns
        height: "100%",
        backgroundColor: BLOCK_COLOR,
        transformOrigin: currentOrigin,
        scaleY: 0,
      }}
      animate={{ scaleY: targetScale }}
      transition={{
        duration,
        delay,
        ease: EASE,
      }}
    />
  );
}

/* ─────────────────────────────────────────────────────────
   Main overlay — mounted once in the root layout
──────────────────────────────────────────────────────────── */
export default function TransitionOverlay() {
  const prefersReduced = useReducedMotion() ?? false;
  const { phase } = useTransitionStore();
  const { onCovered, onRevealDone } = usePageTransition();
  const coveredFired = useRef(false);
  const revealFired  = useRef(false);

  // After the last COVER block finishes → call onCovered
  useEffect(() => {
    if (phase !== "cover") {
      coveredFired.current = false;
      return;
    }
    const lastCoverEnd =
      (BLOCKS.length - 1) * STAGGER + COVER_DURATION;
    const timer = setTimeout(() => {
      if (!coveredFired.current) {
        coveredFired.current = true;
        onCovered();
      }
    }, lastCoverEnd * 1000 + 20); // +20ms buffer

    return () => clearTimeout(timer);
  }, [phase, onCovered]);

  // After the last REVEAL block finishes → call onRevealDone
  useEffect(() => {
    if (phase !== "reveal") {
      revealFired.current = false;
      return;
    }
    const lastRevealEnd =
      (BLOCKS.length - 1) * STAGGER + REVEAL_DURATION;
    const timer = setTimeout(() => {
      if (!revealFired.current) {
        revealFired.current = true;
        onRevealDone();
      }
    }, lastRevealEnd * 1000 + 20);

    return () => clearTimeout(timer);
  }, [phase, onRevealDone]);

  // Reduced motion: just navigate without overlay
  if (prefersReduced) return null;

  // Idle — nothing to render
  if (phase === "idle") return null;

  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 9999,
        pointerEvents: "all",
        overflow: "hidden",
      }}
    >
      {BLOCKS.map((block, i) => {
        const coverDelay  = i * STAGGER;
        const revealDelay = i * STAGGER; 

        return (
          <Block
            key={i}
            left={block.left}
            origin={block.origin}
            coverDelay={coverDelay}
            revealDelay={revealDelay}
            phase={phase}
            prefersReduced={prefersReduced}
          />
        );
      })}
    </div>
  );
}
