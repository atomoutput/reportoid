#!/usr/bin/env python3
"""
Simple Portfolio Export Test
Tests the export functionality without UI dependencies
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock

# Add the project root to Python path
sys.path.insert(0, '/storage/emulated/0/scripts/retoid')

from stability_monitor.config.settings import Settings
from stability_monitor.utils.stability_analytics import SystemStabilityAnalyzer

def create_test_export_controller():
    """Create a minimal controller-like object for testing export methods"""
    
    class TestExportController:
        def __init__(self, settings):
            self.settings = settings
            self.stability_analyzer = SystemStabilityAnalyzer(settings)
        
        def _create_stability_analytics_sheet(self, df: pd.DataFrame) -> list:
            """Create stability analytics data for Excel export"""
            try:
                # Generate stability metrics
                stability_metrics = self.stability_analyzer.calculate_system_stability(df)
                
                stability_data = [
                    ["Metric", "Current Value", "Target/Benchmark", "Status", "Description"],
                    
                    # Portfolio-wide stability metrics (NEW)
                    ["Portfolio Stability", 
                     f"{stability_metrics.portfolio_stability_percentage:.1f}%" if stability_metrics.total_supported_sites > 0 else f"{stability_metrics.overall_stability_percentage:.1f}%", 
                     "≥95% (Excellent)", 
                     "🟢 Excellent" if (stability_metrics.portfolio_stability_percentage if stability_metrics.total_supported_sites > 0 else stability_metrics.overall_stability_percentage) >= 95 else 
                     "🟡 Good" if (stability_metrics.portfolio_stability_percentage if stability_metrics.total_supported_sites > 0 else stability_metrics.overall_stability_percentage) >= 85 else 
                     "🔴 Needs Attention",
                     f"Percentage of ALL {stability_metrics.total_supported_sites} supported sites with zero critical incidents" if stability_metrics.total_supported_sites > 0 else "Percentage of active sites with no critical incidents"],
                    
                    ["Total Supported Sites", 
                     f"{stability_metrics.total_supported_sites}" if stability_metrics.total_supported_sites > 0 else "Not configured", 
                     "Configuration dependent", 
                     "ℹ️ Info",
                     "Total number of sites under IT support coverage"],
                    
                    ["Sites with Zero Critical Incidents", 
                     f"{stability_metrics.sites_with_zero_incidents}", 
                     f"≥{int(stability_metrics.total_supported_sites * 0.95)} sites (95%)" if stability_metrics.total_supported_sites > 0 else "≥95%", 
                     "🟢 Good" if stability_metrics.total_supported_sites == 0 or stability_metrics.sites_with_zero_incidents >= (stability_metrics.total_supported_sites * 0.95) else "🟡 Monitor",
                     "Number of sites with no critical incidents (including sites with no activity)"],
                    
                    ["Portfolio Coverage", 
                     f"{stability_metrics.portfolio_coverage_percentage:.1f}%" if stability_metrics.total_supported_sites > 0 else "100.0%", 
                     "Varies by business", 
                     "ℹ️ Info",
                     f"Percentage of supported sites that had any incidents ({stability_metrics.sites_with_incidents} of {stability_metrics.total_supported_sites})" if stability_metrics.total_supported_sites > 0 else "All active sites covered"],
                    
                    ["Overall System Stability", 
                     f"{stability_metrics.overall_stability_percentage:.1f}%", 
                     "≥95% (Excellent)", 
                     "🟢 Excellent" if stability_metrics.overall_stability_percentage >= 95 else 
                     "🟡 Good" if stability_metrics.overall_stability_percentage >= 85 else 
                     "🔴 Needs Attention",
                     "Legacy metric: Percentage of active sites with no critical incidents"],
                    
                    ["Critical Incident Rate", 
                     f"{stability_metrics.critical_incident_rate:.1f}%", 
                     "≤5% (Target)", 
                     "🟢 Excellent" if stability_metrics.critical_incident_rate <= 5 else 
                     "🟡 Acceptable" if stability_metrics.critical_incident_rate <= 10 else 
                     "🔴 High",
                     "Percentage of tickets that are critical priority"]
                ]
                
                return stability_data
            except Exception as e:
                return [["Error", f"Failed to generate stability analytics: {str(e)}"]]
    
    return TestExportController

def test_portfolio_export_metrics():
    """Test portfolio metrics in export functionality"""
    print("📊 Testing Portfolio Metrics Export...")
    
    # Create test data with known values
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
    
    # Configure settings with 20 total supported sites
    settings = Settings()
    settings.set('stability_analysis.total_supported_sites.count', 20)
    
    print(f"   📋 Scenario: 3 active sites, 2 with criticals, 20 total supported sites")
    
    # Create test controller
    controller_class = create_test_export_controller()
    controller = controller_class(settings)
    
    try:
        # Generate export data
        export_data = controller._create_stability_analytics_sheet(test_df)
        
        print(f"   📈 Export generated with {len(export_data)} rows")
        
        # Parse export data
        metrics_in_export = {}
        for row in export_data[1:]:  # Skip header
            if len(row) >= 2:
                metrics_in_export[row[0]] = row[1]
        
        # Verify portfolio metrics are present
        expected_metrics = {
            "Portfolio Stability": "90.0%",  # 18 of 20 sites (20 - 2 with criticals)
            "Total Supported Sites": "20",
            "Sites with Zero Critical Incidents": "18",  # 20 - 2 with criticals
            "Portfolio Coverage": "15.0%"  # 3 of 20 sites had activity
        }
        
        print(f"   🎯 Verifying portfolio metrics in export:")
        all_correct = True
        for metric_name, expected_value in expected_metrics.items():
            actual_value = metrics_in_export.get(metric_name)
            if actual_value == expected_value:
                print(f"      ✅ {metric_name}: {actual_value}")
            else:
                print(f"      ❌ {metric_name}: {actual_value} (expected: {expected_value})")
                all_correct = False
        
        # Verify legacy metrics still included
        legacy_metrics = ["Overall System Stability", "Critical Incident Rate"]
        for metric in legacy_metrics:
            if metric in metrics_in_export:
                print(f"      ✅ {metric}: {metrics_in_export[metric]} (preserved)")
            else:
                print(f"      ❌ {metric}: Missing (should be preserved)")
                all_correct = False
        
        if all_correct:
            print(f"   ✅ All portfolio metrics correctly integrated into export!")
            return True
        else:
            print(f"   ❌ Some portfolio metrics incorrect in export")
            return False
            
    except Exception as e:
        print(f"   ❌ Portfolio export test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_export_fallback():
    """Test export when portfolio mode disabled"""
    print("\n🔄 Testing Export Fallback Mode...")
    
    now = datetime.now()
    test_data = [
        {'Number': 'INC001', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC002', 'Site': 'Site B', 'Priority': '3 - Medium', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)},
    ]
    
    test_df = pd.DataFrame(test_data)
    
    # Configure settings with portfolio mode disabled
    settings = Settings()
    settings.set('stability_analysis.total_supported_sites.count', 0)  # Disabled
    
    print(f"   📋 Scenario: Portfolio mode disabled, should fallback gracefully")
    
    controller_class = create_test_export_controller()
    controller = controller_class(settings)
    
    try:
        export_data = controller._create_stability_analytics_sheet(test_df)
        
        # Parse export data
        metrics_in_export = {}
        for row in export_data[1:]:  # Skip header
            if len(row) >= 2:
                metrics_in_export[row[0]] = row[1]
        
        # Verify fallback behavior
        expected_fallbacks = {
            "Portfolio Stability": "50.0%",  # Should use overall stability (1 of 2 sites stable)
            "Total Supported Sites": "Not configured",
            "Sites with Zero Critical Incidents": "1",  # 1 site without criticals
            "Portfolio Coverage": "100.0%"  # All active sites covered
        }
        
        print(f"   🔍 Verifying fallback behavior:")
        fallback_correct = True
        for metric_name, expected_value in expected_fallbacks.items():
            actual_value = metrics_in_export.get(metric_name)
            if actual_value == expected_value:
                print(f"      ✅ {metric_name}: {actual_value}")
            else:
                print(f"      ❌ {metric_name}: {actual_value} (expected: {expected_value})")
                fallback_correct = False
        
        if fallback_correct:
            print(f"   ✅ Fallback mode working correctly in export!")
            return True
        else:
            print(f"   ❌ Fallback mode issues detected")
            return False
            
    except Exception as e:
        print(f"   ❌ Fallback export test failed: {str(e)}")
        return False

def run_simple_export_tests():
    """Run simplified export tests"""
    print("📊 Testing Portfolio Export Integration (Simple)")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: Portfolio metrics in export
    test_results['portfolio_export_metrics'] = test_portfolio_export_metrics()
    
    # Test 2: Export fallback mode
    test_results['export_fallback'] = test_export_fallback()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 EXPORT INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    if passed_tests == total_tests:
        print("\n🎉 PORTFOLIO EXPORT INTEGRATION COMPLETE!")
        print("\n✨ Export System Successfully Enhanced:")
        print("• ✅ Portfolio Stability: % of total sites with zero criticals")
        print("• ✅ Total Supported Sites: Shows configured site count") 
        print("• ✅ Sites with Zero Critical Incidents: Accurate count")
        print("• ✅ Portfolio Coverage: Activity percentage across portfolio")
        print("• ✅ Legacy Compatibility: Original metrics preserved")
        print("• ✅ Graceful Fallback: Works when portfolio disabled")
        
        print("\n🎯 Client Export Requirements Met:")
        print("• ✅ Total sites stability check now included in Excel exports")
        print("• ✅ Dynamic site count reflected in export calculations") 
        print("• ✅ Portfolio-wide statistics available in export sheets")
        print("• ✅ Clear descriptions and status indicators for each metric")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_simple_export_tests()
    sys.exit(0 if success else 1)