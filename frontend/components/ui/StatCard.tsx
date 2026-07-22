import React from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { cn } from "@/components/ui/Button";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
  className?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export function StatCard({ title, value, icon, description, className, trend }: StatCardProps) {
  return (
    <Card className={cn("overflow-hidden bg-white/5 backdrop-blur-xl border-white/10 hover:bg-white/10 transition-all duration-300", className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-400">{title}</p>
            <div className="flex items-baseline gap-2 mt-2">
              <h3 className="text-3xl font-bold text-white">{value}</h3>
              {trend && (
                <span className={cn("text-xs font-medium", trend.isPositive ? "text-emerald-400" : "text-rose-400")}>
                  {trend.isPositive ? "+" : "-"}{trend.value}%
                </span>
              )}
            </div>
            {description && (
              <p className="text-xs text-slate-500 mt-1">{description}</p>
            )}
          </div>
          <div className="p-3 bg-white/5 rounded-xl text-indigo-400">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
