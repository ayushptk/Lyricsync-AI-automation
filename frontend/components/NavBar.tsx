"use client";

import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { usePageTransition } from "@/components/transitions/usePageTransition";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";

export default function NavBar() {
  const { navigateTo, isTransitioning } = usePageTransition();
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const intersectingSections = new Set<string>();
    
    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          intersectingSections.add(entry.target.id);
        } else {
          intersectingSections.delete(entry.target.id);
        }
      });
      
      setIsVisible(intersectingSections.size === 0);
    };

    const observer = new IntersectionObserver(observerCallback, {
      root: null,
      threshold: 0.05,
    });

    const setupObserver = () => {
      const precisionSec = document.getElementById("precision");
      const footerSec = document.getElementById("footer");
      
      if (precisionSec) observer.observe(precisionSec);
      if (footerSec) observer.observe(footerSec);
    };

    // Wait for DOM to be ready
    const timeoutId = setTimeout(setupObserver, 100);

    return () => {
      clearTimeout(timeoutId);
      observer.disconnect();
    };
  }, []);

  return (
    <motion.nav 
      initial={{ y: 0 }}
      animate={{ y: isVisible ? 0 : -100 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="fixed top-0 w-full h-[80px] z-50 flex items-center px-6 md:px-12"
    >
      <div className="flex items-center justify-between w-full max-w-7xl mx-auto">
        <div className="font-heading font-semibold text-xl tracking-tighter">
          LyricSync<span className="text-accent">.</span>
        </div>
        <div className="flex items-center gap-6">
          {/* Login — triggers geometric purple transition */}
          <button
            onClick={() => navigateTo("/login")}
            disabled={isTransitioning}
            className="text-text-secondary hover:text-text-primary transition-colors text-sm font-medium disabled:cursor-not-allowed disabled:opacity-70"
          >
            Log in
          </button>
          <Link href="/upload">
            <Button size="sm">Get Started</Button>
          </Link>
        </div>
      </div>
    </motion.nav>
  );
}
