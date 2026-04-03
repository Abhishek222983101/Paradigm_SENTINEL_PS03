"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { 
  Shield, 
  Activity, 
  Zap, 
  Search, 
  Network,
  Menu,
  X,
  ExternalLink
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: <Activity className="w-4 h-4" /> },
  { label: "Simulator", href: "/simulator", icon: <Zap className="w-4 h-4" /> },
  { label: "Investigation", href: "/investigation", icon: <Search className="w-4 h-4" /> },
  { label: "Graph", href: "/graph", icon: <Network className="w-4 h-4" /> },
];

/**
 * SENTINEL Floating Header
 * Cyber-brutalist navigation with aggressive styling
 * Transforms on scroll with smooth transitions
 */
export function FloatingHeader() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <>
      <motion.header
        className={cn(
          "fixed top-0 left-0 right-0 z-50",
          "transition-all duration-300"
        )}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        <div
          className={cn(
            "mx-auto transition-all duration-300",
            isScrolled
              ? "max-w-5xl mt-4 mx-4 md:mx-auto"
              : "max-w-full"
          )}
        >
          <div
            className={cn(
              "flex items-center justify-between px-6 py-4",
              "transition-all duration-300",
              isScrolled
                ? "bg-carbon/95 backdrop-blur-md border-4 border-white shadow-[4px_4px_0px_#fff]"
                : "bg-void/80 backdrop-blur-sm border-b-2 border-graphite"
            )}
          >
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 group">
              <motion.div
                className={cn(
                  "flex items-center justify-center w-10 h-10",
                  "bg-cyber-cyan border-2 border-white",
                  "shadow-[2px_2px_0px_#fff]",
                  "group-hover:shadow-[4px_4px_0px_#00E5FF]",
                  "group-hover:translate-x-[-1px] group-hover:translate-y-[-1px]",
                  "transition-all duration-150"
                )}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Shield className="w-6 h-6 text-void" />
              </motion.div>
              <span className="font-heading text-xl font-bold tracking-tight text-white">
                SENTINEL
              </span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-2">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2",
                    "font-mono text-sm uppercase tracking-wider",
                    "text-steel hover:text-white",
                    "border-2 border-transparent hover:border-white",
                    "hover:bg-graphite",
                    "transition-all duration-150"
                  )}
                >
                  {item.icon}
                  {item.label}
                </Link>
              ))}
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-4">
              {/* GitHub Link */}
              <a
                href="https://github.com/Abhishek222983101/Paradigm_SENTINEL_PS03"
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  "hidden sm:flex items-center gap-2 px-4 py-2",
                  "font-mono text-sm text-steel hover:text-white",
                  "border-2 border-graphite hover:border-white",
                  "transition-all duration-150"
                )}
              >
                <ExternalLink className="w-4 h-4" />
                <span>GitHub</span>
              </a>

              {/* Live Status Indicator */}
              <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-graphite border-2 border-terminal-green">
                <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse shadow-[0_0_8px_#39FF14]" />
                <span className="font-mono text-xs text-terminal-green uppercase">
                  Live
                </span>
              </div>

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className={cn(
                  "md:hidden flex items-center justify-center w-10 h-10",
                  "border-2 border-white",
                  "hover:bg-white hover:text-void",
                  "transition-all duration-150"
                )}
                aria-label="Toggle menu"
              >
                {isMobileMenuOpen ? (
                  <X className="w-5 h-5" />
                ) : (
                  <Menu className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            className="fixed inset-0 z-40 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {/* Backdrop */}
            <motion.div
              className="absolute inset-0 bg-void/95 backdrop-blur-md"
              onClick={() => setIsMobileMenuOpen(false)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />

            {/* Menu Content */}
            <motion.nav
              className="absolute top-20 left-4 right-4 bg-carbon border-4 border-white shadow-[8px_8px_0px_#fff] p-6"
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
            >
              <div className="flex flex-col gap-2">
                {navItems.map((item, index) => (
                  <motion.div
                    key={item.href}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Link
                      href={item.href}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={cn(
                        "flex items-center gap-3 px-4 py-3",
                        "font-mono text-lg uppercase tracking-wider",
                        "text-white hover:text-cyber-cyan",
                        "border-2 border-transparent hover:border-cyber-cyan",
                        "hover:bg-graphite",
                        "transition-all duration-150"
                      )}
                    >
                      {item.icon}
                      {item.label}
                    </Link>
                  </motion.div>
                ))}

                {/* GitHub in mobile menu */}
                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: navItems.length * 0.05 }}
                >
                  <a
                    href="https://github.com/Abhishek222983101/Paradigm_SENTINEL_PS03"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(
                      "flex items-center gap-3 px-4 py-3",
                      "font-mono text-lg uppercase tracking-wider",
                      "text-steel hover:text-white",
                      "border-2 border-transparent hover:border-white",
                      "hover:bg-graphite",
                      "transition-all duration-150"
                    )}
                  >
                    <ExternalLink className="w-5 h-5" />
                    GitHub
                  </a>
                </motion.div>
              </div>
            </motion.nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default FloatingHeader;
