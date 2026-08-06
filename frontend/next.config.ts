import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The floating dev-tools badge has its own unrelated "Theme" preference
  // that only skins itself, which was getting confused with the app's own
  // theme toggle. Disabling it removes that ambiguity.
  devIndicators: false,
};

export default nextConfig;
