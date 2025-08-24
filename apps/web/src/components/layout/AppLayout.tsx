import { NavLink, useLocation } from "react-router-dom";
import { useMemo } from "react";
import { Gauge, UploadCloud, GitCompare, AlertTriangle, Sigma, FileCog, ScrollText } from "lucide-react";
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { isAuthenticated, clearTokens } from "@/lib/auth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const items = useMemo(() => [
    { title: "Dashboard", url: "/", icon: Gauge },
    { title: "File Upload", url: "/upload", icon: UploadCloud },
    { title: "Reconciliation", url: "/reconciliation", icon: GitCompare },
    { title: "Exceptions", url: "/exceptions", icon: AlertTriangle },
    { title: "SPAN Analysis", url: "/span", icon: Sigma },
    { title: "OTC Processing", url: "/otc", icon: FileCog },
    { title: "Audit Trail", url: "/audit", icon: ScrollText },
  ], []);

  const getNavCls = ({ isActive }: { isActive: boolean }) =>
    isActive ? "bg-muted text-primary font-medium" : "hover:bg-muted/50";

  return (
    <SidebarProvider>
      <header className="h-14 border-b flex items-center gap-3 px-3">
        <SidebarTrigger />
        <div className="flex-1 flex items-center gap-2">
          <div className="h-6 w-1.5 rounded-full bg-primary" />
          <span className="font-semibold tracking-tight">DerivaClear</span>
          <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-medium">NEW UI</span>
        </div>
          <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="relative inline-flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full rounded-full bg-success opacity-75 pulse" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-success" />
            </span>
            <span>Operational</span>
            {isAuthenticated() ? (
              <button className="text-sm underline" onClick={clearTokens}>Logout</button>
            ) : null}
          </div>
          <ThemeToggle />
        </div>
      </header>

      <div className="flex min-h-screen w-full">
        <Sidebar collapsible="icon" className="">
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Navigation</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {items.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild>
                        <NavLink to={item.url} end className={getNavCls}>
                          <item.icon className="mr-2 h-4 w-4" />
                          <span>{item.title}</span>
                        </NavLink>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>

        <main className="flex-1 p-6 container animate-fade-in">
          {children}
        </main>
      </div>
    </SidebarProvider>
  );
}
