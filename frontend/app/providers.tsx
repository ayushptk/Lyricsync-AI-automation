"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useState, useEffect } from "react";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";

function AuthInit({ children }: { children: ReactNode }) {
  const { setUser } = useAuthStore();

  useEffect(() => {
    const initAuth = async () => {
      try {
        const response = await api.get("/api/v1/auth/me");
        setUser(response.data);
      } catch (error) {
        setUser(null); // This clears the user and sets isLoading to false
      }
    };
    initAuth();
  }, [setUser]);

  return <>{children}</>;
}

export default function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthInit>
        {children}
      </AuthInit>
    </QueryClientProvider>
  );
}
