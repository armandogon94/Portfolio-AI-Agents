import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produce a standalone build so the prod Dockerfile can copy a minimal
  // runtime image from .next/standalone (slice-20a, DEC-26).
  output: "standalone",
};

export default nextConfig;
