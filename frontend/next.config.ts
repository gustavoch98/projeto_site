import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  images: {
    // O componente <Image> só otimiza imagens de domínios liberados aqui
    remotePatterns: [
      { protocol: "https", hostname: "ddragon.leagueoflegends.com", pathname: "/cdn/**" },
      { protocol: "https", hostname: "raw.communitydragon.org", pathname: "/latest/**" },
    ],
  },
};

export default nextConfig;
