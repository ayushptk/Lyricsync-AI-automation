"use client";

import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import api from "@/lib/api";
import { AuthInput } from "@/components/auth/AuthInput";
import { GoogleAuthButton } from "@/components/auth/GoogleAuthButton";
import { useAuthUIStore } from "@/components/auth/AuthLayout";
import { Loader2 } from "lucide-react";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();
  const { status, setStatus } = useAuthUIStore();

  useEffect(() => {
    setStatus("idle");
  }, [setStatus]);

  const registerMutation = useMutation({
    mutationFn: async () => {
      setStatus("signing_in");
      await new Promise(r => setTimeout(r, 600));
      
      setStatus("syncing");
      const response = await api.post("/api/v1/auth/register", { email, password });
      
      setStatus("ready");
      await new Promise(r => setTimeout(r, 400));
      
      return response.data;
    },
    onSuccess: () => {
      setStatus("success");
      setTimeout(() => {
        router.push("/login?registered=true");
      }, 800);
    },
    onError: () => {
      setStatus("idle");
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (status !== "idle") return; 
    registerMutation.mutate();
  };

  return (
    <div className="w-full flex flex-col gap-8">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-medium tracking-tight mb-2 font-heading">Create an Account</h2>
        <p className="text-sm text-slate-400 font-sans">Join LyricSync to generate automated karaoke videos.</p>
      </div>

      <GoogleAuthButton />

      <div className="flex items-center gap-4 w-full">
        <div className="h-[1px] w-full bg-white/5"></div>
        <span className="text-[11px] font-medium text-slate-500 uppercase tracking-widest font-sans">OR</span>
        <div className="h-[1px] w-full bg-white/5"></div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-4">
          <AuthInput
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={status !== "idle"}
          />
          <AuthInput
            label="Password"
            isPassword
            placeholder="Create a strong password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            disabled={status !== "idle"}
          />
          
          <AnimatePresence>
            {registerMutation.isError && (
              <motion.p 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="text-[13px] text-red-400 font-medium"
              >
                Registration failed. This user may already exist.
              </motion.p>
            )}
          </AnimatePresence>
        </div>

        <motion.button
          whileHover={status === "idle" ? { y: -1, boxShadow: "0 10px 20px -10px rgba(99,102,241,0.3)" } : {}}
          whileTap={status === "idle" ? { scale: 0.98 } : {}}
          type="submit"
          disabled={status !== "idle"}
          className="relative w-full h-[48px] md:h-[52px] rounded-xl bg-accent hover:bg-accent-hover text-[15px] font-medium text-white shadow-sm transition-all overflow-hidden disabled:cursor-not-allowed group mt-2"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out" />
          
          <AnimatePresence mode="wait">
            {status === "idle" && (
              <motion.span key="idle" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                Create Account
              </motion.span>
            )}
            {status === "signing_in" && (
              <motion.span key="signing_in" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="flex items-center gap-2 justify-center">
                <Loader2 className="w-4 h-4 animate-spin opacity-70" /> Creating account...
              </motion.span>
            )}
            {status === "syncing" && (
              <motion.span key="syncing" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="flex items-center gap-2 justify-center">
                <Loader2 className="w-4 h-4 animate-spin opacity-70" /> Finalizing...
              </motion.span>
            )}
            {status === "ready" && (
              <motion.span key="ready" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="flex items-center gap-2 justify-center">
                Ready
              </motion.span>
            )}
            {status === "success" && (
              <motion.span key="success" initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center gap-2 justify-center">
                Redirecting...
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>

        <p className="text-[14px] text-slate-400 text-center pt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-white hover:text-accent transition-colors font-medium relative group inline-block">
            Sign in
            <span className="absolute -bottom-0.5 left-0 w-0 h-[1px] bg-accent-hover transition-all group-hover:w-full"></span>
          </Link>
        </p>
      </form>
    </div>
  );
}
