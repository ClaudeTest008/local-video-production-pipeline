import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@lvpp/shared", "@lvpp/ui"],
  output: process.env.LVPP_DESKTOP ? "export" : undefined, // static export for the Tauri shell
};

export default nextConfig;
