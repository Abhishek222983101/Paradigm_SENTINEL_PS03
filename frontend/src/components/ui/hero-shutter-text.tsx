"use client";

import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { RefreshCw } from "lucide-react";

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
  const [animationKey, setAnimationKey] = useState(0);

  const letters = text.split("");

  const handleReplay = () => {
    setAnimationKey(prev => prev + 1);
  };

  return (
    <div ref={containerRef} className={cn("relative flex flex-col sm:flex-row items-center justify-center py-4", className)}>
      <motion.div
        key={animationKey}
        className="flex select-none relative"
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
            className="relative font-heading text-6xl sm:text-8xl md:text-[8rem] lg:text-[11rem] font-black leading-none uppercase tracking-tighter mx-[-2px] md:mx-[-4px]"
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
            <motion.span 
              className="text-transparent absolute inset-0"
              style={{
                WebkitTextStroke: "2px rgba(255, 255, 255, 0.15)",
              }}
              animate={{
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                delay: index * 0.2,
                ease: "easeInOut"
              }}
            >
              {letter}
            </motion.span>

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

        {/* Replay Animation Button */}
        <motion.button
          onClick={handleReplay}
          className="absolute -right-8 sm:-right-12 md:-right-16 top-1/2 -translate-y-1/2 p-2 border-2 border-graphite text-steel hover:text-cyber-cyan hover:border-cyber-cyan hover:bg-cyber-cyan/10 transition-colors z-30 group"
          title="Re-initialize System"
          variants={{
            hidden: { opacity: 0, scale: 0.5 },
            visible: { 
              opacity: 1, 
              scale: 1,
              transition: { delay: 1.5, type: "spring" }
            }
          }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <RefreshCw className="w-4 h-4 md:w-5 md:h-5 group-hover:animate-spin" />
        </motion.button>
      </motion.div>

      {/* Cyber scanning line that sweeps across the text once */}
      <motion.div
        key={`scan-${animationKey}`}
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
