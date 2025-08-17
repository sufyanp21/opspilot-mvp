import React from "react";

const COMMIT_SHA = (import.meta.env.VITE_GIT_SHA as string) || "dev-local";
const APP_NAME = (import.meta.env.VITE_APP_NAME as string) || "OpsPilot Vite";
const BUILD_TIME = (import.meta.env.VITE_BUILD_TIME as string) || new Date().toISOString();
const NONCE = Math.random().toString(36).slice(2, 8);

export function BuildBeacon() {
  const isProd = import.meta.env.PROD;
  return (
    <footer
      style={{
        position: "fixed",
        bottom: 8,
        right: 12,
        fontSize: isProd ? 11 : 13,
        opacity: isProd ? 0.7 : 1,
        background: isProd ? "rgba(59, 130, 246, 0.8)" : "rgba(16, 185, 129, 0.9)",
        color: "white",
        padding: "4px 8px",
        borderRadius: 8,
        zIndex: 9999,
        pointerEvents: "none",
        userSelect: "none",
        fontWeight: "500",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        border: "1px solid rgba(255,255,255,0.2)",
      }}
      data-app-name={APP_NAME}
      data-git-sha={COMMIT_SHA}
      data-build-time={BUILD_TIME}
      data-nonce={NONCE}
      aria-label="build-beacon"
    >
      🚀 NEW UI · {APP_NAME} · {COMMIT_SHA.slice(0, 7)} · {NONCE}
    </footer>
  );
}

export default BuildBeacon;


