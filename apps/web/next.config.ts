import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@lvpp/shared", "@lvpp/ui"],
  // Static export for the Tauri shell: explicit opt-in via LVPP_DESKTOP, or
  // automatic under `tauri build` (Tauri CLI sets TAURI_ENV_PLATFORM for hooks).
  output:
    process.env.LVPP_DESKTOP || process.env.TAURI_ENV_PLATFORM ? "export" : undefined,
};

export default nextConfig;
