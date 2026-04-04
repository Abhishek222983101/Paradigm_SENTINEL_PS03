"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { 
  Shield, 
  Activity, 
  Zap, 
  Search, 
  Network, 
  ArrowRight,
  Brain,
  Eye,
  Lock,
  Clock
} from "lucide-react";

import { FloatingHeader } from "@/components/layout/floating-header";
import { HeroShutterText } from "@/components/ui/hero-shutter-text";
import { GridAnimation } from "@/components/ui/grid-animation";
import { MetricsGrid, defaultFraudMetrics } from "@/components/ui/metrics-score-cards";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// Module cards for navigation
const modules = [
  {
    title: "Live Dashboard",
    description: "Real-time transaction monitoring with ML-powered risk assessment",
    href: "/dashboard",
    icon: Activity,
    color: "primary" as const,
    stats: "2.3K TXN/MIN",
  },
  {
    title: "Attack Simulator",
    description: "Inject fraud scenarios and watch the system respond in real-time",
    href: "/simulator",
    icon: Zap,
    color: "warning" as const,
    stats: "5 SCENARIOS",
  },
  {
    title: "Investigation Hub",
    description: "AI-powered case analysis with SHAP explainability",
    href: "/investigation",
    icon: Search,
    color: "danger" as const,
    stats: "MISTRAL 7B",
  },
  {
    title: "Fraud Network",
    description: "Interactive graph visualization of fraud rings and connections",
    href: "/graph",
    icon: Network,
    color: "success" as const,
    stats: "GNN POWERED",
  },
];

// Feature highlights
const features = [
  {
    icon: Brain,
    title: "Multi-Modal AI",
    description: "Tabular + Sequential + Graph neural networks fused for maximum accuracy",
  },
  {
    icon: Clock,
    title: "Sub-100ms Latency",
    description: "Real-time decisions before transactions complete",
  },
  {
    icon: Eye,
    title: "Explainable AI",
    description: "SHAP values and natural language reports for every decision",
  },
  {
    icon: Lock,
    title: "Adaptive Thresholds",
    description: "RL-based threshold optimization that learns from feedback",
  },
];

// Technology stack
const techStack = [
  { name: "PyTorch", category: "ML" },
  { name: "PyG (GNN)", category: "ML" },
  { name: "XGBoost", category: "ML" },
  { name: "Mistral 7B", category: "LLM" },
  { name: "FastAPI", category: "Backend" },
  { name: "Next.js 16", category: "Frontend" },
  { name: "WebSocket", category: "Real-time" },
  { name: "SHAP", category: "XAI" },
];

const getColorStyles = (color: string) => {
  const styles = {
    primary: {
      icon: "text-[var(--accent-primary)]",
      badge: "bg-[var(--accent-primary-glow)] text-[var(--accent-primary)] border-[var(--accent-primary)]/30",
      card: "hover:border-[var(--accent-primary)]/50",
    },
    warning: {
      icon: "text-[var(--accent-warning)]",
      badge: "bg-[var(--accent-warning-glow)] text-[var(--accent-warning)] border-[var(--accent-warning)]/30",
      card: "hover:border-[var(--accent-warning)]/50",
    },
    danger: {
      icon: "text-[var(--accent-danger)]",
      badge: "bg-[var(--accent-danger-glow)] text-[var(--accent-danger)] border-[var(--accent-danger)]/30",
      card: "hover:border-[var(--accent-danger)]/50",
    },
    success: {
      icon: "text-[var(--accent-success)]",
      badge: "bg-[var(--accent-success-glow)] text-[var(--accent-success)] border-[var(--accent-success)]/30",
      card: "hover:border-[var(--accent-success)]/50",
    },
  };
  return styles[color as keyof typeof styles] || styles.primary;
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[var(--bg-base)]">
      <FloatingHeader />
      
      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
        {/* Background Grid */}
        <GridAnimation className="opacity-30" />
        
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[var(--bg-base)]/50 to-[var(--bg-base)]" />
        
        {/* Content */}
        <div className="relative z-10 container-app text-center px-4">
          {/* Alert badge */}
          <motion.div
            className="inline-flex items-center gap-2.5 px-4 py-2 mb-8 rounded-full bg-[var(--bg-surface)] border border-[var(--border-default)]"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <span className="status-dot live" />
            <span className="font-mono text-xs text-[var(--accent-primary)] uppercase tracking-wider">
              HackTheCore PS03 — Financial Fraud Detection
            </span>
          </motion.div>

          {/* Main title with shutter effect */}
          <HeroShutterText text="SENTINEL" className="mb-6" />

          {/* Subtitle */}
          <motion.p
            className="font-heading text-2xl md:text-4xl font-semibold text-[var(--text-primary)] tracking-tight mb-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            Financial Fraud Intelligence
          </motion.p>

          {/* Description */}
          <motion.p
            className="text-[var(--text-secondary)] text-base md:text-lg max-w-2xl mx-auto mb-12 leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            Real-time multi-modal deep learning for transaction security.
            Detect fraud chains, identify synthetic identities, and visualize fraud networks
            with sub-100ms latency.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
          >
            <Link href="/dashboard">
              <Button variant="cyan" size="lg" rightIcon={<ArrowRight className="w-5 h-5" />}>
                Live Dashboard
              </Button>
            </Link>
            <Link href="/simulator">
              <Button variant="outline" size="lg" rightIcon={<Zap className="w-5 h-5" />}>
                Run Simulator
              </Button>
            </Link>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            className="absolute bottom-8 left-1/2 -translate-x-1/2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, y: [0, 10, 0] }}
            transition={{ delay: 1.2, y: { duration: 1.5, repeat: Infinity } }}
          >
            <div className="w-6 h-10 border-2 border-[var(--border-strong)] rounded-full flex justify-center pt-2">
              <div className="w-1 h-2 bg-[var(--accent-primary)] rounded-full" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* Modules Section */}
      <section className="relative py-24 bg-[var(--bg-elevated)]">
        <div className="container-app">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-heading text-3xl md:text-5xl font-semibold text-[var(--text-primary)] tracking-tight mb-4">
              Command Center
            </h2>
            <p className="text-[var(--text-secondary)] text-base max-w-xl mx-auto">
              Four integrated modules for complete fraud intelligence
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {modules.map((module, index) => {
              const colorStyles = getColorStyles(module.color);
              return (
                <motion.div
                  key={module.title}
                  initial={{ opacity: 0, y: 40 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link href={module.href}>
                    <Card
                      variant={module.color === "primary" ? "cyan" : module.color === "danger" ? "crimson" : module.color === "warning" ? "amber" : "green"}
                      hover
                      className={cn("h-full group cursor-pointer", colorStyles.card)}
                    >
                      <CardHeader className="flex flex-row items-start justify-between">
                        <div>
                          <CardTitle className="flex items-center gap-3">
                            <module.icon className={cn("w-5 h-5", colorStyles.icon)} />
                            {module.title}
                          </CardTitle>
                          <CardDescription>{module.description}</CardDescription>
                        </div>
                        <div className={cn(
                          "px-2.5 py-1 rounded-md font-mono text-xs border",
                          colorStyles.badge
                        )}>
                          {module.stats}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-2 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] transition-colors">
                          <span className="text-sm font-medium">Enter Module</span>
                          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-24 bg-[var(--bg-base)]">
        <div className="container-app relative z-10">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-heading text-3xl md:text-5xl font-semibold text-[var(--text-primary)] tracking-tight mb-4">
              The Detection Engine
            </h2>
            <p className="text-[var(--text-secondary)] text-base max-w-xl mx-auto">
              Multi-modal AI that catches what rules-based systems miss
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="card hover:border-[var(--accent-primary)]/30 transition-all"
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="p-2.5 w-fit rounded-lg bg-[var(--accent-primary-glow)] mb-4">
                  <feature.icon className="w-6 h-6 text-[var(--accent-primary)]" />
                </div>
                <h3 className="font-heading text-base font-semibold text-[var(--text-primary)] mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-[var(--text-muted)] leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Metrics Section */}
      <section className="relative py-24 bg-[var(--bg-elevated)]">
        <div className="container-app">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-heading text-3xl md:text-5xl font-semibold text-[var(--text-primary)] tracking-tight mb-4">
              Performance Metrics
            </h2>
            <p className="text-[var(--text-secondary)] text-base max-w-xl mx-auto">
              Real-time system performance indicators
            </p>
          </motion.div>

          <MetricsGrid metrics={defaultFraudMetrics} />
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="relative py-24 bg-[var(--bg-base)] border-t border-[var(--border-subtle)]">
        <div className="container-app">
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-heading text-2xl md:text-3xl font-semibold text-[var(--text-primary)] tracking-tight mb-4">
              Technology Stack
            </h2>
          </motion.div>

          <motion.div
            className="flex flex-wrap justify-center gap-3"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            {techStack.map((tech, index) => (
              <motion.div
                key={tech.name}
                className="px-4 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] hover:border-[var(--accent-primary)]/30 transition-colors"
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
              >
                <span className="font-mono text-sm text-[var(--text-primary)]">{tech.name}</span>
                <span className="ml-2 font-mono text-xs text-[var(--text-muted)]">({tech.category})</span>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Bottom CTA Section */}
      <section className="relative py-32 overflow-hidden">
        <GridAnimation className="opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-base)] via-transparent to-[var(--bg-base)]" />
        <div className="container-app relative z-10 text-center">
          <motion.h2
            className="font-heading text-4xl md:text-6xl lg:text-7xl font-semibold text-[var(--text-primary)] tracking-tight mb-8"
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            Stop Fraud Now
          </motion.h2>
          
          <motion.div
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            <Link href="/dashboard">
              <Button variant="crimson" size="lg" rightIcon={<Shield className="w-5 h-5" />}>
                Launch Platform
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[var(--bg-surface)] border-t border-[var(--border-default)] py-8">
        <div className="container-app">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--accent-primary)]">
                <Shield className="w-5 h-5 text-[var(--bg-base)]" />
              </div>
              <span className="font-heading text-lg font-semibold text-[var(--text-primary)]">SENTINEL</span>
            </div>
            
            <div className="text-sm text-[var(--text-muted)] text-center">
              Team Paradigm — HackTheCore PS03 — Financial Fraud Detection
            </div>
            
            <div className="status-badge live">
              <span className="status-dot live" />
              System Active
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
