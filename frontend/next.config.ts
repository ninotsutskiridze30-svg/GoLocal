import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Drei's Html portals currently manage their own React roots and are not Strict Mode cleanup-safe in development.
  reactStrictMode: false,
  /* config options here */
  experimental: {
    agentFeedback: true,
  },
  cacheComponents: true,
  partialPrefetching: true,
};

export default nextConfig;
