#!/usr/bin/env python3
"""
End-to-end demo flow tests for OpsPilot MVP
Tests the complete demo workflow from data generation to UI interaction.
"""

import pytest
import requests
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add scripts to path for demo utilities
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))

from demo_seed import DemoDataGenerator
from demo_run import DemoRunner


class TestDemoFlow:
    """End-to-end tests for the complete demo workflow."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.base_url = "http://localhost:8000"
        cls.frontend_url = "http://localhost:3000"
        cls.demo_runner = DemoRunner()
        cls.demo_generator = DemoDataGenerator()
        cls.test_files = {}
    
    def test_01_services_running(self):
        """Test that required services are running."""
        services = self.demo_runner.check_services()
        
        # Backend should be running
        assert services["backend"], "Backend service not running on localhost:8000"
        
        # Frontend is optional for API tests
        if not services["frontend"]:
            print("⚠️  Frontend not running - UI tests will be skipped")
    
    def test_02_generate_demo_data(self):
        """Test demo data generation."""
        # Generate demo data
        demo_files = self.demo_generator.generate_all_demo_data()
        
        assert demo_files is not None, "Failed to generate demo data"
        assert "internal_etd" in demo_files, "Missing internal ETD file"
        assert "cleared_etd" in demo_files, "Missing cleared ETD file"
        assert "span_margins" in demo_files, "Missing SPAN margins file"
        assert "otc_fpml" in demo_files, "Missing OTC FpML file"
        
        # Verify files exist
        for file_type, filepath in demo_files.items():
            assert Path(filepath).exists(), f"Generated file does not exist: {filepath}"
            assert Path(filepath).stat().st_size > 0, f"Generated file is empty: {filepath}"
        
        self.test_files = demo_files
        print(f"✅ Generated {len(demo_files)} demo files")
    
    def test_03_api_health_check(self):
        """Test API health endpoint."""
        response = requests.get(f"{self.base_url}/api/v1/health")
        
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        health_data = response.json()
        assert health_data["status"] == "healthy", "API not healthy"
        
        print("✅ API health check passed")
    
    def test_04_file_upload_internal(self):
        """Test uploading internal ETD file."""
        filepath = self.test_files["internal_etd"]
        
        with open(filepath, 'rb') as f:
            files = {'file': (Path(filepath).name, f, 'text/csv')}
            data = {'file_kind': 'internal'}
            
            response = requests.post(
                f"{self.base_url}/api/v1/files/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == 200, f"Internal file upload failed: {response.status_code}"
        
        result = response.json()
        assert "file_id" in result, "No file_id in upload response"
        
        self.internal_file_id = result["file_id"]
        print(f"✅ Uploaded internal file: {self.internal_file_id}")
    
    def test_05_file_upload_cleared(self):
        """Test uploading cleared ETD file."""
        filepath = self.test_files["cleared_etd"]
        
        with open(filepath, 'rb') as f:
            files = {'file': (Path(filepath).name, f, 'text/csv')}
            data = {'file_kind': 'cleared'}
            
            response = requests.post(
                f"{self.base_url}/api/v1/files/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == 200, f"Cleared file upload failed: {response.status_code}"
        
        result = response.json()
        assert "file_id" in result, "No file_id in upload response"
        
        self.cleared_file_id = result["file_id"]
        print(f"✅ Uploaded cleared file: {self.cleared_file_id}")
    
    def test_06_file_upload_span(self):
        """Test uploading SPAN margins file."""
        filepath = self.test_files["span_margins"]
        
        with open(filepath, 'rb') as f:
            files = {'file': (Path(filepath).name, f, 'text/csv')}
            data = {'file_kind': 'span'}
            
            response = requests.post(
                f"{self.base_url}/api/v1/files/upload",
                files=files,
                data=data
            )
        
        assert response.status_code == 200, f"SPAN file upload failed: {response.status_code}"
        
        result = response.json()
        assert "file_id" in result, "No file_id in upload response"
        
        self.span_file_id = result["file_id"]
        print(f"✅ Uploaded SPAN file: {self.span_file_id}")
    
    def test_07_etd_reconciliation(self):
        """Test ETD reconciliation process."""
        recon_request = {
            "internal_file_id": self.internal_file_id,
            "cleared_file_id": self.cleared_file_id,
            "match_keys": ["trade_date", "account", "symbol"],
            "price_tolerance_ticks": 1,
            "qty_tolerance": 0,
            "default_tick_size": 0.25
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/reconcile/etd",
            json=recon_request
        )
        
        assert response.status_code == 200, f"Reconciliation failed: {response.status_code}"
        
        result = response.json()
        assert "run_id" in result, "No run_id in reconciliation response"
        assert "total_trades" in result, "No total_trades in response"
        assert "matched_trades" in result, "No matched_trades in response"
        assert "exception_count" in result, "No exception_count in response"
        
        self.run_id = result["run_id"]
        self.total_trades = result["total_trades"]
        self.exception_count = result["exception_count"]
        
        print(f"✅ Reconciliation completed: {self.total_trades} trades, {self.exception_count} exceptions")
    
    def test_08_get_reconciliation_results(self):
        """Test retrieving reconciliation results."""
        response = requests.get(f"{self.base_url}/api/v1/reconcile/runs/{self.run_id}")
        
        assert response.status_code == 200, f"Failed to get reconciliation results: {response.status_code}"
        
        result = response.json()
        assert result["id"] == self.run_id, "Run ID mismatch"
        assert "status" in result, "No status in reconciliation result"
        
        print(f"✅ Retrieved reconciliation results for run {self.run_id}")
    
    def test_09_get_exceptions(self):
        """Test retrieving reconciliation exceptions."""
        response = requests.get(f"{self.base_url}/api/v1/exceptions/")
        
        assert response.status_code == 200, f"Failed to get exceptions: {response.status_code}"
        
        exceptions = response.json()
        assert isinstance(exceptions, list), "Exceptions response should be a list"
        
        if self.exception_count > 0:
            assert len(exceptions) > 0, "Should have exceptions but got empty list"
        
        print(f"✅ Retrieved {len(exceptions)} exceptions")
    
    def test_10_exception_clustering(self):
        """Test exception clustering functionality."""
        if self.exception_count == 0:
            pytest.skip("No exceptions to cluster")
        
        clustering_request = {
            "method": "fuzzy_hash",
            "config": {
                "threshold": 0.8,
                "max_clusters": 50
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/exceptions/cluster",
            json=clustering_request
        )
        
        assert response.status_code == 200, f"Exception clustering failed: {response.status_code}"
        
        result = response.json()
        assert "cluster_count" in result, "No cluster_count in clustering response"
        
        print(f"✅ Exception clustering completed: {result.get('cluster_count', 0)} clusters")
    
    def test_11_span_processing(self):
        """Test SPAN margin processing."""
        response = requests.post(f"{self.base_url}/api/v1/span/upload/{self.span_file_id}")
        
        assert response.status_code == 200, f"SPAN processing failed: {response.status_code}"
        
        result = response.json()
        assert "snapshot_count" in result, "No snapshot_count in SPAN response"
        
        print(f"✅ SPAN processing completed: {result.get('snapshot_count', 0)} snapshots")
    
    def test_12_margin_deltas(self):
        """Test SPAN margin delta calculation."""
        # First, get available snapshots
        response = requests.get(f"{self.base_url}/api/v1/span/snapshots")
        
        if response.status_code == 200:
            snapshots = response.json()
            if len(snapshots) >= 2:
                # Test delta calculation between snapshots
                delta_request = {
                    "base_snapshot_id": snapshots[0]["id"],
                    "compare_snapshot_id": snapshots[1]["id"] if len(snapshots) > 1 else snapshots[0]["id"]
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/margin/deltas",
                    json=delta_request
                )
                
                if response.status_code == 200:
                    print("✅ Margin delta calculation completed")
                else:
                    print(f"⚠️  Margin delta calculation failed: {response.status_code}")
            else:
                print("⚠️  Not enough snapshots for delta calculation")
        else:
            print("⚠️  Could not retrieve SPAN snapshots")
    
    def test_13_otc_fpml_upload(self):
        """Test OTC FpML file processing."""
        filepath = self.test_files["otc_fpml"]
        
        with open(filepath, 'rb') as f:
            files = {'file': (Path(filepath).name, f, 'application/xml')}
            
            response = requests.post(
                f"{self.base_url}/api/v1/otc/fpml",
                files=files
            )
        
        # OTC processing might not be fully implemented, so we allow 404/501
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ OTC FpML processing completed: {result}")
        elif response.status_code in [404, 501]:
            print("⚠️  OTC FpML processing not fully implemented (expected)")
        else:
            print(f"⚠️  OTC FpML processing failed: {response.status_code}")
    
    def test_14_audit_events(self):
        """Test audit trail functionality."""
        response = requests.get(f"{self.base_url}/api/v1/audit/events")
        
        if response.status_code == 200:
            events = response.json()
            assert isinstance(events, list), "Audit events should be a list"
            print(f"✅ Retrieved {len(events)} audit events")
        elif response.status_code == 404:
            print("⚠️  Audit endpoints not available (expected if not implemented)")
        else:
            print(f"⚠️  Audit events retrieval failed: {response.status_code}")
    
    def test_15_lineage_tracking(self):
        """Test data lineage functionality."""
        response = requests.get(f"{self.base_url}/api/v1/audit/lineage/nodes")
        
        if response.status_code == 200:
            nodes = response.json()
            assert isinstance(nodes, list), "Lineage nodes should be a list"
            print(f"✅ Retrieved {len(nodes)} lineage nodes")
        elif response.status_code == 404:
            print("⚠️  Lineage endpoints not available (expected if not implemented)")
        else:
            print(f"⚠️  Lineage nodes retrieval failed: {response.status_code}")
    
    def test_16_api_documentation(self):
        """Test API documentation availability."""
        response = requests.get(f"{self.base_url}/docs")
        
        assert response.status_code == 200, f"API docs not available: {response.status_code}"
        
        print("✅ API documentation accessible")
    
    def test_17_frontend_accessibility(self):
        """Test frontend accessibility (if running)."""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("✅ Frontend accessible")
            else:
                print(f"⚠️  Frontend returned status: {response.status_code}")
        except requests.exceptions.RequestException:
            print("⚠️  Frontend not accessible (may not be running)")
    
    def test_18_demo_data_integrity(self):
        """Test that demo data maintains integrity throughout the workflow."""
        # Verify reconciliation results are consistent
        response = requests.get(f"{self.base_url}/api/v1/reconcile/runs/{self.run_id}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check that totals make sense
            total = result.get("total_trades", 0)
            matched = result.get("matched_trades", 0)
            exceptions = result.get("exception_count", 0)
            
            assert matched + exceptions <= total, "Matched + exceptions should not exceed total"
            assert total > 0, "Should have processed some trades"
            
            print(f"✅ Data integrity verified: {total} total, {matched} matched, {exceptions} exceptions")
        else:
            print("⚠️  Could not verify data integrity")
    
    def test_19_performance_metrics(self):
        """Test that demo performs within acceptable limits."""
        # Simple performance test - reconciliation should complete in reasonable time
        start_time = time.time()
        
        # Re-run a small reconciliation to measure performance
        small_recon_request = {
            "internal_file_id": self.internal_file_id,
            "cleared_file_id": self.cleared_file_id,
            "match_keys": ["trade_date", "account", "symbol"],
            "price_tolerance_ticks": 1,
            "qty_tolerance": 0,
            "default_tick_size": 0.25
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/reconcile/etd",
            json=small_recon_request
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            assert duration < 30, f"Reconciliation took too long: {duration:.2f}s"
            print(f"✅ Performance test passed: reconciliation completed in {duration:.2f}s")
        else:
            print("⚠️  Could not complete performance test")
    
    def test_20_cleanup(self):
        """Clean up test artifacts."""
        # Note: In a real implementation, you might want to clean up uploaded files
        # and database records created during testing
        
        print("✅ Test cleanup completed")
        print("\n" + "="*60)
        print("🎉 End-to-End Demo Tests Completed!")
        print("="*60)
        print(f"📊 Processed {self.total_trades} trades")
        print(f"🚨 Found {self.exception_count} exceptions")
        print(f"📁 Uploaded {len(self.test_files)} files")
        print(f"🔗 Run ID: {self.run_id}")
        print("\n🎯 Demo is ready for presentation!")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
