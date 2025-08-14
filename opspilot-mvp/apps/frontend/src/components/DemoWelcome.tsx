import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import DemoMode, { DEMO_CONFIG, DemoNotifications } from '@/lib/demo';

interface DemoWelcomeProps {
  onDismiss?: () => void;
}

export default function DemoWelcome({ onDismiss }: DemoWelcomeProps) {
  const [currentTip, setCurrentTip] = useState(0);
  const [showWelcome, setShowWelcome] = useState(true);

  useEffect(() => {
    // Rotate tips every 5 seconds
    const interval = setInterval(() => {
      setCurrentTip(prev => (prev + 1) % DEMO_CONFIG.tips.length);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleDismiss = () => {
    setShowWelcome(false);
    onDismiss?.();
  };

  const handleStartTour = () => {
    // TODO: Implement tour functionality
    console.log('Starting demo tour...');
    handleDismiss();
  };

  if (!DemoMode.isEnabled() || !showWelcome) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-2xl w-full">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-3xl">🎯</span>
          </div>
          <CardTitle className="text-2xl">Welcome to OpsPilot MVP Demo!</CardTitle>
          <CardDescription className="text-lg">
            Explore derivatives data automation with realistic sample data
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Demo Scenarios */}
          <div>
            <h3 className="font-semibold mb-3">🚀 Demo Scenarios</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {DEMO_CONFIG.scenarios.map((scenario) => (
                <div key={scenario.id} className="p-3 border rounded-lg">
                  <h4 className="font-medium text-sm">{scenario.name}</h4>
                  <p className="text-xs text-gray-600 mt-1">{scenario.description}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {scenario.features.map((feature) => (
                      <Badge key={feature} variant="secondary" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Current Tip */}
          <Alert>
            <AlertDescription>
              <strong>Demo Tip:</strong> {DEMO_CONFIG.tips[currentTip]}
            </AlertDescription>
          </Alert>

          {/* Sample Metrics Preview */}
          <div>
            <h3 className="font-semibold mb-3">📊 Sample Data Overview</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
              <div className="p-2 bg-blue-50 rounded">
                <div className="text-lg font-bold text-blue-600">
                  {DEMO_CONFIG.sampleMetrics.totalTrades.toLocaleString()}
                </div>
                <div className="text-xs text-gray-600">Total Trades</div>
              </div>
              <div className="p-2 bg-green-50 rounded">
                <div className="text-lg font-bold text-green-600">
                  {DEMO_CONFIG.sampleMetrics.exceptions}
                </div>
                <div className="text-xs text-gray-600">Exceptions</div>
              </div>
              <div className="p-2 bg-purple-50 rounded">
                <div className="text-lg font-bold text-purple-600">
                  {DEMO_CONFIG.sampleMetrics.clusters}
                </div>
                <div className="text-xs text-gray-600">Clusters</div>
              </div>
              <div className="p-2 bg-orange-50 rounded">
                <div className="text-lg font-bold text-orange-600">
                  {DEMO_CONFIG.sampleMetrics.spanSnapshots}
                </div>
                <div className="text-xs text-gray-600">SPAN Records</div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <Button onClick={handleStartTour} className="flex-1">
              🎯 Start Guided Tour
            </Button>
            <Button onClick={handleDismiss} variant="outline" className="flex-1">
              🚀 Explore Freely
            </Button>
          </div>

          {/* Footer */}
          <div className="text-center text-xs text-gray-500 pt-2 border-t">
            💡 This is a demonstration with sample data. 
            <Button 
              variant="link" 
              className="text-xs p-0 h-auto ml-1"
              onClick={() => DemoMode.disable()}
            >
              Exit Demo Mode
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
