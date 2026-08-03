import { AuthLayout } from "@/components/auth/AuthLayout";

export default function AuthGroupLayer({ children }: { children: React.ReactNode }) {
  return <AuthLayout>{children}</AuthLayout>;
}
