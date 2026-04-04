"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
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
 * Refined navigation with smooth transitions
 */
export function FloatingHeader() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const isActive = (href: string) => pathname === href;

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
                ? "bg-[var(--bg-surface)]/95 backdrop-blur-md border border-[var(--border-default)] rounded-xl shadow-[var(--shadow-lg)]"
                : "bg-[var(--bg-base)]/80 backdrop-blur-sm border-b border-[var(--border-subtle)]"
            )}
          >
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 group">
              <motion.div
                className={cn(
                  "flex items-center justify-center w-10 h-10 rounded-lg",
                  "bg-[var(--accent-primary)] shadow-[0_0_16px_var(--accent-primary-glow)]",
                  "group-hover:shadow-[0_0_24px_var(--accent-primary-glow)]",
                  "transition-all duration-200"
                )}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Shield className="w-5 h-5 text-[var(--bg-base)]" />
              </motion.div>
              <span className="font-heading text-xl font-semibold tracking-tight text-[var(--text-primary)]">
                SENTINEL
              </span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg",
                    "font-medium text-sm",
                    "transition-all duration-150",
                    isActive(item.href)
                      ? "text-[var(--accent-primary)] bg-[var(--accent-primary-glow)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-overlay)]"
                  )}
                >
                  {item.icon}
                  {item.label}
                </Link>
              ))}
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-3">
              {/* GitHub Link */}
              <a
                href="https://github.com/Abhishek222983101/Paradigm_SENTINEL_PS03"
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  "hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg",
                  "text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]",
                  "border border-[var(--border-default)] hover:border-[var(--border-strong)]",
                  "hover:bg-[var(--bg-overlay)]",
                  "transition-all duration-150"
                )}
              >
                <ExternalLink className="w-4 h-4" />
                <span>GitHub</span>
              </a>

              {/* Live Status Indicator */}
              <div className="hidden sm:flex status-badge live">
                <span className="status-dot live" />
                Live
              </div>

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className={cn(
                  "md:hidden flex items-center justify-center w-10 h-10 rounded-lg",
                  "border border-[var(--border-default)]",
                  "text-[var(--text-secondary)] hover:text-[var(--text-primary)]",
                  "hover:bg-[var(--bg-overlay)]",
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
              className="absolute inset-0 bg-[var(--bg-base)]/95 backdrop-blur-md"
              onClick={() => setIsMobileMenuOpen(false)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />

            {/* Menu Content */}
            <motion.nav
              className="absolute top-20 left-4 right-4 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl shadow-[var(--shadow-lg)] p-4"
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
            >
              <div className="flex flex-col gap-1">
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
                        "flex items-center gap-3 px-4 py-3 rounded-lg",
                        "text-base font-medium",
                        "transition-all duration-150",
                        isActive(item.href)
                          ? "text-[var(--accent-primary)] bg-[var(--accent-primary-glow)]"
                          : "text-[var(--text-primary)] hover:text-[var(--accent-primary)] hover:bg-[var(--bg-overlay)]"
                      )}
                    >
                      {item.icon}
                      {item.label}
                    </Link>
                  </motion.div>
                ))}

                {/* Divider */}
                <div className="my-2 border-t border-[var(--border-subtle)]" />

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
                      "flex items-center gap-3 px-4 py-3 rounded-lg",
                      "text-base font-medium",
                      "text-[var(--text-muted)] hover:text-[var(--text-primary)]",
                      "hover:bg-[var(--bg-overlay)]",
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
