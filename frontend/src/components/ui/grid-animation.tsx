"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, useAnimation } from "framer-motion";
import { cn } from "@/lib/utils";

interface GridAnimationProps {
  className?: string;
  lineColor?: string;
  dotColor?: string;
  glowIntensity?: "low" | "medium" | "high";
}

interface Point {
  x: number;
  y: number;
}

/**
 * SENTINEL Grid Animation
 * Mouse-following glowing cyan grid lines on dark background
 * Creates a cybersecurity command center aesthetic
 */
export function GridAnimation({
  className,
  lineColor = "#00E5FF",
  dotColor = "#00E5FF",
  glowIntensity = "medium",
}: GridAnimationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const mousePos = useRef<Point>({ x: 0, y: 0 });
  const targetPos = useRef<Point>({ x: 0, y: 0 });
  const animationFrame = useRef<number | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const glowSettings = {
    low: { blur: 10, alpha: 0.3 },
    medium: { blur: 20, alpha: 0.5 },
    high: { blur: 30, alpha: 0.7 },
  };

  const glow = glowSettings[glowIntensity];
  const gridSize = 48;
  const influenceRadius = 200;

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    targetPos.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  }, []);

  const lerp = (start: number, end: number, factor: number) => {
    return start + (end - start) * factor;
  };

  const drawGrid = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const { width, height } = dimensions;
    if (width === 0 || height === 0) return;

    // Smooth mouse following
    mousePos.current.x = lerp(mousePos.current.x, targetPos.current.x, 0.1);
    mousePos.current.y = lerp(mousePos.current.y, targetPos.current.y, 0.1);

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw grid lines
    ctx.strokeStyle = "rgba(37, 37, 37, 0.8)";
    ctx.lineWidth = 1;

    // Vertical lines
    for (let x = 0; x <= width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    // Horizontal lines
    for (let y = 0; y <= height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Draw glowing lines near mouse
    const mx = mousePos.current.x;
    const my = mousePos.current.y;

    // Find nearest grid intersection
    const nearestX = Math.round(mx / gridSize) * gridSize;
    const nearestY = Math.round(my / gridSize) * gridSize;

    // Draw highlighted vertical line
    const distX = Math.abs(mx - nearestX);
    if (distX < influenceRadius) {
      const intensity = 1 - distX / influenceRadius;
      ctx.strokeStyle = lineColor;
      ctx.lineWidth = 2;
      ctx.globalAlpha = intensity * glow.alpha;
      ctx.shadowColor = lineColor;
      ctx.shadowBlur = glow.blur * intensity;

      ctx.beginPath();
      ctx.moveTo(nearestX, 0);
      ctx.lineTo(nearestX, height);
      ctx.stroke();

      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
    }

    // Draw highlighted horizontal line
    const distY = Math.abs(my - nearestY);
    if (distY < influenceRadius) {
      const intensity = 1 - distY / influenceRadius;
      ctx.strokeStyle = lineColor;
      ctx.lineWidth = 2;
      ctx.globalAlpha = intensity * glow.alpha;
      ctx.shadowColor = lineColor;
      ctx.shadowBlur = glow.blur * intensity;

      ctx.beginPath();
      ctx.moveTo(0, nearestY);
      ctx.lineTo(width, nearestY);
      ctx.stroke();

      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
    }

    // Draw dots at intersections near mouse
    for (let x = 0; x <= width; x += gridSize) {
      for (let y = 0; y <= height; y += gridSize) {
        const dist = Math.sqrt((x - mx) ** 2 + (y - my) ** 2);
        if (dist < influenceRadius) {
          const intensity = 1 - dist / influenceRadius;
          const size = 2 + intensity * 4;

          ctx.fillStyle = dotColor;
          ctx.globalAlpha = intensity * 0.8;
          ctx.shadowColor = dotColor;
          ctx.shadowBlur = glow.blur * intensity;

          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fill();

          ctx.shadowBlur = 0;
          ctx.globalAlpha = 1;
        }
      }
    }

    // Draw crosshair at mouse position
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.6;
    ctx.setLineDash([4, 4]);

    // Horizontal crosshair
    ctx.beginPath();
    ctx.moveTo(mx - 20, my);
    ctx.lineTo(mx + 20, my);
    ctx.stroke();

    // Vertical crosshair
    ctx.beginPath();
    ctx.moveTo(mx, my - 20);
    ctx.lineTo(mx, my + 20);
    ctx.stroke();

    ctx.setLineDash([]);
    ctx.globalAlpha = 1;

    // Draw center dot
    ctx.fillStyle = lineColor;
    ctx.shadowColor = lineColor;
    ctx.shadowBlur = 15;
    ctx.beginPath();
    ctx.arc(mx, my, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    animationFrame.current = requestAnimationFrame(drawGrid);
  }, [dimensions, lineColor, dotColor, glow]);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  useEffect(() => {
    if (dimensions.width > 0 && dimensions.height > 0) {
      // Initialize mouse position to center
      targetPos.current = {
        x: dimensions.width / 2,
        y: dimensions.height / 2,
      };
      mousePos.current = { ...targetPos.current };

      window.addEventListener("mousemove", handleMouseMove);
      animationFrame.current = requestAnimationFrame(drawGrid);

      return () => {
        window.removeEventListener("mousemove", handleMouseMove);
        if (animationFrame.current) {
          cancelAnimationFrame(animationFrame.current);
        }
      };
    }
  }, [dimensions, handleMouseMove, drawGrid]);

  return (
    <div
      ref={containerRef}
      className={cn("absolute inset-0 overflow-hidden", className)}
    >
      <canvas
        ref={canvasRef}
        width={dimensions.width}
        height={dimensions.height}
        className="absolute inset-0"
        style={{ background: "transparent" }}
      />
      
      {/* Corner accents */}
      <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-cyber-cyan opacity-50" />
      <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-cyber-cyan opacity-50" />
      <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-cyber-cyan opacity-50" />
      <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-cyber-cyan opacity-50" />
    </div>
  );
}

export default GridAnimation;
