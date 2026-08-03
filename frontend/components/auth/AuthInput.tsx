"use client";

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface AuthInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  isPassword?: boolean;
}

export function AuthInput({ label, isPassword, className, ...props }: AuthInputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="space-y-2">
      <label className="text-[13px] font-medium text-slate-300">
        {label}
      </label>
      <div className={cn(
        "relative rounded-xl border transition-all duration-200 overflow-hidden bg-white/5",
        isFocused ? "border-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.1)]" : "border-white/10"
      )}>
        <input
          {...props}
          type={isPassword && !showPassword ? "password" : "text"}
          onFocus={(e) => {
            setIsFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            props.onBlur?.(e);
          }}
          className={cn(
            "w-full h-[48px] md:h-[52px] bg-transparent px-4 text-[15px] text-white placeholder:text-slate-500 outline-none",
            className
          )}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
            aria-label="Toggle password visibility"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
    </div>
  );
}
