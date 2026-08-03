import React from "react";

export function DashboardBackground() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      {/* Base dark charcoal/midnight navy is set by globals.css body bg */}
      
      {/* Very subtle ambient gradient */}
      <div className="absolute top-0 left-0 right-0 h-[80vh] bg-gradient-to-b from-indigo-900/10 via-transparent to-transparent opacity-60" />
      
      {/* Subtle radial lighting / glow */}
      <div className="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] rounded-full bg-blue-600/5 blur-[120px]" />
      <div className="absolute top-[10%] -right-[10%] w-[50%] h-[50%] rounded-full bg-indigo-600/5 blur-[120px]" />
      
      {/* Optional: Add a very subtle noise/grain texture here if desired, 
          but usually standard gradients are cleaner for performance unless using an optimized SVG. */}
    </div>
  );
}
