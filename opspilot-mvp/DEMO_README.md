# 🎯 OpsPilot MVP Demo Guide

Welcome to the OpsPilot MVP demonstration! This guide will help you run and explore the complete derivatives data automation platform.

## 🚀 Quick Start

### Option 1: Automated Demo (Recommended)
```bash
# Run the complete demo setup
python scripts/demo_run.py
```

This will:
- Generate realistic sample data (ETD, OTC, SPAN)
- Start backend and frontend services
- Upload files and run reconciliation
- Open the UI in your browser
- Show you exactly what to explore

### Option 2: Manual Setup
```bash
# 1. Generate demo data
python scripts/demo_seed.py

# 2. Start backend (in one terminal)
cd apps/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Start frontend (in another terminal)
cd apps/frontend
npm run dev

# 4. Open http://localhost:3000
```

## 📊 Demo Features

### 🔄 **ETD Reconciliation**
- **1,000 internal trades** vs **950 cleared trades**
- **~50 intentional breaks** for demonstration
- **Smart matching** on trade_date + account + symbol
- **Price tolerance** of 1 tick, quantity exact match

### 🎯 **Exception Management**
- **Automatic clustering** of similar breaks
- **4-tier SLA system**: CRITICAL (2h), HIGH (8h), MEDIUM (24h), LOW (72h)
- **Auto-escalation** at 50% SLA time
- **Bulk operations** for mass assignment/resolution
- **Team workload** monitoring

### 📈 **SPAN Margin Analysis**
- **500 margin records** across multiple products
- **Delta calculation** between snapshots
- **Narrative generation** for margin changes
- **Risk analysis** and reporting

### 💱 **OTC FpML Processing**
- **Sample IRS trades** in FpML 5.x format
- **Economic matching** for key terms
- **Canonical trade** representation

### 🔍 **Audit & Lineage**
- **Immutable audit trail** with hash chaining
- **Complete data lineage** from source to output
- **Tamper detection** and integrity verification
- **Compliance reporting**

## 🎮 Demo Scenarios

### Scenario 1: Trade Reconciliation Flow
1. **Dashboard** → See overview metrics
2. **Upload** → Internal and cleared trade files
3. **Reconciliation** → Run ETD matching
4. **Results** → View matches and breaks
5. **Exceptions** → Explore break details

### Scenario 2: Exception Management
1. **Exceptions Tab** → View all breaks
2. **Clustering** → Group similar issues
3. **Assignment** → Route to teams
4. **SLA Tracking** → Monitor resolution times
5. **Bulk Actions** → Mass operations

### Scenario 3: SPAN Analysis
1. **SPAN Tab** → Upload margin files
2. **Snapshots** → View margin data
3. **Deltas** → Compare time periods
4. **Narratives** → Understand changes
5. **Reports** → Generate summaries

### Scenario 4: Audit Trail
1. **Audit Tab** → View system activities
2. **Lineage** → Trace data flow
3. **Integrity** → Verify chain
4. **Export** → Compliance reports

## 📁 Demo Data Structure

```
demo_data/
├── internal/
│   └── etd_trades_internal_20240115.csv    # 1,000 internal trades
├── cleared/
│   └── etd_trades_cleared_20240115.csv     # 950 cleared trades (with breaks)
├── span/
│   └── span_margins_20240115.csv           # 500 margin records
└── otc/
    └── otc_trades_20240115.xml             # Sample FpML trades
```

## 🎯 Key Demo Highlights

### **Smart Break Detection**
- Price breaks: ±$0.25, $0.50, $0.75
- Quantity breaks: +1, +2, +5 shares
- Missing trades in cleared data

### **Realistic Data**
- **10 symbols**: ES, NQ, YM, RTY, ZN, ZB, ZF, GC, SI, CL
- **5 accounts**: PROP_DESK, CLIENT_A, CLIENT_B, HEDGE_FUND_1, PENSION_FUND
- **4 exchanges**: CME, CBOT, NYMEX, ICE
- **Market-realistic prices** with ±5% variation

### **Exception Clustering**
- **Fuzzy hash clustering** groups similar breaks
- **Cause-based grouping**: price vs quantity vs missing
- **Confidence scoring** for cluster assignments

### **SLA Management**
- **Auto-assignment rules** by product, counterparty, amount
- **Escalation workflows** with notifications
- **Team capacity** and specialization tracking

## 🔧 Configuration

### Demo Mode Toggle
```typescript
// Enable demo mode with sample data
DemoMode.enable();

// Disable for production use
DemoMode.disable();
```

### Reconciliation Settings
```json
{
  "match_keys": ["trade_date", "account", "symbol"],
  "price_tolerance_ticks": 1,
  "qty_tolerance": 0,
  "default_tick_size": 0.25
}
```

### Clustering Configuration
```json
{
  "method": "fuzzy_hash",
  "threshold": 0.8,
  "max_clusters": 50
}
```

## 🧪 Testing

### Run End-to-End Tests
```bash
# Complete demo workflow test
python tests/e2e/test_demo_flow.py

# Or with pytest
pytest tests/e2e/test_demo_flow.py -v
```

### Test Coverage
- ✅ Data generation and file uploads
- ✅ ETD reconciliation workflow
- ✅ Exception clustering and SLA
- ✅ SPAN margin processing
- ✅ OTC FpML handling
- ✅ Audit trail and lineage
- ✅ API endpoints and responses
- ✅ Performance benchmarks

## 🎨 UI Features

### **Interactive Dashboard**
- Real-time metrics and KPIs
- Drill-down capabilities
- Responsive design

### **Data Grids**
- Sortable and filterable tables
- Bulk selection and actions
- Export capabilities

### **Exception Management**
- Tabbed interface (All, Clusters, SLA, Teams)
- Visual status indicators
- Bulk assignment workflows

### **Charts & Visualizations**
- SPAN margin trends
- Exception aging analysis
- SLA breach monitoring

## 🔗 API Endpoints

### Core Operations
- `POST /api/v1/files/upload` - File upload
- `POST /api/v1/reconcile/etd` - ETD reconciliation
- `GET /api/v1/exceptions/` - List exceptions
- `POST /api/v1/exceptions/cluster` - Cluster exceptions

### SPAN & Margins
- `POST /api/v1/span/upload/{file_id}` - Process SPAN data
- `POST /api/v1/margin/deltas` - Calculate deltas
- `GET /api/v1/margin/narratives` - Get narratives

### Audit & Lineage
- `GET /api/v1/audit/events` - Audit events
- `GET /api/v1/audit/lineage/nodes` - Lineage nodes
- `POST /api/v1/audit/export` - Export audit data

### Documentation
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API docs

## 🎯 Demo Tips

### **For Presentations**
1. Start with the **Dashboard** for overview
2. Show **file upload** and **reconciliation**
3. Explore **exceptions** and **clustering**
4. Demonstrate **SLA management**
5. Highlight **audit trail** for compliance

### **For Technical Audiences**
1. Show **API documentation** at `/docs`
2. Demonstrate **data lineage** tracking
3. Explain **hash chain integrity**
4. Show **clustering algorithms**
5. Discuss **scalability** features

### **For Business Users**
1. Focus on **operational efficiency**
2. Show **exception workflows**
3. Demonstrate **SLA monitoring**
4. Highlight **audit compliance**
5. Show **reporting capabilities**

## 🚨 Troubleshooting

### Services Not Starting
```bash
# Check if ports are in use
netstat -an | findstr :8000
netstat -an | findstr :3000

# Kill existing processes if needed
taskkill /f /im python.exe
taskkill /f /im node.exe
```

### Database Issues
```bash
# Reset database (if needed)
cd apps/backend
alembic downgrade base
alembic upgrade head
```

### File Upload Errors
- Check file permissions
- Verify CSV format and headers
- Ensure files are not empty

### Performance Issues
- Reduce demo data size in `demo_seed.py`
- Check available memory
- Monitor CPU usage during reconciliation

## 📞 Support

For demo support or questions:
- Check the main `README.md` for setup instructions
- Review API docs at `http://localhost:8000/docs`
- Run tests to verify functionality
- Check logs in terminal outputs

## 🎉 Demo Success Metrics

A successful demo should show:
- ✅ **1,000+ trades** processed
- ✅ **~50 exceptions** identified
- ✅ **10+ clusters** created
- ✅ **500+ SPAN records** processed
- ✅ **Complete audit trail** maintained
- ✅ **Sub-30 second** reconciliation time
- ✅ **Interactive UI** fully functional

---

**🚀 Ready to showcase OpsPilot MVP? Run `python scripts/demo_run.py` and let's go!**
