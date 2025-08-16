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
        fontSize: isProd ? 10 : 12,
        opacity: isProd ? 0.45 : 0.9,
        background: "rgba(0,0,0,0.04)",
        color: "var(--muted-foreground, #555)",
        padding: "2px 6px",
        borderRadius: 6,
        zIndex: 9999,
        pointerEvents: "none",
        userSelect: "none",
      }}
      data-app-name={APP_NAME}
      data-git-sha={COMMIT_SHA}
      data-build-time={BUILD_TIME}
      data-nonce={NONCE}
      aria-label="build-beacon"
    >
      {APP_NAME} · {COMMIT_SHA.slice(0, 7)} · {BUILD_TIME} · {NONCE}
    </footer>
  );
}

export default BuildBeacon;


