"use client";

import { forwardRef } from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

type CardVariant = "default" | "cyan" | "crimson" | "amber" | "green";

interface CardProps extends HTMLMotionProps<"div"> {
  variant?: CardVariant;
  hover?: boolean;
  glow?: boolean;
}

const variantStyles: Record<CardVariant, string> = {
  default: "border-white shadow-[4px_4px_0px_#fff]",
  cyan: "border-cyber-cyan shadow-[4px_4px_0px_#00E5FF]",
  crimson: "border-neon-crimson shadow-[4px_4px_0px_#FF003C]",
  amber: "border-warning-amber shadow-[4px_4px_0px_#FFB800]",
  green: "border-terminal-green shadow-[4px_4px_0px_#39FF14]",
};

const glowStyles: Record<CardVariant, string> = {
  default: "",
  cyan: "shadow-[4px_4px_0px_#00E5FF,0_0_30px_rgba(0,229,255,0.2)]",
  crimson: "shadow-[4px_4px_0px_#FF003C,0_0_30px_rgba(255,0,60,0.2)]",
  amber: "shadow-[4px_4px_0px_#FFB800,0_0_30px_rgba(255,184,0,0.2)]",
  green: "shadow-[4px_4px_0px_#39FF14,0_0_30px_rgba(57,255,20,0.2)]",
};

/**
 * SENTINEL Brutal Card
 * Container with hard shadows and cyber styling
 */
export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = "default", hover = false, glow = false, className, children, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={cn(
          "bg-carbon border-4 p-6",
          variantStyles[variant],
          glow && glowStyles[variant],
          hover && [
            "transition-all duration-150",
            "hover:translate-x-[-2px] hover:translate-y-[-2px]",
            "hover:shadow-[8px_8px_0px_currentColor]",
          ],
          className
        )}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = "Card";

/**
 * Card Header
 */
interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function CardHeader({ children, className }: CardHeaderProps) {
  return (
    <div className={cn("mb-4 pb-4 border-b-2 border-graphite", className)}>
      {children}
    </div>
  );
}

/**
 * Card Title
 */
interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

export function CardTitle({ children, className }: CardTitleProps) {
  return (
    <h3 className={cn("font-heading text-xl font-bold uppercase tracking-tight text-white", className)}>
      {children}
    </h3>
  );
}

/**
 * Card Description
 */
interface CardDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export function CardDescription({ children, className }: CardDescriptionProps) {
  return (
    <p className={cn("font-mono text-sm text-steel mt-1", className)}>
      {children}
    </p>
  );
}

/**
 * Card Content
 */
interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export function CardContent({ children, className }: CardContentProps) {
  return <div className={cn("", className)}>{children}</div>;
}

/**
 * Card Footer
 */
interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function CardFooter({ children, className }: CardFooterProps) {
  return (
    <div className={cn("mt-4 pt-4 border-t-2 border-graphite flex items-center gap-4", className)}>
      {children}
    </div>
  );
}

export default Card;
