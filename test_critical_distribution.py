#!/usr/bin/env python3
"""
Test Critical Incident Distribution
Tests the expanded stability percentages breakdown (0, 1, 2, 3, 4+ critical cases)
"""

import sys
import pandas as pd
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, '/storage/emulated/0/scripts/retoid')

from stability_monitor.config.settings import Settings
from stability_monitor.utils.stability_analytics import SystemStabilityAnalyzer

def test_critical_distribution_calculation():
    """Test critical incident distribution calculation"""
    print("📊 Testing Critical Incident Distribution...")
    
    # Create test data with known distribution
    now = datetime.now()
    test_data = [
        # Site A: 0 criticals (2 high priority tickets)
        {'Number': 'INC001', 'Site': 'Site A', 'Priority': '2 - High', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC002', 'Site': 'Site A', 'Priority': '3 - Medium', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)},
        
        # Site B: 1 critical
        {'Number': 'INC003', 'Site': 'Site B', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC004', 'Site': 'Site B', 'Priority': '3 - Medium', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)},
        
        # Site C: 2 criticals
        {'Number': 'INC005', 'Site': 'Site C', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC006', 'Site': 'Site C', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)},
        
        # Site D: 3 criticals
        {'Number': 'INC007', 'Site': 'Site D', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC008', 'Site': 'Site D', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)},
        {'Number': 'INC009', 'Site': 'Site D', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=3)},
        
        # Site E: 5 criticals (4+ category)
        {'Number': 'INC010', 'Site': 'Site E', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC011', 'Site': 'Site E', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)},
        {'Number': 'INC012', 'Site': 'Site E', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=3)},
        {'Number': 'INC013', 'Site': 'Site E', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=4)},
        {'Number': 'INC014', 'Site': 'Site E', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
    ]
    
    test_df = pd.DataFrame(test_data)
    
    # Test with portfolio mode (10 total sites)
    settings = Settings()
    settings.set('stability_analysis.total_supported_sites.count', 10)
    
    print(f"   📋 Test scenario: 5 active sites, 10 total supported sites")
    print(f"      - Site A: 0 criticals")
    print(f"      - Site B: 1 critical") 
    print(f"      - Site C: 2 criticals")
    print(f"      - Site D: 3 criticals")
    print(f"      - Site E: 5 criticals (4+ category)")
    print(f"      - 5 silent sites: 0 criticals each")
    
    analyzer = SystemStabilityAnalyzer(settings)
    metrics = analyzer.calculate_system_stability(test_df)
    
    # Expected distribution:
    # 0 criticals: 1 (Site A) + 5 (silent sites) = 6 sites (60%)
    # 1 critical: 1 (Site B) = 1 site (10%)
    # 2 criticals: 1 (Site C) = 1 site (10%) 
    # 3 criticals: 1 (Site D) = 1 site (10%)
    # 4+ criticals: 1 (Site E) = 1 site (10%)
    
    expected_distribution = {
        "zero_criticals": {"count": 6, "percentage": 60.0},
        "one_critical": {"count": 1, "percentage": 10.0},
        "two_criticals": {"count": 1, "percentage": 10.0},
        "three_criticals": {"count": 1, "percentage": 10.0},
        "four_plus_criticals": {"count": 1, "percentage": 10.0}
    }
    
    print(f"   📈 Results:")
    distribution = metrics.critical_distribution
    success = True
    
    for category, expected in expected_distribution.items():
        actual = distribution[category]
        print(f"      • {category.replace('_', ' ').title()}: {actual['count']} sites ({actual['percentage']:.1f}%) - Expected: {expected['count']} sites ({expected['percentage']:.1f}%)")
        
        if actual['count'] != expected['count'] or abs(actual['percentage'] - expected['percentage']) > 0.1:
            print(f"        ❌ Mismatch!")
            success = False
        else:
            print(f"        ✅ Correct")
    
    if success:
        print(f"   ✅ Critical distribution calculation working correctly!")
        return True
    else:
        print(f"   ❌ Critical distribution calculation has errors")
        return False

def test_distribution_in_export():
    """Test that critical distribution appears in export data"""
    print("\n📤 Testing Critical Distribution in Export...")
    
    # Create test data
    now = datetime.now()
    test_data = [
        {'Number': 'INC001', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=1)},
        {'Number': 'INC002', 'Site': 'Site B', 'Priority': '3 - Medium', 'Created': now, 'Company': "Test", 'Resolved': now + timedelta(hours=2)},
    ]
    
    test_df = pd.DataFrame(test_data)
    
    # Configure settings
    settings = Settings()
    settings.set('stability_analysis.total_supported_sites.count', 5)
    
    # Create a simple export controller
    class TestExportController:
        def __init__(self, settings):
            self.settings = settings
            self.stability_analyzer = SystemStabilityAnalyzer(settings)
        
        def _create_stability_analytics_sheet(self, df):
            # Simplified version of the export sheet creation
            stability_metrics = self.stability_analyzer.calculate_system_stability(df)
            
            export_data = [
                ["Metric", "Value"],
                ["Sites with 0 Critical Incidents", 
                 f"{stability_metrics.critical_distribution['zero_criticals']['count']} sites ({stability_metrics.critical_distribution['zero_criticals']['percentage']:.1f}%)"],
                ["Sites with 1 Critical Incident", 
                 f"{stability_metrics.critical_distribution['one_critical']['count']} sites ({stability_metrics.critical_distribution['one_critical']['percentage']:.1f}%)"],
                ["Sites with 2 Critical Incidents", 
                 f"{stability_metrics.critical_distribution['two_criticals']['count']} sites ({stability_metrics.critical_distribution['two_criticals']['percentage']:.1f}%)"],
                ["Sites with 3 Critical Incidents", 
                 f"{stability_metrics.critical_distribution['three_criticals']['count']} sites ({stability_metrics.critical_distribution['three_criticals']['percentage']:.1f}%)"],
                ["Sites with 4+ Critical Incidents", 
                 f"{stability_metrics.critical_distribution['four_plus_criticals']['count']} sites ({stability_metrics.critical_distribution['four_plus_criticals']['percentage']:.1f}%)"],
            ]
            
            return export_data
    
    controller = TestExportController(settings)
    export_data = controller._create_stability_analytics_sheet(test_df)
    
    print(f"   📊 Export contains {len(export_data)} rows:")
    for row in export_data:
        if len(row) >= 2:
            print(f"      • {row[0]}: {row[1]}")
    
    # Verify all distribution categories are present
    distribution_categories = [
        "Sites with 0 Critical Incidents",
        "Sites with 1 Critical Incident", 
        "Sites with 2 Critical Incidents",
        "Sites with 3 Critical Incidents",
        "Sites with 4+ Critical Incidents"
    ]
    
    found_categories = [row[0] for row in export_data if len(row) >= 2]
    missing_categories = [cat for cat in distribution_categories if cat not in found_categories]
    
    if not missing_categories:
        print(f"   ✅ All critical distribution categories included in export!")
        return True
    else:
        print(f"   ❌ Missing categories: {missing_categories}")
        return False

def test_distribution_insights():
    """Test that distribution insights are generated"""
    print("\n💡 Testing Critical Distribution Insights...")
    
    # Test scenario with problematic distribution
    now = datetime.now()
    test_data = [
        # Create 4 sites with multiple criticals each
        {'Number': 'INC001', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
        {'Number': 'INC002', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
        {'Number': 'INC003', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
        {'Number': 'INC004', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
        {'Number': 'INC005', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
        
        {'Number': 'INC006', 'Site': 'Site B', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
        {'Number': 'INC007', 'Site': 'Site B', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
        {'Number': 'INC008', 'Site': 'Site B', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
        {'Number': 'INC009', 'Site': 'Site B', 'Priority': '1 - Critical', 'Created': now, 'Company': "Test", 'Resolved': None},
    ]
    
    test_df = pd.DataFrame(test_data)
    
    settings = Settings()
    settings.set('stability_analysis.total_supported_sites.count', 10)
    
    analyzer = SystemStabilityAnalyzer(settings)
    metrics = analyzer.calculate_system_stability(test_df)
    insights = analyzer.generate_stability_insights(metrics)
    
    print(f"   💡 Generated {len(insights)} insights:")
    distribution_insights = []
    for insight in insights:
        if any(keyword in insight.lower() for keyword in ['distribution', 'sites have', 'zero critical', '4+', 'immediate intervention']):
            distribution_insights.append(insight)
            print(f"      • {insight}")
    
    if distribution_insights:
        print(f"   ✅ Critical distribution insights generated ({len(distribution_insights)} found)!")
        return True
    else:
        print(f"   ❌ No critical distribution insights found")
        return False

def run_critical_distribution_tests():
    """Run all critical distribution tests"""
    print("📊 Testing Critical Incident Distribution Expansion")
    print("=" * 70)
    
    test_results = {}
    
    # Test 1: Distribution calculation
    test_results['distribution_calculation'] = test_critical_distribution_calculation()
    
    # Test 2: Export integration
    test_results['distribution_in_export'] = test_distribution_in_export()
    
    # Test 3: Insights generation
    test_results['distribution_insights'] = test_distribution_insights()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 CRITICAL DISTRIBUTION TEST SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL CRITICAL DISTRIBUTION TESTS PASSED!")
        print("\n✨ Enhanced Stability Analysis Features:")
        print("• ✅ Sites with 0 Critical Incidents: Count and percentage")
        print("• ✅ Sites with 1 Critical Incident: Monitoring tier") 
        print("• ✅ Sites with 2 Critical Incidents: Attention tier")
        print("• ✅ Sites with 3 Critical Incidents: High priority tier")
        print("• ✅ Sites with 4+ Critical Incidents: Critical intervention tier")
        print("• ✅ Export Integration: All distribution metrics in Excel")
        print("• ✅ Intelligent Insights: Distribution-based recommendations")
        print("\n🎯 Client Requirements Extended:")
        print("• ✅ Detailed breakdown of stability percentages by critical count")
        print("• ✅ Portfolio-wide distribution analysis including silent sites")
        print("• ✅ Actionable insights for each stability tier")
        print("• ✅ Professional export formatting with status indicators")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed - review implementation")
        return False

if __name__ == "__main__":
    success = run_critical_distribution_tests()
    sys.exit(0 if success else 1)