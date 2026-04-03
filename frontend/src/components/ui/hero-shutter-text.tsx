"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { cn } from "@/lib/utils";

interface HeroShutterTextProps {
  text?: string;
  className?: string;
}

/**
 * SENTINEL Hero Shutter Text - Redesigned for pure Cyber-Brutalism
 * Avoids messy glowing boxes (AI slop) in favor of harsh, sharp, 
 * high-contrast typography with glitch offsets and stroke outlines.
 */
export function HeroShutterText({ 
  text = "SENTINEL", 
  className 
}: HeroShutterTextProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  const letters = text.split("");

  return (
    <div ref={containerRef} className={cn("relative flex justify-center py-4", className)}>
      <motion.div
        className="flex select-none"
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
        variants={{
          hidden: {},
          visible: {
            transition: {
              staggerChildren: 0.1,
            },
          },
        }}
      >
        {letters.map((letter, index) => (
          <motion.div
            key={index}
            className="relative font-heading text-7xl sm:text-9xl md:text-[10rem] lg:text-[14rem] font-black leading-none uppercase tracking-tighter mx-[-2px] md:mx-[-4px]"
            variants={{
              hidden: { opacity: 0, y: 40 },
              visible: { 
                opacity: 1, 
                y: 0, 
                transition: { type: "spring", stiffness: 400, damping: 25 }
              }
            }}
          >
            {/* Background Layer: Dimmed Outlined Text */}
            <span 
              className="text-transparent absolute inset-0"
              style={{
                WebkitTextStroke: "2px rgba(255, 255, 255, 0.15)",
              }}
            >
              {letter}
            </span>

            {/* Glitch Layer 1: Crimson */}
            <motion.span 
              className="text-transparent absolute inset-0"
              style={{
                WebkitTextStroke: "2px var(--color-neon-crimson)",
                textShadow: "0 0 15px rgba(255,0,60,0.3)"
              }}
              variants={{
                hidden: { x: 0, y: 0, opacity: 0 },
                visible: { 
                  x: [-4, 4, -2, 0], 
                  y: [2, -2, 1, 0],
                  opacity: [0, 1, 0.5, 0],
                  transition: { 
                    duration: 0.3, 
                    delay: 0.4 + index * 0.1,
                    times: [0, 0.3, 0.6, 1]
                  }
                }
              }}
            >
              {letter}
            </motion.span>

            {/* Glitch Layer 2: Cyber Cyan */}
            <motion.span 
              className="text-transparent absolute inset-0"
              style={{
                WebkitTextStroke: "2px var(--color-cyber-cyan)",
                textShadow: "0 0 15px rgba(0,229,255,0.3)"
              }}
              variants={{
                hidden: { x: 0, y: 0, opacity: 0 },
                visible: { 
                  x: [4, -4, 2, 0], 
                  y: [-2, 2, -1, 0],
                  opacity: [0, 1, 0.5, 0],
                  transition: { 
                    duration: 0.3, 
                    delay: 0.45 + index * 0.1,
                    times: [0, 0.3, 0.6, 1]
                  }
                }
              }}
            >
              {letter}
            </motion.span>

            {/* Foreground Layer: Solid White with Shutter Reveal */}
            <motion.span
              className="text-white relative z-10 block"
              variants={{
                hidden: { clipPath: "polygon(0 0, 100% 0, 100% 0, 0 0)" },
                visible: { 
                  clipPath: "polygon(0 0, 100% 0, 100% 100%, 0 100%)",
                  transition: { duration: 0.6, delay: 0.2 + index * 0.1, ease: [0.76, 0, 0.24, 1] }
                }
              }}
            >
              {letter}
            </motion.span>
          </motion.div>
        ))}
      </motion.div>

      {/* Cyber scanning line that sweeps across the text once */}
      <motion.div
        className="absolute top-0 bottom-0 w-[4px] bg-white z-20 mix-blend-difference"
        style={{
          boxShadow: "0 0 20px var(--color-cyber-cyan), 0 0 40px var(--color-cyber-cyan)"
        }}
        initial={{ left: "0%", opacity: 0 }}
        animate={isInView ? { 
          left: ["0%", "100%"], 
          opacity: [0, 1, 1, 0] 
        } : {}}
        transition={{ 
          duration: 1.5, 
          delay: 0.5,
          ease: "easeInOut",
          times: [0, 0.1, 0.9, 1]
        }}
      />
    </div>
  );
}

export default HeroShutterText;
