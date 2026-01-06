import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'default' | 'outline' | 'ghost';
    size?: 'default' | 'sm' | 'lg' | 'icon';
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'default', size = 'default', ...props }, ref) => {
        return (
            <button
                className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 disabled:opacity-50 disabled:pointer-events-none ring-offset-slate-950",
                    {
                        'bg-slate-50 text-slate-900 hover:bg-slate-50/90': variant === 'default',
                        'border border-slate-800 hover:bg-slate-800 hover:text-slate-50': variant === 'outline',
                        'hover:bg-slate-800 hover:text-slate-50': variant === 'ghost',
                        'h-10 py-2 px-4': size === 'default',
                        'h-9 px-3 rounded-md': size === 'sm',
                        'h-11 px-8 rounded-md': size === 'lg',
                        'h-10 w-10': size === 'icon',
                    },
                    className
                )}
                ref={ref}
                {...props}
            />
        )
    }
)
Button.displayName = "Button"

export { Button }
