import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import { useApp } from "@/lib/store";
import client from "@/lib/api";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, setUser } = useApp();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const didCheckRef = useRef(false);

  useEffect(() => {
    if (didCheckRef.current) return; // ensure single execution
    didCheckRef.current = true;

    const checkAuth = async () => {
      console.log("Running auth check...");
      const token = localStorage.getItem("opspilot_access");

      if (!token) {
        console.log("No token found, user is not authenticated.");
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      console.log("Token found, verifying via /auth/me ...");
      try {
        // Use the new /auth/me endpoint to validate the token and get user info
        const { data } = await client.get("/auth/me");
        if (data && data.email) {
          console.log("Auth check successful, user is:", data.email);
          setUser({ email: data.email, role: data.roles.includes("admin") ? "admin" : "analyst" });
          setIsAuthenticated(true);
        } else {
          console.warn("Auth check returned invalid user data.");
          throw new Error("Invalid user data");
        }
      } catch (error) {
        console.error("Authentication check failed:", error);
        // Token is invalid or expired, clear it
        localStorage.removeItem("opspilot_access");
        localStorage.removeItem("opspilot_refresh");
        localStorage.removeItem("user_email");
        setUser(null);
        setIsAuthenticated(false);
      }

      setIsLoading(false);
    };

    checkAuth();
  }, [setUser]);

  if (isLoading) {
    console.log("Auth check in progress...");
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log("User is not authenticated, redirecting to login.");
    return <Navigate to="/login" replace />;
  }

  console.log("User is authenticated, rendering protected content.");
  return <>{children}</>;
}
