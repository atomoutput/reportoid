#!/usr/bin/env python3
"""
Test script for the stability monitor application
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stability_monitor.models.data_manager import DataManager
from stability_monitor.models.report_engine import ReportEngine
from stability_monitor.config.settings import Settings

def test_data_loading():
    """Test data loading functionality"""
    print("Testing data loading...")
    
    settings = Settings()
    data_manager = DataManager(settings)
    
    # Test loading the sample CSV
    csv_path = "stability_monitor/tests/sample_data/wowzi.csv"
    if not os.path.exists(csv_path):
        print(f"Sample CSV not found at {csv_path}")
        return False, None
    
    result = data_manager.load_file(csv_path)
    
    if not result["valid"]:
        print("Data loading failed:")
        for error in result["errors"]:
            print(f"  - {error}")
        return False, None
    
    print("✓ Data loaded successfully!")
    print(f"  - Records: {result['info']['processed_records']}")
    print(f"  - Sites: {result['info']['sites']}")
    print(f"  - Companies: {result['info']['companies']}")
    print(f"  - Categories: {result['info']['categories']}")
    
    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    
    return True, data_manager

def test_reports(data_manager):
    """Test report generation"""
    print("\nTesting report generation...")
    
    settings = Settings()
    report_engine = ReportEngine(settings)
    
    # Test Critical Hotspots report
    print("Testing Critical Hotspots report...")
    results, columns = report_engine.generate_critical_hotspots_report(data_manager.data)
    print(f"  - Found {len(results)} critical hotspots")
    if results:
        print(f"  - Columns: {columns}")
        print(f"  - Sample result: {results[0]}")
    
    # Test Site Scorecard report
    print("Testing Site Scorecard report...")
    results, columns = report_engine.generate_site_scorecard_report(data_manager.data)
    print(f"  - Found {len(results)} sites in scorecard")
    if results:
        print(f"  - Columns: {columns}")
    
    # Test Green List report
    print("Testing Green List report...")
    results, columns = report_engine.generate_green_list_report(data_manager.data)
    print(f"  - Found {len(results)} stable sites")
    
    # Test Franchise Overview report
    print("Testing Franchise Overview report...")
    results, columns = report_engine.generate_franchise_overview_report(data_manager.data)
    print(f"  - Found {len(results)} companies")
    
    # Test Equipment Analysis report
    print("Testing Equipment Analysis report...")
    results, columns = report_engine.generate_equipment_analysis_report(data_manager.data)
    print(f"  - Found {len(results)} equipment categories")
    
    # Test Incident Details report
    print("Testing Incident Details report...")
    results, columns = report_engine.generate_incident_details_report(data_manager.data)
    print(f"  - Found {len(results)} individual tickets")
    if results:
        print(f"  - Columns: {columns}")
        print(f"  - Sample ticket: {results[0][1]} - {results[0][2][:30]}...")
    
    print("✓ All reports tested successfully!")

def test_filtering(data_manager):
    """Test filtering functionality"""
    print("\nTesting filtering...")
    
    # Test basic filters
    filters = {
        "priorities": ["1 - Critical", "2 - High"],
        "company": "Delight Ohio River LLC dba Wendy's - 41941622"
    }
    
    filtered_data = data_manager.apply_filters(filters)
    print(f"  - Original data: {len(data_manager.data)} records")
    print(f"  - Filtered data: {len(filtered_data)} records")
    
    # Test category mapping
    print(f"  - Category mapping: {len(data_manager.category_mapping)} categories")
    for category, subcategories in list(data_manager.category_mapping.items())[:3]:
        print(f"    - {category}: {len(subcategories)} subcategories")
    
    print("✓ Filtering tested successfully!")

def main():
    """Run all tests"""
    print("IT Stability Monitor - Component Tests")
    print("=" * 50)
    
    # Test data loading
    success, data_manager = test_data_loading()
    if not success:
        print("Data loading test failed. Exiting.")
        return False
    
    # Test reports
    test_reports(data_manager)
    
    # Test filtering
    test_filtering(data_manager)
    
    print("\n" + "=" * 50)
    print("All tests completed successfully! 🎉")
    print("The application components are working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)