import React, { useState } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DataGrid } from '@/components/DataGrid';
import { KPICard } from '@/components/KPICard';

interface ParsedTrade {
  trade_id: string;
  trade_date: string;
  counterparty: string;
  product_type: string;
  notional?: number;
  currency?: string;
  fixed_rate?: number;
  forward_rate?: number;
  effective_date?: string;
  maturity_date?: string;
  value_date?: string;
}

interface ReconException {
  exception_type: string;
  trade_id: string;
  account: string;
  symbol: string;
  difference_summary: string;
  additional_details?: {
    economic_differences?: Array<{
      field: string;
      internal: string;
      external: string;
      difference: string;
      within_tolerance: boolean;
    }>;
  };
}

interface ReconResult {
  reconciliation_summary: {
    internal_trades: number;
    external_confirmations: number;
    matched_trades: number;
    exceptions: number;
    match_rate: string;
  };
  exceptions: ReconException[];
  summary_stats: {
    irs_trades?: number;
    fx_trades?: number;
    economic_breaks?: number;
    missing_confirmations?: number;
    unexpected_confirmations?: number;
  };
}

export default function OTC() {
  const [fpmlFile, setFpmlFile] = useState<File | null>(null);
  const [internalFile, setInternalFile] = useState<File | null>(null);
  const [parsedTrades, setParsedTrades] = useState<ParsedTrade[]>([]);
  const [reconResult, setReconResult] = useState<ReconResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isReconciling, setIsReconciling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('upload');

  const handleFpmlUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('/api/v1/otc/fpml', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      setParsedTrades(result.trades || []);
      setFpmlFile(file);
      setActiveTab('parsed');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReconciliation = async () => {
    if (!fpmlFile || !internalFile) {
      setError('Please upload both FpML and internal trade files');
      return;
    }

    setIsReconciling(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('internal_file', internalFile);
      formData.append('external_file', fpmlFile);
      formData.append('rate_tolerance_bp', '0.5');
      formData.append('notional_tolerance', '1.0');
      formData.append('date_tolerance_days', '0');
      
      const response = await fetch('/api/v1/otc/reconcile', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Reconciliation failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      setReconResult(result);
      setActiveTab('reconciliation');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reconciliation failed');
    } finally {
      setIsReconciling(false);
    }
  };

  const handleDrop = (e: React.DragEvent, fileType: 'fpml' | 'internal') => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const file = files[0];
    
    if (!file) return;
    
    if (fileType === 'fpml') {
      if (file.name.endsWith('.xml') || file.name.endsWith('.zip')) {
        handleFpmlUpload(file);
      } else {
        setError('Please upload XML or ZIP files for FpML confirmations');
      }
    } else {
      if (file.name.endsWith('.csv')) {
        setInternalFile(file);
      } else {
        setError('Please upload CSV files for internal trades');
      }
    }
  };

  const tradeColumns = [
    { key: 'trade_id', header: 'Trade ID', width: '120px' },
    { key: 'product_type', header: 'Product', width: '80px' },
    { key: 'counterparty', header: 'Counterparty', width: '120px' },
    { 
      key: 'notional', 
      header: 'Notional', 
      width: '120px',
      render: (value: number, row: ParsedTrade) => 
        value ? `${row.currency || ''} ${value.toLocaleString()}` : '-'
    },
    { 
      key: 'fixed_rate', 
      header: 'Rate', 
      width: '100px',
      render: (value: number) => 
        value ? `${(value * 100).toFixed(3)}%` : '-'
    },
    { key: 'effective_date', header: 'Effective', width: '100px' },
    { key: 'maturity_date', header: 'Maturity', width: '100px' }
  ];

  const exceptionColumns = [
    { key: 'trade_id', header: 'Trade ID', width: '120px' },
    { 
      key: 'exception_type', 
      header: 'Type', 
      width: '120px',
      render: (value: string) => (
        <Badge variant={value === 'PRICE_BREAK' ? 'destructive' : 'secondary'}>
          {value.replace('_', ' ')}
        </Badge>
      )
    },
    { key: 'account', header: 'Account', width: '100px' },
    { key: 'symbol', header: 'Product', width: '80px' },
    { key: 'difference_summary', header: 'Difference', width: '300px' }
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">OTC Trade Processing</h1>
        <p className="text-muted-foreground">
          Upload FpML confirmations and reconcile against internal trades
        </p>
      </div>

      {error && (
        <Alert className="mb-6" variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="upload">Upload Files</TabsTrigger>
          <TabsTrigger value="parsed" disabled={parsedTrades.length === 0}>
            Parsed Trades ({parsedTrades.length})
          </TabsTrigger>
          <TabsTrigger value="reconciliation" disabled={!reconResult}>
            Reconciliation
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* FpML Upload */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  FpML Confirmations
                </CardTitle>
                <CardDescription>
                  Upload XML files or ZIP archives containing FpML confirmations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:border-muted-foreground/50 transition-colors cursor-pointer"
                  onDrop={(e) => handleDrop(e, 'fpml')}
                  onDragOver={(e) => e.preventDefault()}
                  onClick={() => document.getElementById('fpml-upload')?.click()}
                >
                  <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground mb-2">
                    {fpmlFile ? fpmlFile.name : 'Drop FpML files here or click to browse'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Supports XML and ZIP files
                  </p>
                  <input
                    id="fpml-upload"
                    type="file"
                    accept=".xml,.zip"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFpmlUpload(file);
                    }}
                  />
                </div>
                {fpmlFile && (
                  <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    {parsedTrades.length} trades parsed successfully
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Internal Trades Upload */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Internal Trades
                </CardTitle>
                <CardDescription>
                  Upload CSV file containing internal trade data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:border-muted-foreground/50 transition-colors cursor-pointer"
                  onDrop={(e) => handleDrop(e, 'internal')}
                  onDragOver={(e) => e.preventDefault()}
                  onClick={() => document.getElementById('internal-upload')?.click()}
                >
                  <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground mb-2">
                    {internalFile ? internalFile.name : 'Drop CSV file here or click to browse'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    CSV format required
                  </p>
                  <input
                    id="internal-upload"
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) setInternalFile(file);
                    }}
                  />
                </div>
                {internalFile && (
                  <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    File uploaded successfully
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {fpmlFile && internalFile && (
            <div className="flex justify-center">
              <Button
                onClick={handleReconciliation}
                disabled={isReconciling}
                size="lg"
                className="px-8"
              >
                {isReconciling ? 'Reconciling...' : 'Run Reconciliation'}
              </Button>
            </div>
          )}
        </TabsContent>

        <TabsContent value="parsed" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Parsed FpML Trades</CardTitle>
              <CardDescription>
                {parsedTrades.length} trades extracted from FpML confirmations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataGrid
                data={parsedTrades}
                columns={tradeColumns}
                className="min-h-[400px]"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reconciliation" className="space-y-6">
          {reconResult && (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <KPICard
                  title="Match Rate"
                  value={reconResult.reconciliation_summary.match_rate}
                  icon={<CheckCircle className="h-4 w-4" />}
                  trend="neutral"
                />
                <KPICard
                  title="Matched Trades"
                  value={reconResult.reconciliation_summary.matched_trades.toString()}
                  icon={<CheckCircle className="h-4 w-4" />}
                  trend="positive"
                />
                <KPICard
                  title="Exceptions"
                  value={reconResult.reconciliation_summary.exceptions.toString()}
                  icon={<AlertCircle className="h-4 w-4" />}
                  trend={reconResult.reconciliation_summary.exceptions > 0 ? "negative" : "neutral"}
                />
                <KPICard
                  title="Economic Breaks"
                  value={(reconResult.summary_stats.economic_breaks || 0).toString()}
                  icon={<TrendingUp className="h-4 w-4" />}
                  trend="negative"
                />
              </div>

              {/* Exceptions */}
              {reconResult.exceptions.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Reconciliation Exceptions</CardTitle>
                    <CardDescription>
                      {reconResult.exceptions.length} exceptions requiring attention
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <DataGrid
                      data={reconResult.exceptions}
                      columns={exceptionColumns}
                      className="min-h-[300px]"
                      onRowClick={(exception) => {
                        // Show detailed exception view
                        console.log('Exception details:', exception);
                      }}
                    />
                  </CardContent>
                </Card>
              )}

              {/* Summary Stats */}
              <Card>
                <CardHeader>
                  <CardTitle>Reconciliation Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Internal Trades:</span>
                      <span className="ml-2">{reconResult.reconciliation_summary.internal_trades}</span>
                    </div>
                    <div>
                      <span className="font-medium">External Confirmations:</span>
                      <span className="ml-2">{reconResult.reconciliation_summary.external_confirmations}</span>
                    </div>
                    <div>
                      <span className="font-medium">IRS Trades:</span>
                      <span className="ml-2">{reconResult.summary_stats.irs_trades || 0}</span>
                    </div>
                    <div>
                      <span className="font-medium">FX Trades:</span>
                      <span className="ml-2">{reconResult.summary_stats.fx_trades || 0}</span>
                    </div>
                    <div>
                      <span className="font-medium">Missing Confirmations:</span>
                      <span className="ml-2">{reconResult.summary_stats.missing_confirmations || 0}</span>
                    </div>
                    <div>
                      <span className="font-medium">Unexpected Confirmations:</span>
                      <span className="ml-2">{reconResult.summary_stats.unexpected_confirmations || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
