import { useState } from "react";
import { useApp } from "@/lib/store";
import client from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Activity, AlertTriangle } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("trader@example.com");
  const [password, setPassword] = useState("demo");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setUser } = useApp();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const { data } = await client.post("/auth/login", { email, password });
      localStorage.setItem("opspilot_access", data.access_token);
      localStorage.setItem("user_email", email); // Store for ProtectedRoute
      if (data.refresh_token) {
        localStorage.setItem("opspilot_refresh", data.refresh_token);
      }
      
      // Extract user info from response or token
      const userRole = email.includes("+admin@") ? "admin" : "analyst";
      setUser({ email, role: userRole });
      
      // Use React Router navigation instead of window.location
      setTimeout(() => {
        window.location.href = "/";
      }, 100);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed. Please check your credentials.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-3">
          <div className="flex items-center justify-center gap-3 mb-6">
            <Activity className="h-10 w-10 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-slate-900">OpsPilot</h1>
              <p className="text-sm text-slate-600">Derivatives Operations Platform</p>
            </div>
          </div>
          <h2 className="text-xl font-semibold text-slate-700">Secure Trading Operations Access</h2>
          <p className="text-sm text-slate-600">
            Real-time reconciliation & risk management for institutional derivatives
          </p>
        </div>

        <Card className="border-slate-200 shadow-xl">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access the platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="trader@company.com"
                  className="w-full"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full"
                  required
                />
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button 
                type="submit" 
                className="w-full bg-blue-600 hover:bg-blue-700"
                disabled={isLoading}
              >
                {isLoading ? "Signing in..." : "Sign In"}
              </Button>
            </form>
            
            <div className="mt-6 text-center">
              <div className="text-xs text-slate-500 space-y-2 bg-slate-50 p-3 rounded">
                <p className="font-medium text-slate-700">Demo Credentials:</p>
                <p>Any email + password: <code className="bg-white px-1 rounded">demo</code></p>
                <p>Admin access: email ending with <code className="bg-white px-1 rounded">+admin@company.com</code></p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
