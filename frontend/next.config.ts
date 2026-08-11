import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://lyricsync-alb-698441018.eu-north-1.elb.amazonaws.com/api/:path*",
      },
    ];
  },
};

export default nextConfig;
