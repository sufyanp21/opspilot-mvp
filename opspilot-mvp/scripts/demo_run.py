#!/usr/bin/env python3
"""
OpsPilot MVP Demo Runner
Orchestrates the complete demo experience: seed data, run reconciliation, open UI.
"""

import os
import sys
import time
import subprocess
import requests
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional

# Add the backend app to Python path
sys.path.append(str(Path(__file__).parent.parent / "apps" / "backend"))

from demo_seed import DemoDataGenerator


class DemoRunner:
    """Orchestrates the complete OpsPilot MVP demo experience."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.demo_dir = Path(__file__).parent.parent / "demo_data"
        self.backend_dir = Path(__file__).parent.parent / "apps" / "backend"
        self.frontend_dir = Path(__file__).parent.parent / "apps" / "frontend"
    
    def check_services(self) -> Dict[str, bool]:
        """Check if backend and frontend services are running."""
        services = {"backend": False, "frontend": False}
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            services["backend"] = response.status_code == 200
        except:
            pass
        
        try:
            response = requests.get(self.frontend_url, timeout=5)
            services["frontend"] = response.status_code == 200
        except:
            pass
        
        return services
    
    def start_services(self):
        """Start backend and frontend services."""
        print("🚀 Starting OpsPilot MVP services...")
        
        services = self.check_services()
        
        if not services["backend"]:
            print("  • Starting backend API server...")
            try:
                # Start backend using uvicorn
                backend_cmd = [
                    sys.executable, "-m", "uvicorn", 
                    "app.main:app", 
                    "--host", "0.0.0.0", 
                    "--port", "8000",
                    "--reload"
                ]
                subprocess.Popen(
                    backend_cmd, 
                    cwd=self.backend_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("    ✅ Backend starting on http://localhost:8000")
            except Exception as e:
                print(f"    ❌ Failed to start backend: {e}")
        else:
            print("  • Backend already running ✅")
        
        if not services["frontend"]:
            print("  • Starting frontend dev server...")
            try:
                # Start frontend using npm/yarn
                frontend_cmd = ["npm", "run", "dev"]
                subprocess.Popen(
                    frontend_cmd,
                    cwd=self.frontend_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("    ✅ Frontend starting on http://localhost:3000")
            except Exception as e:
                print(f"    ❌ Failed to start frontend: {e}")
        else:
            print("  • Frontend already running ✅")
        
        # Wait for services to be ready
        if not all(services.values()):
            print("  • Waiting for services to start...")
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                services = self.check_services()
                if all(services.values()):
                    break
                print(f"    Waiting... ({i+1}/30)")
            
            if not all(services.values()):
                print("  ⚠️  Services may not be fully ready, continuing anyway...")
    
    def upload_file(self, filepath: str, file_kind: str) -> Optional[str]:
        """Upload a file to the OpsPilot API."""
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (Path(filepath).name, f, 'text/csv')}
                data = {'file_kind': file_kind}
                
                response = requests.post(
                    f"{self.base_url}/api/v1/files/upload",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"    ✅ Uploaded {Path(filepath).name} (ID: {result.get('file_id', 'unknown')})")
                    return result.get('file_id')
                else:
                    print(f"    ❌ Failed to upload {Path(filepath).name}: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"    ❌ Error uploading {Path(filepath).name}: {e}")
            return None
    
    def run_reconciliation(self, internal_file_id: str, cleared_file_id: str) -> Optional[str]:
        """Run ETD reconciliation."""
        try:
            recon_request = {
                "internal_file_id": internal_file_id,
                "cleared_file_id": cleared_file_id,
                "match_keys": ["trade_date", "account", "symbol"],
                "price_tolerance_ticks": 1,
                "qty_tolerance": 0,
                "default_tick_size": 0.25
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/reconcile/etd",
                json=recon_request,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                run_id = result.get('run_id')
                print(f"    ✅ Reconciliation completed (Run ID: {run_id})")
                print(f"      • Total trades: {result.get('total_trades', 0)}")
                print(f"      • Matched: {result.get('matched_trades', 0)}")
                print(f"      • Exceptions: {result.get('exception_count', 0)}")
                return run_id
            else:
                print(f"    ❌ Reconciliation failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    ❌ Error running reconciliation: {e}")
            return None
    
    def run_exception_clustering(self) -> bool:
        """Run exception clustering analysis."""
        try:
            clustering_request = {
                "method": "fuzzy_hash",
                "config": {
                    "threshold": 0.8,
                    "max_clusters": 50
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/exceptions/cluster",
                json=clustering_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"    ✅ Exception clustering completed")
                print(f"      • Clusters created: {result.get('cluster_count', 0)}")
                print(f"      • Exceptions clustered: {result.get('clustered_exceptions', 0)}")
                return True
            else:
                print(f"    ❌ Exception clustering failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ❌ Error running exception clustering: {e}")
            return False
    
    def process_span_margins(self, span_file_id: str) -> bool:
        """Process SPAN margin data."""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/span/upload/{span_file_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"    ✅ SPAN processing completed")
                print(f"      • Snapshots created: {result.get('snapshot_count', 0)}")
                return True
            else:
                print(f"    ❌ SPAN processing failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ❌ Error processing SPAN data: {e}")
            return False
    
    def run_complete_demo(self):
        """Run the complete demo workflow."""
        print("🎯 OpsPilot MVP Demo Runner")
        print("=" * 50)
        
        # Step 1: Generate demo data
        print("\n📊 Step 1: Generating Demo Data")
        generator = DemoDataGenerator()
        demo_files = generator.generate_all_demo_data()
        
        if not demo_files:
            print("❌ Failed to generate demo data")
            return False
        
        # Step 2: Start services
        print("\n🚀 Step 2: Starting Services")
        self.start_services()
        
        # Step 3: Upload files
        print("\n📁 Step 3: Uploading Demo Files")
        
        internal_file_id = self.upload_file(demo_files["internal_etd"], "internal")
        cleared_file_id = self.upload_file(demo_files["cleared_etd"], "cleared")
        span_file_id = self.upload_file(demo_files["span_margins"], "span")
        
        if not internal_file_id or not cleared_file_id:
            print("❌ Failed to upload required files")
            return False
        
        # Step 4: Run reconciliation
        print("\n🔄 Step 4: Running ETD Reconciliation")
        run_id = self.run_reconciliation(internal_file_id, cleared_file_id)
        
        if not run_id:
            print("❌ Failed to run reconciliation")
            return False
        
        # Step 5: Run exception clustering
        print("\n🎯 Step 5: Running Exception Clustering")
        self.run_exception_clustering()
        
        # Step 6: Process SPAN data
        if span_file_id:
            print("\n📈 Step 6: Processing SPAN Margins")
            self.process_span_margins(span_file_id)
        
        # Step 7: Open UI
        print("\n🌐 Step 7: Opening Demo UI")
        try:
            webbrowser.open(self.frontend_url)
            print(f"    ✅ Opening {self.frontend_url} in browser")
        except Exception as e:
            print(f"    ⚠️  Could not open browser automatically: {e}")
            print(f"    Please manually navigate to: {self.frontend_url}")
        
        # Demo complete
        print("\n" + "=" * 50)
        print("🎉 OpsPilot MVP Demo Setup Complete!")
        print("\n🎯 Demo Features to Explore:")
        print("  • ETD Trade Reconciliation with breaks")
        print("  • Exception Clustering & SLA Management")
        print("  • SPAN Margin Analysis")
        print("  • OTC FpML Processing")
        print("  • Audit Trail & Data Lineage")
        print("  • Interactive Dashboard & Reports")
        
        print(f"\n🌐 Access the demo at: {self.frontend_url}")
        print(f"📚 API documentation: {self.base_url}/docs")
        
        print("\n⚡ Quick Demo Flow:")
        print("  1. Dashboard - See overview metrics")
        print("  2. Reconciliation - View trade matches & breaks")
        print("  3. Exceptions - Explore clustered breaks & SLA")
        print("  4. SPAN - Analyze margin requirements")
        print("  5. Audit - Review system activity trail")
        
        return True


def main():
    """Main demo runner function."""
    try:
        runner = DemoRunner()
        success = runner.run_complete_demo()
        
        if success:
            print("\n✨ Demo is ready! Press Ctrl+C to stop services when done.")
            try:
                # Keep script running
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Demo stopped. Services may still be running.")
        else:
            print("\n❌ Demo setup failed. Check the logs above.")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Demo runner error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
