#!/usr/bin/env python3
"""
Test Portfolio Export Integration
Tests that the export system includes the new portfolio metrics
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock

# Add the project root to Python path
sys.path.insert(0, '/storage/emulated/0/scripts/retoid')

from stability_monitor.config.settings import Settings
from stability_monitor.controllers.app_controller import AppController

def test_export_portfolio_metrics():
    """Test that export includes portfolio metrics"""
    print("📊 Testing Export Portfolio Metrics Integration...")
    
    # Create test data
    now = datetime.now()
    test_data = [
        # Site A: 1 critical
        {'Number': 'INC001', 'Site': 'Wendy\'s #123', 'Priority': '1 - Critical', 'Created': now, 'Company': "Wendy's", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC002', 'Site': 'Wendy\'s #123', 'Priority': '2 - High', 'Created': now, 'Company': "Wendy's", 'Resolved': now + timedelta(hours=2)},
        
        # Site B: No criticals
        {'Number': 'INC003', 'Site': 'Wendy\'s #124', 'Priority': '3 - Medium', 'Created': now, 'Company': "Wendy's", 'Resolved': now + timedelta(hours=3)},
        
        # Site C: 1 critical  
        {'Number': 'INC004', 'Site': 'Wendy\'s #125', 'Priority': '1 - Critical', 'Created': now, 'Company': "Wendy's", 'Resolved': None},
    ]
    
    test_df = pd.DataFrame(test_data)
    
    # Configure settings with portfolio metrics
    settings = Settings()
    settings.set('stability_analysis.total_supported_sites.count', 50)  # 50 total sites
    
    print(f"   📋 Test scenario: 3 active sites, 2 with criticals, 50 total supported sites")
    
    # Create controller (mocked UI components)
    mock_root = Mock()
    mock_main_window = Mock()
    
    controller = AppController(mock_root, settings)
    controller.main_window = mock_main_window
    
    # Test the export sheet creation
    try:
        stability_data = controller._create_stability_analytics_sheet(test_df)
        
        print(f"   📈 Export sheet generated with {len(stability_data)} rows")
        
        # Check for portfolio metrics in export
        portfolio_metrics_found = {}
        for row in stability_data[1:]:  # Skip header
            if len(row) >= 2:
                metric_name = row[0]
                metric_value = row[1]
                portfolio_metrics_found[metric_name] = metric_value
        
        # Verify key portfolio metrics are present
        required_portfolio_metrics = [
            "Portfolio Stability", 
            "Total Supported Sites", 
            "Sites with Zero Critical Incidents", 
            "Portfolio Coverage"
        ]
        
        print(f"   🔍 Checking for portfolio metrics in export:")
        missing_metrics = []
        for metric in required_portfolio_metrics:
            if metric in portfolio_metrics_found:
                print(f"      ✅ {metric}: {portfolio_metrics_found[metric]}")
            else:
                print(f"      ❌ {metric}: Missing")
                missing_metrics.append(metric)
        
        if missing_metrics:
            print(f"   ❌ Missing {len(missing_metrics)} portfolio metrics from export")
            return False
        
        # Verify portfolio calculations are correct
        expected_portfolio_stability = "96.0%"  # 48 of 50 sites (50 - 2 with criticals)
        expected_total_sites = "50"
        expected_sites_zero_incidents = "48"  # 50 total - 2 with criticals
        expected_coverage = "6.0%"  # 3 of 50 sites had activity
        
        verifications = [
            ("Portfolio Stability", expected_portfolio_stability),
            ("Total Supported Sites", expected_total_sites),
            ("Sites with Zero Critical Incidents", expected_sites_zero_incidents),
            ("Portfolio Coverage", expected_coverage)
        ]
        
        print(f"   🎯 Verifying calculation accuracy:")
        for metric_name, expected_value in verifications:
            actual_value = portfolio_metrics_found.get(metric_name, "Not found")
            if actual_value == expected_value:
                print(f"      ✅ {metric_name}: {actual_value} (correct)")
            else:
                print(f"      ❌ {metric_name}: {actual_value} (expected: {expected_value})")
                return False
        
        # Verify legacy metric is still included
        if "Overall System Stability" in portfolio_metrics_found:
            print(f"      ✅ Legacy metric preserved: Overall System Stability: {portfolio_metrics_found['Overall System Stability']}")
        else:
            print(f"      ❌ Legacy metric missing: Overall System Stability")
            return False
        
        print(f"   ✅ All portfolio metrics correctly integrated into export system!")
        return True
        
    except Exception as e:
        print(f"   ❌ Export integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_export_fallback_mode():
    """Test export when total sites not configured (fallback mode)"""
    print("\n🔄 Testing Export Fallback Mode...")
    
    # Create test data
    now = datetime.now()
    test_data = [
        {'Number': 'INC001', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC002', 'Site': 'Site B', 'Priority': '3 - Medium', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)},
    ]
    
    test_df = pd.DataFrame(test_data)
    
    # Configure settings with NO total sites (fallback mode)
    settings = Settings()
    settings.set('stability_analysis.total_supported_sites.count', 0)  # Disabled
    
    print(f"   📋 Test scenario: Portfolio mode disabled, should fall back gracefully")
    
    # Create controller
    mock_root = Mock()
    mock_main_window = Mock()
    
    controller = AppController(mock_root, settings)
    controller.main_window = mock_main_window
    
    try:
        stability_data = controller._create_stability_analytics_sheet(test_df)
        
        # Check that export still works and includes fallback values
        metrics_found = {}
        for row in stability_data[1:]:  # Skip header
            if len(row) >= 2:
                metrics_found[row[0]] = row[1]
        
        # Should still have portfolio metrics but with fallback values
        if "Portfolio Stability" in metrics_found and "Total Supported Sites" in metrics_found:
            print(f"      ✅ Portfolio Stability: {metrics_found['Portfolio Stability']} (fallback to active sites)")
            print(f"      ✅ Total Supported Sites: {metrics_found['Total Supported Sites']} (not configured)")
            print(f"   ✅ Fallback mode working correctly in export!")
            return True
        else:
            print(f"   ❌ Fallback mode missing expected metrics")
            return False
        
    except Exception as e:
        print(f"   ❌ Fallback mode test failed: {str(e)}")
        return False

def test_export_comprehensive_integration():
    """Test that portfolio metrics integrate properly with comprehensive export"""
    print("\n🎯 Testing Comprehensive Export Integration...")
    
    # This verifies that the portfolio metrics don't break the existing export structure
    now = datetime.now()
    test_data = [
        {'Number': 'INC001', 'Site': 'Test Site', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)}
    ]
    
    test_df = pd.DataFrame(test_data)
    settings = Settings()
    settings.set('stability_analysis.total_supported_sites.count', 10)
    
    mock_root = Mock()
    mock_main_window = Mock()
    
    controller = AppController(mock_root, settings)
    controller.main_window = mock_main_window
    
    try:
        # Test all export sheet methods to ensure compatibility
        export_methods = [
            ("Stability Analytics", controller._create_stability_analytics_sheet),
            ("Pattern Analysis", controller._create_pattern_analysis_sheet),
            ("Insights", controller._create_insights_sheet),
            ("Critical Evidence", controller._create_critical_evidence_sheet),
            ("Synchronized Evidence", controller._create_synchronized_evidence_sheet)
        ]
        
        successful_exports = 0
        for sheet_name, method in export_methods:
            try:
                sheet_data = method(test_df)
                if sheet_data and len(sheet_data) > 0:
                    print(f"      ✅ {sheet_name}: {len(sheet_data)} rows generated")
                    successful_exports += 1
                else:
                    print(f"      ❌ {sheet_name}: No data generated")
            except Exception as e:
                print(f"      ❌ {sheet_name}: Failed - {str(e)}")
        
        if successful_exports == len(export_methods):
            print(f"   ✅ All {len(export_methods)} export sheets working with portfolio metrics!")
            return True
        else:
            print(f"   ❌ Only {successful_exports}/{len(export_methods)} export sheets working")
            return False
        
    except Exception as e:
        print(f"   ❌ Comprehensive export integration failed: {str(e)}")
        return False

def run_export_portfolio_tests():
    """Run all export portfolio integration tests"""
    print("📊 Testing Export System Portfolio Integration")
    print("=" * 70)
    
    test_results = {}
    
    # Test 1: Portfolio metrics in export
    test_results['export_portfolio_metrics'] = test_export_portfolio_metrics()
    
    # Test 2: Export fallback mode
    test_results['export_fallback_mode'] = test_export_fallback_mode()
    
    # Test 3: Comprehensive export integration
    test_results['export_comprehensive_integration'] = test_export_comprehensive_integration()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 EXPORT PORTFOLIO INTEGRATION SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL EXPORT PORTFOLIO TESTS PASSED!")
        print("\n✨ Export System Now Includes:")
        print("• ✅ Portfolio Stability: % of total supported sites with zero criticals")
        print("• ✅ Total Supported Sites: Dynamic configuration value")  
        print("• ✅ Sites with Zero Critical Incidents: Count of stable sites")
        print("• ✅ Portfolio Coverage: % of supported sites with any activity")
        print("• ✅ Backward Compatibility: Legacy metrics preserved")
        print("• ✅ Graceful Fallback: Works when portfolio mode disabled")
        print("\n📈 Excel Export Enhancement:")
        print("  📋 4 new portfolio-specific metrics added to Stability Analytics sheet")
        print("  🔧 Dynamic calculations based on configured total sites")
        print("  📊 Clear descriptions and status indicators for each metric")
        print("  ↩️ Graceful fallback to legacy behavior when needed")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed - review implementation")
        return False

if __name__ == "__main__":
    success = run_export_portfolio_tests()
    sys.exit(0 if success else 1)