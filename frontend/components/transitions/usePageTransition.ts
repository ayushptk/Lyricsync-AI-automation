"use client";

import { create } from "zustand";
import { useRouter } from "next/navigation";
import { useCallback, useRef } from "react";

/* ─────────────────────────────────────────────────────────
   Transition store — shared across all components
──────────────────────────────────────────────────────────── */
interface TransitionStore {
  isTransitioning: boolean;
  phase: "idle" | "cover" | "covered" | "reveal";
  pendingRoute: string | null;
  setPhase: (phase: TransitionStore["phase"]) => void;
  setTransitioning: (val: boolean) => void;
  setPendingRoute: (route: string | null) => void;
}

export const useTransitionStore = create<TransitionStore>((set) => ({
  isTransitioning: false,
  phase: "idle",
  pendingRoute: null,
  setPhase: (phase) => set({ phase }),
  setTransitioning: (val) => set({ isTransitioning: val }),
  setPendingRoute: (route) => set({ pendingRoute: route }),
}));

/* ─────────────────────────────────────────────────────────
   Hook — call this to trigger a transition navigation
──────────────────────────────────────────────────────────── */
export function usePageTransition() {
  const router = useRouter();
  const { isTransitioning, setPhase, setTransitioning, pendingRoute, setPendingRoute } = useTransitionStore();

  const navigateTo = useCallback(
    (href: string) => {
      // Prevent double-click during active transition
      if (isTransitioning) return;

      setPendingRoute(href);
      setTransitioning(true);
      setPhase("cover");
    },
    [isTransitioning, setPhase, setTransitioning, setPendingRoute]
  );

  // Called by the overlay when fully covered — safe to navigate now
  const onCovered = useCallback(() => {
    setPhase("covered");
    if (pendingRoute) {
      router.push(pendingRoute);
      setPendingRoute(null);
    }
    // Small delay so the new page mounts underneath before reveal starts
    setTimeout(() => {
      setPhase("reveal");
    }, 120);
  }, [router, setPhase, pendingRoute, setPendingRoute]);

  // Called by the overlay when reveal is complete
  const onRevealDone = useCallback(() => {
    setPhase("idle");
    setTransitioning(false);
  }, [setPhase, setTransitioning]);

  return { navigateTo, onCovered, onRevealDone, isTransitioning };
}
