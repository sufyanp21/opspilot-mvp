import Dashboard from "./Dashboard";
import { useState } from "react";
import { postJson } from "@/lib/api";
import { setTokens, isAuthenticated } from "@/lib/auth";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { TrendingUp, Shield, Activity, FileText, CheckCircle, AlertTriangle } from "lucide-react";

const Index = () => {
  const [email, setEmail] = useState("trader@example.com");
  const [password, setPassword] = useState("demo");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(isAuthenticated());
  
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    
    try {
      const t = await postJson<{ access_token: string; refresh_token: string }>("/auth/login", { email, password });
      setTokens(t.access_token, t.refresh_token);
      setIsLoggedIn(true);
    } catch (err) {
      setError("Invalid credentials. Use 'demo' as password.");
    } finally {
      setIsLoading(false);
    }
  }

  if (isLoggedIn) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">OpsPilot Trading Operations</h1>
            <p className="text-muted-foreground">Real-time derivatives reconciliation & risk management</p>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span className="text-sm text-green-600 font-medium">System Operational</span>
          </div>
        </div>
        
        <Dashboard />
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link to="/upload" className="group">
            <Card className="transition-all hover:shadow-md group-hover:border-blue-300">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-base">Data Ingestion</CardTitle>
                </div>
                <CardDescription>Upload trade files & positions</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          
          <Link to="/reconciliation" className="group">
            <Card className="transition-all hover:shadow-md group-hover:border-green-300">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  <CardTitle className="text-base">Reconciliation</CardTitle>
                </div>
                <CardDescription>ETD & OTC trade matching</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          
          <Link to="/exceptions" className="group">
            <Card className="transition-all hover:shadow-md group-hover:border-orange-300">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                  <CardTitle className="text-base">Exceptions</CardTitle>
                </div>
                <CardDescription>Break management & resolution</CardDescription>
              </CardHeader>
            </Card>
          </Link>
          
          <Link to="/audit" className="group">
            <Card className="transition-all hover:shadow-md group-hover:border-purple-300">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-purple-600" />
                  <CardTitle className="text-base">Audit Trail</CardTitle>
                </div>
                <CardDescription>Regulatory reporting & logs</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Activity className="h-8 w-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-slate-900">OpsPilot</h1>
          </div>
          <h2 className="text-lg font-semibold text-slate-700">Derivatives Operations Platform</h2>
          <p className="text-sm text-slate-600">Secure access to trading reconciliation & risk management</p>
        </div>

        <Card className="border-slate-200 shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">Sign In</CardTitle>
            <CardDescription>Enter your credentials to access the platform</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
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
            
            <div className="mt-4 text-center">
              <div className="text-xs text-slate-500 space-y-1">
                <p><strong>Demo Credentials:</strong></p>
                <p>Any email + password: <code className="bg-slate-100 px-1 rounded">demo</code></p>
                <p>Admin access: email ending with <code className="bg-slate-100 px-1 rounded">+admin@</code></p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Index;
