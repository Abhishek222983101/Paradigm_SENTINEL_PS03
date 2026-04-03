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
    color: "cyan" as const,
    stats: "2.3K TXN/MIN",
  },
  {
    title: "Attack Simulator",
    description: "Inject fraud scenarios and watch the system respond in real-time",
    href: "/simulator",
    icon: Zap,
    color: "amber" as const,
    stats: "5 SCENARIOS",
  },
  {
    title: "Investigation Hub",
    description: "AI-powered case analysis with SHAP explainability",
    href: "/investigation",
    icon: Search,
    color: "crimson" as const,
    stats: "MISTRAL 7B",
  },
  {
    title: "Fraud Network",
    description: "Interactive graph visualization of fraud rings and connections",
    href: "/graph",
    icon: Network,
    color: "green" as const,
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

export default function HomePage() {
  return (
    <div className="min-h-screen bg-void">
      <FloatingHeader />
      
      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
        {/* Background Grid */}
        <GridAnimation className="opacity-50" />
        
        {/* Dot pattern overlay */}
        <div className="absolute inset-0 bg-dot-pattern opacity-30" />
        
        {/* Content */}
        <div className="relative z-10 container-brutal text-center">
          {/* Alert badge */}
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 mb-8 bg-carbon border-2 border-cyber-cyan"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
            <span className="font-mono text-xs text-cyber-cyan uppercase tracking-wider">
              HackTheCore PS03 — Financial Fraud Detection
            </span>
          </motion.div>

          {/* Main title with shutter effect */}
          <HeroShutterText text="SENTINEL" className="mb-6" />

          {/* Subtitle */}
          <motion.p
            className="font-heading text-2xl md:text-4xl font-bold text-white uppercase tracking-tight mb-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            Financial Fraud Intelligence
          </motion.p>

          {/* Description */}
          <motion.p
            className="font-mono text-steel text-sm md:text-base max-w-2xl mx-auto mb-12"
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
            <div className="w-6 h-10 border-2 border-white rounded-full flex justify-center pt-2">
              <div className="w-1 h-2 bg-cyber-cyan rounded-full" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* Modules Section */}
      <section className="relative py-24 bg-abyss">
        <div className="container-brutal">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-heading text-4xl md:text-6xl font-bold text-white uppercase tracking-tight mb-4">
              Command Center
            </h2>
            <p className="font-mono text-steel text-sm max-w-xl mx-auto">
              Four integrated modules for complete fraud intelligence
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {modules.map((module, index) => (
              <motion.div
                key={module.title}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Link href={module.href}>
                  <Card
                    variant={module.color}
                    hover
                    className="h-full group cursor-pointer"
                  >
                    <CardHeader className="flex flex-row items-start justify-between">
                      <div>
                        <CardTitle className="flex items-center gap-3">
                          <module.icon className={cn(
                            "w-6 h-6",
                            module.color === "cyan" && "text-cyber-cyan",
                            module.color === "crimson" && "text-neon-crimson",
                            module.color === "amber" && "text-warning-amber",
                            module.color === "green" && "text-terminal-green",
                          )} />
                          {module.title}
                        </CardTitle>
                        <CardDescription>{module.description}</CardDescription>
                      </div>
                      <div className={cn(
                        "px-3 py-1 font-mono text-xs border-2",
                        module.color === "cyan" && "border-cyber-cyan text-cyber-cyan",
                        module.color === "crimson" && "border-neon-crimson text-neon-crimson",
                        module.color === "amber" && "border-warning-amber text-warning-amber",
                        module.color === "green" && "border-terminal-green text-terminal-green",
                      )}>
                        {module.stats}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-2 text-steel group-hover:text-white transition-colors">
                        <span className="font-mono text-sm">Enter Module</span>
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-24 bg-void">
        <div className="absolute inset-0 bg-grid-pattern opacity-20" />
        <div className="container-brutal relative z-10">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-heading text-4xl md:text-6xl font-bold text-white uppercase tracking-tight mb-4">
              The Detection Engine
            </h2>
            <p className="font-mono text-steel text-sm max-w-xl mx-auto">
              Multi-modal AI that catches what rules-based systems miss
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="bg-carbon border-4 border-graphite p-6 hover:border-cyber-cyan transition-colors"
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <feature.icon className="w-10 h-10 text-cyber-cyan mb-4" />
                <h3 className="font-heading text-lg font-bold text-white uppercase mb-2">
                  {feature.title}
                </h3>
                <p className="font-mono text-sm text-steel">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Metrics Section */}
      <section className="relative py-24 bg-abyss">
        <div className="container-brutal">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-heading text-4xl md:text-6xl font-bold text-white uppercase tracking-tight mb-4">
              Performance Metrics
            </h2>
            <p className="font-mono text-steel text-sm max-w-xl mx-auto">
              Real-time system performance indicators
            </p>
          </motion.div>

          <MetricsGrid metrics={defaultFraudMetrics} />
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="relative py-24 bg-void border-t-4 border-graphite">
        <div className="container-brutal">
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-heading text-2xl md:text-3xl font-bold text-white uppercase tracking-tight mb-4">
              Technology Stack
            </h2>
          </motion.div>

          <motion.div
            className="flex flex-wrap justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            {techStack.map((tech, index) => (
              <motion.div
                key={tech.name}
                className="px-4 py-2 bg-carbon border-2 border-graphite hover:border-cyber-cyan transition-colors"
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
              >
                <span className="font-mono text-sm text-white">{tech.name}</span>
                <span className="ml-2 font-mono text-xs text-steel">({tech.category})</span>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Bottom CTA Section */}
      <section className="relative py-32 overflow-hidden">
        <GridAnimation className="opacity-30" />
        <div className="container-brutal relative z-10 text-center">
          <motion.h2
            className="font-heading text-5xl md:text-7xl lg:text-8xl font-bold text-white uppercase tracking-tight mb-8"
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{
              textShadow: "0 0 40px rgba(255,0,60,0.5)",
            }}
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
      <footer className="bg-carbon border-t-4 border-graphite py-8">
        <div className="container-brutal">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 bg-cyber-cyan">
                <Shield className="w-5 h-5 text-void" />
              </div>
              <span className="font-heading text-lg font-bold text-white">SENTINEL</span>
            </div>
            
            <div className="font-mono text-xs text-steel text-center">
              Team Paradigm — HackTheCore PS03 — Financial Fraud Detection
            </div>
            
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
              <span className="font-mono text-xs text-terminal-green">SYSTEM ACTIVE</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
