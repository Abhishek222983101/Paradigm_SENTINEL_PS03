"use client";

import { forwardRef } from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

type ButtonVariant = "default" | "cyan" | "crimson" | "amber" | "green" | "ghost" | "outline";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  children: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  default: "bg-white text-void border-white shadow-[4px_4px_0px_#fff] hover:shadow-[6px_6px_0px_#fff]",
  cyan: "bg-cyber-cyan text-void border-cyber-cyan shadow-[4px_4px_0px_#00B8CC] hover:shadow-[6px_6px_0px_#00E5FF]",
  crimson: "bg-neon-crimson text-white border-neon-crimson shadow-[4px_4px_0px_#CC0030] hover:shadow-[6px_6px_0px_#FF003C]",
  amber: "bg-warning-amber text-void border-warning-amber shadow-[4px_4px_0px_#CC9300] hover:shadow-[6px_6px_0px_#FFB800]",
  green: "bg-terminal-green text-void border-terminal-green shadow-[4px_4px_0px_#2ECC10] hover:shadow-[6px_6px_0px_#39FF14]",
  ghost: "bg-transparent text-white border-white shadow-none hover:bg-white hover:text-void",
  outline: "bg-transparent text-white border-white shadow-[4px_4px_0px_#fff] hover:bg-white hover:text-void",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-4 py-2 text-xs",
  md: "px-6 py-3 text-sm",
  lg: "px-8 py-4 text-base",
};

/**
 * SENTINEL Brutal Button
 * Aggressive, high-contrast button with spring animations
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = "default",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <motion.button
        ref={ref}
        className={cn(
          "relative inline-flex items-center justify-center gap-2",
          "font-heading font-bold uppercase tracking-wider",
          "border-4 cursor-pointer",
          "transition-all duration-100",
          "hover:translate-x-[-2px] hover:translate-y-[-2px]",
          "active:translate-x-[2px] active:translate-y-[2px]",
          "active:shadow-[2px_2px_0px_currentColor]",
          "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-x-0 disabled:hover:translate-y-0",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        disabled={disabled || isLoading}
        whileTap={{ scale: 0.98 }}
        {...props}
      >
        {isLoading && (
          <Loader2 className="w-4 h-4 animate-spin" />
        )}
        {!isLoading && leftIcon}
        {children}
        {!isLoading && rightIcon}
      </motion.button>
    );
  }
);

Button.displayName = "Button";

/**
 * Icon-only brutal button
 */
interface IconButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  icon: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  "aria-label": string;
}

const iconSizeStyles: Record<ButtonSize, string> = {
  sm: "w-8 h-8",
  md: "w-10 h-10",
  lg: "w-12 h-12",
};

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      icon,
      variant = "default",
      size = "md",
      className,
      ...props
    },
    ref
  ) => {
    return (
      <motion.button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center",
          "border-4 cursor-pointer",
          "transition-all duration-100",
          "hover:translate-x-[-2px] hover:translate-y-[-2px]",
          "active:translate-x-[2px] active:translate-y-[2px]",
          variantStyles[variant],
          iconSizeStyles[size],
          className
        )}
        whileTap={{ scale: 0.95 }}
        {...props}
      >
        {icon}
      </motion.button>
    );
  }
);

IconButton.displayName = "IconButton";

export default Button;
