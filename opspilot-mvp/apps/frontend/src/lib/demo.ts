/**
 * Demo mode configuration and utilities for OpsPilot MVP
 */

// Demo mode state
let isDemoMode = false;

// Demo configuration
export const DEMO_CONFIG = {
  // Demo data settings
  autoRefresh: true,
  refreshInterval: 30000, // 30 seconds
  
  // Demo notifications
  showWelcomeMessage: true,
  showFeatureTours: true,
  
  // Demo data
  sampleMetrics: {
    totalTrades: 1950,
    matchedTrades: 1897,
    exceptions: 53,
    clusters: 12,
    slaBreaches: 8,
    spanSnapshots: 500,
    marginUtilization: 78.5
  },
  
  // Demo scenarios
  scenarios: [
    {
      id: 'etd_recon',
      name: 'ETD Reconciliation',
      description: 'Trade matching with price and quantity breaks',
      features: ['reconciliation', 'exceptions', 'clustering']
    },
    {
      id: 'span_analysis',
      name: 'SPAN Margin Analysis',
      description: 'Margin requirement analysis and delta reporting',
      features: ['span', 'margins', 'deltas']
    },
    {
      id: 'otc_processing',
      name: 'OTC FpML Processing',
      description: 'FpML parsing and economic matching',
      features: ['otc', 'fpml', 'economics']
    },
    {
      id: 'audit_lineage',
      name: 'Audit & Lineage',
      description: 'Complete data traceability and audit trails',
      features: ['audit', 'lineage', 'compliance']
    }
  ],
  
  // Demo tips
  tips: [
    "💡 Click on any metric card to drill down into details",
    "🔍 Use filters to explore different data views",
    "📊 Hover over charts for detailed information",
    "🎯 Try the exception clustering feature",
    "📈 Check out the SPAN margin analysis",
    "🔗 Explore data lineage in the audit section"
  ]
};

// Demo mode utilities
export const DemoMode = {
  // Enable/disable demo mode
  enable(): void {
    isDemoMode = true;
    localStorage.setItem('opspilot_demo_mode', 'true');
    console.log('🎯 Demo mode enabled');
  },

  disable(): void {
    isDemoMode = false;
    localStorage.removeItem('opspilot_demo_mode');
    console.log('📊 Demo mode disabled');
  },

  // Check if demo mode is active
  isEnabled(): boolean {
    if (isDemoMode) return true;
    
    // Check localStorage
    const stored = localStorage.getItem('opspilot_demo_mode');
    isDemoMode = stored === 'true';
    return isDemoMode;
  },

  // Toggle demo mode
  toggle(): boolean {
    if (this.isEnabled()) {
      this.disable();
    } else {
      this.enable();
    }
    return this.isEnabled();
  },

  // Get demo data
  getData(key: keyof typeof DEMO_CONFIG): any {
    return DEMO_CONFIG[key];
  },

  // Get random demo tip
  getRandomTip(): string {
    const tips = DEMO_CONFIG.tips;
    return tips[Math.floor(Math.random() * tips.length)];
  },

  // Simulate loading delay for demo effect
  async simulateLoading(minMs: number = 500, maxMs: number = 1500): Promise<void> {
    if (!this.isEnabled()) return;
    
    const delay = Math.random() * (maxMs - minMs) + minMs;
    await new Promise(resolve => setTimeout(resolve, delay));
  },

  // Add demo data to API responses
  enhanceApiResponse(data: any, type: 'metrics' | 'trades' | 'exceptions' | 'span'): any {
    if (!this.isEnabled()) return data;

    switch (type) {
      case 'metrics':
        return {
          ...data,
          ...DEMO_CONFIG.sampleMetrics,
          isDemoData: true
        };
      
      case 'trades':
        return {
          ...data,
          trades: data.trades?.map((trade: any, index: number) => ({
            ...trade,
            demoHighlight: index < 5, // Highlight first 5 trades
            demoNote: index === 0 ? "This trade has a price break" : undefined
          })) || [],
          isDemoData: true
        };
      
      case 'exceptions':
        return {
          ...data,
          exceptions: data.exceptions?.map((exception: any, index: number) => ({
            ...exception,
            demoCluster: index < 10 ? `CLUSTER_${Math.floor(index / 3) + 1}` : undefined,
            demoSeverity: ['HIGH', 'MEDIUM', 'LOW'][index % 3]
          })) || [],
          isDemoData: true
        };
      
      case 'span':
        return {
          ...data,
          margins: data.margins?.map((margin: any) => ({
            ...margin,
            demoTrend: Math.random() > 0.5 ? 'up' : 'down',
            demoChange: (Math.random() * 10 - 5).toFixed(2) + '%'
          })) || [],
          isDemoData: true
        };
      
      default:
        return { ...data, isDemoData: true };
    }
  }
};

// Demo notification component data
export const DemoNotifications = {
  welcome: {
    title: "🎯 Welcome to OpsPilot MVP Demo!",
    message: "Explore derivatives data automation with realistic sample data. Click anywhere to dismiss this message.",
    type: "info" as const,
    duration: 10000
  },
  
  features: [
    {
      title: "📊 ETD Reconciliation",
      message: "View trade matching results with automatic break detection",
      type: "success" as const
    },
    {
      title: "🎯 Exception Clustering",
      message: "Smart grouping of similar breaks with SLA management",
      type: "info" as const
    },
    {
      title: "📈 SPAN Analysis",
      message: "Margin requirement analysis with delta reporting",
      type: "warning" as const
    },
    {
      title: "🔍 Audit Trail",
      message: "Complete data lineage and activity tracking",
      type: "info" as const
    }
  ]
};

// Demo tour steps
export const DemoTour = {
  steps: [
    {
      target: '[data-tour="dashboard"]',
      title: "Dashboard Overview",
      content: "Get a high-level view of all reconciliation activities, exceptions, and system health.",
      placement: "bottom" as const
    },
    {
      target: '[data-tour="reconciliation"]',
      title: "Trade Reconciliation",
      content: "Upload internal and cleared trade files to identify breaks and mismatches.",
      placement: "bottom" as const
    },
    {
      target: '[data-tour="exceptions"]',
      title: "Exception Management",
      content: "Review, cluster, and manage reconciliation breaks with SLA tracking.",
      placement: "bottom" as const
    },
    {
      target: '[data-tour="span"]',
      title: "SPAN Analysis",
      content: "Analyze margin requirements and track changes over time.",
      placement: "bottom" as const
    },
    {
      target: '[data-tour="audit"]',
      title: "Audit & Lineage",
      content: "Track all system activities and data transformations for compliance.",
      placement: "bottom" as const
    }
  ]
};

// Export demo mode instance
export default DemoMode;
