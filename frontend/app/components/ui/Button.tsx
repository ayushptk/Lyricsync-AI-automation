import * as React from "react"
import { cn } from "@/app/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'glass';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    
    const baseStyles = "inline-flex items-center justify-center whitespace-nowrap rounded-xl font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-95";
    
    const variants = {
      default: "bg-blue-600 text-white hover:bg-blue-700 shadow-md shadow-blue-500/20",
      outline: "border border-border bg-transparent hover:bg-zinc-800 text-foreground",
      ghost: "hover:bg-zinc-800 hover:text-foreground text-zinc-300",
      glass: "glass hover:bg-zinc-800/80 text-foreground border border-white/10 shadow-[0_0_15px_rgba(255,255,255,0.05)]",
    }
    
    const sizes = {
      default: "h-11 px-6 py-2",
      sm: "h-9 rounded-md px-3 text-sm",
      lg: "h-14 rounded-2xl px-8 text-lg",
      icon: "h-10 w-10",
    }
    
    return (
      <button
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
