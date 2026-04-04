import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // API Proxy Rewrites
  // Routes /api/* requests to the FastAPI backend
  async rewrites() {
    return [
      // REST API routes
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
      // Health check
      {
        source: "/api/health",
        destination: "http://localhost:8000/api/v1/health",
      },
    ];
  },
  
  // WebSocket proxy is handled differently - 
  // WebSockets connect directly to ws://localhost:8000/ws/*
  
  // Experimental features for better performance
  experimental: {
    // Enable optimized package imports
    optimizePackageImports: ["lucide-react", "framer-motion", "recharts"],
  },
  
  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
};

export default nextConfig;
