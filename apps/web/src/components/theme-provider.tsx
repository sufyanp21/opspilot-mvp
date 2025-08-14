import { ThemeProvider as NextThemesProvider } from "next-themes";
import { PropsWithChildren } from "react";

export function ThemeProvider({ children, defaultTheme = "system" }: PropsWithChildren<{ defaultTheme?: string }>) {
  return (
    <NextThemesProvider attribute="class" defaultTheme={defaultTheme} enableSystem themes={["light", "dark"]}>
      {children}
    </NextThemesProvider>
  );
}
