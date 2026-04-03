"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { cn } from "@/lib/utils";

interface HeroShutterTextProps {
  text?: string;
  className?: string;
}

/**
 * SENTINEL Hero Shutter Text
 * Aggressive split-shutter reveal animation with cyber colors
 * Each letter splits and reveals with staggered timing
 */
export function HeroShutterText({ 
  text = "SENTINEL", 
  className 
}: HeroShutterTextProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  const letters = text.split("");
  
  // Cyber-brutalist color rotation
  const colors = [
    "text-cyber-cyan",      // Cyan
    "text-neon-crimson",    // Crimson
    "text-warning-amber",   // Amber
    "text-cyber-cyan",      // Cyan
    "text-terminal-green",  // Green
    "text-neon-crimson",    // Crimson
    "text-warning-amber",   // Amber
    "text-cyber-cyan",      // Cyan
  ];

  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  };

  const letterVariants = {
    hidden: {
      y: "100%",
      opacity: 0,
    },
    visible: {
      y: "0%",
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 500,
        damping: 30,
        mass: 1,
      },
    },
  };

  const shutterVariants = {
    hidden: {
      scaleY: 1,
    },
    visible: {
      scaleY: 0,
      transition: {
        duration: 0.4,
        ease: [0.65, 0, 0.35, 1],
        delay: 0.2,
      },
    },
  };

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <motion.div
        className="flex items-center justify-center gap-1 md:gap-2"
        variants={containerVariants}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        {letters.map((letter, index) => (
          <div key={index} className="relative overflow-hidden">
            {/* Main letter */}
            <motion.span
              className={cn(
                "inline-block font-heading text-6xl sm:text-8xl md:text-9xl lg:text-[12rem] xl:text-[14rem]",
                "font-extrabold tracking-tighter leading-none",
                colors[index % colors.length],
                "drop-shadow-[0_0_30px_currentColor]"
              )}
              variants={letterVariants}
              style={{
                textShadow: "0 0 40px currentColor, 0 0 80px currentColor",
              }}
            >
              {letter}
            </motion.span>

            {/* Shutter overlay */}
            <motion.div
              className="absolute inset-0 bg-void origin-top"
              variants={shutterVariants}
              initial="hidden"
              animate={isInView ? "visible" : "hidden"}
              style={{ transitionDelay: `${index * 0.03}s` }}
            />

            {/* Glitch slice effect */}
            <motion.div
              className={cn(
                "absolute inset-0 opacity-0",
                colors[(index + 1) % colors.length]
              )}
              animate={
                isInView
                  ? {
                      opacity: [0, 0.8, 0],
                      x: [0, -4, 4, 0],
                      transition: {
                        delay: 0.5 + index * 0.02,
                        duration: 0.15,
                        times: [0, 0.5, 0.75, 1],
                      },
                    }
                  : {}
              }
            >
              <span
                className={cn(
                  "inline-block font-heading text-6xl sm:text-8xl md:text-9xl lg:text-[12rem] xl:text-[14rem]",
                  "font-extrabold tracking-tighter leading-none"
                )}
              >
                {letter}
              </span>
            </motion.div>
          </div>
        ))}
      </motion.div>

      {/* Scanline effect */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        initial={{ opacity: 0 }}
        animate={isInView ? { opacity: 1 } : { opacity: 0 }}
        transition={{ delay: 0.8 }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyber-cyan/5 to-transparent h-[2px] animate-scan" />
      </motion.div>
    </div>
  );
}

// Animation for the scan effect
const scanKeyframes = `
@keyframes scan {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100vh); }
}
`;

// Inject the keyframes
if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = scanKeyframes;
  document.head.appendChild(style);
}

export default HeroShutterText;
