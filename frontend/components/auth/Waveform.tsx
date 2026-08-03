"use client";

import { useEffect, useRef } from "react";

interface WaveformProps {
  authStatus: "idle" | "signing_in" | "syncing" | "ready" | "success";
}

export function Waveform({ authStatus }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let time = 0;

    // Handle resize
    const resize = () => {
      const parent = canvas.parentElement;
      if (parent) {
        const dpr = window.devicePixelRatio || 1;
        canvas.width = parent.clientWidth * dpr;
        canvas.height = parent.clientHeight * dpr;
        ctx.scale(dpr, dpr);
        canvas.style.width = `${parent.clientWidth}px`;
        canvas.style.height = `${parent.clientHeight}px`;
      }
    };

    window.addEventListener("resize", resize);
    resize();

    // Mouse interaction
    let mouseX = -1000;
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
    };
    window.addEventListener("mousemove", handleMouseMove);

    // Render loop
    const render = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      ctx.clearRect(0, 0, width, height);

      time += 0.015;

      // Determine base amplitude based on authStatus
      let baseAmplitude = 50;
      let speedMultiplier = 1;
      
      if (authStatus === "signing_in") {
        baseAmplitude = 80;
        speedMultiplier = 1.5;
      } else if (authStatus === "syncing") {
        baseAmplitude = 120;
        speedMultiplier = 2.5;
      } else if (authStatus === "ready" || authStatus === "success") {
        baseAmplitude = 180;
        speedMultiplier = 3.5;
      }

      time += 0.015 * (speedMultiplier - 1); // Extra speed

      // Helper to draw a single smooth wave line
      const drawLine = (offset: number, ampMult: number, color: string, lineWidth: number, blur = 0) => {
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        
        if (blur > 0) {
          ctx.shadowBlur = blur;
          ctx.shadowColor = color;
        } else {
          ctx.shadowBlur = 0;
        }

        const points = 150;
        for (let i = 0; i <= points; i++) {
          const x = (i / points) * width;
          
          // Mouse influence
          const dist = Math.abs(x - mouseX);
          const mouseInfluence = Math.max(0, 1 - dist / 250) * 40;

          // Complex wave combination
          const wave1 = Math.sin(x * 0.005 + time + offset);
          const wave2 = Math.sin(x * 0.01 - time * 0.8 + offset);
          const wave3 = Math.sin(x * 0.02 + time * 1.5);
          
          // Envelop to taper edges smoothly
          const envelope = Math.sin((i / points) * Math.PI);
          
          const yOffset = (wave1 * 0.5 + wave2 * 0.3 + wave3 * 0.2) * (baseAmplitude * ampMult + mouseInfluence) * envelope;
          
          const y = height / 2 + yOffset;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      };

      // Draw Layers
      drawLine(0, 1.2, "rgba(99, 102, 241, 0.15)", 8, 20); // Background ambient glow
      drawLine(Math.PI, 0.8, "rgba(139, 92, 246, 0.3)", 3, 5); // Mid layer
      drawLine(0, 1, "rgba(224, 231, 255, 0.8)", 1.5, 0); // Crisp front layer

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, [authStatus]);

  return (
    <div className="w-full h-full relative">
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 w-full h-full"
      />
    </div>
  );
}
