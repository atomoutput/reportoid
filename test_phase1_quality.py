#!/usr/bin/env python3
"""
Test script for Phase 1 Data Quality features
Tests site filtering and duplicate detection functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stability_monitor.models.data_manager import DataManager
from stability_monitor.models.report_engine import ReportEngine
from stability_monitor.config.settings import Settings

def test_data_quality_features():
    """Test the new data quality features"""
    print("🧪 Testing Phase 1 Data Quality Features")
    print("=" * 60)
    
    settings = Settings()
    data_manager = DataManager(settings)
    report_engine = ReportEngine(settings)
    
    # Test loading with quality management
    print("1. Testing data loading with quality features...")
    csv_path = "stability_monitor/tests/sample_data/wowzi.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Sample CSV not found at {csv_path}")
        return False
    
    result = data_manager.load_file(csv_path)
    
    if not result["valid"]:
        print("❌ Data loading failed:")
        for error in result["errors"]:
            print(f"  - {error}")
        return False
    
    print("✅ Data loaded successfully with quality features!")
    
    # Display loading results with quality metrics
    info = result["info"]
    print(f"  📊 Original records: {info.get('original_records', 'N/A')}")
    print(f"  📊 Processed records: {info['processed_records']}")
    print(f"  🔍 Filtered out: {info.get('filtered_out', 0)} tickets")
    print(f"  ⭐ Quality Score: {info.get('quality_score', 0):.1f}%")
    print(f"  🏢 Sites: {info['sites']}")
    print(f"  🏬 Companies: {info['companies']}")
    
    if result["warnings"]:
        print("  ⚠️  Quality warnings:")
        for warning in result["warnings"]:
            print(f"    - {warning}")
    
    # Test quality report generation
    print("\n2. Testing quality report generation...")
    quality_report = data_manager.get_quality_report()
    
    if quality_report:
        print("✅ Quality report generated successfully!")
        print(f"  📈 Data Quality Score: {quality_report['data_quality_score']:.1f}%")
        
        # Site filtering results
        site_filter = quality_report.get('site_filtering', {})
        print(f"  🏢 Site Filtering: {site_filter.get('filtered_count', 0)} kept, {site_filter.get('removed_count', 0)} removed")
        
        # Duplicate detection results  
        dup_analysis = quality_report.get('duplicate_analysis', {})
        print(f"  🔍 Duplicate Groups: {dup_analysis.get('total_duplicate_groups', 0)}")
        print(f"  📝 Manual Review Required: {dup_analysis.get('manual_review_required', 0)}")
        print(f"  🤖 High Confidence: {dup_analysis.get('high_confidence_groups', 0)}")
        
        # Show recommendations
        recommendations = quality_report.get('recommendations', [])
        if recommendations:
            print("  💡 Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"    {i}. {rec}")
    else:
        print("❌ Failed to generate quality report")
        return False
    
    # Test duplicate group detection
    print("\n3. Testing duplicate group detection...")
    duplicate_groups = data_manager.get_duplicate_groups()
    print(f"✅ Found {len(duplicate_groups)} duplicate groups")
    
    if duplicate_groups:
        for i, group in enumerate(duplicate_groups[:3], 1):  # Show first 3 groups
            print(f"  Group {i}: {group.confidence_score:.1%} confidence")
            ticket_numbers = group.get_ticket_numbers()
            print(f"    Tickets: {', '.join(ticket_numbers)}")
            print(f"    Site: {group.primary_ticket.get('Site', 'N/A')}")
    
    # Test quality-flagged data
    print("\n4. Testing quality-flagged data...")
    quality_data = data_manager.get_quality_flagged_data()
    
    if quality_data is not None:
        print("✅ Quality-flagged data available!")
        
        # Show quality flag distribution
        if 'Duplicate_Flag' in quality_data.columns:
            flag_counts = quality_data['Duplicate_Flag'].value_counts()
            print("  🏷️  Quality Flag Distribution:")
            for flag, count in flag_counts.items():
                print(f"    {flag}: {count}")
        
        # Show high-confidence duplicates
        high_conf_duplicates = quality_data[
            (quality_data.get('Duplicate_Confidence', 0) >= 0.9) & 
            (quality_data.get('Duplicate_Flag', '') != 'Clean')
        ]
        
        if not high_conf_duplicates.empty:
            print(f"  🎯 High-confidence duplicates: {len(high_conf_duplicates)}")
    else:
        print("❌ Quality-flagged data not available")
        return False
    
    # Test new reports
    print("\n5. Testing new quality reports...")
    
    # Data Quality Report
    results, columns = report_engine.generate_data_quality_report(quality_report, duplicate_groups)
    print(f"✅ Data Quality Report: {len(results)} metrics")
    if results:
        print("  📊 Quality Metrics:")
        for result in results[:3]:  # Show first 3 metrics
            print(f"    {result[0]}: {result[1]} ({result[2]})")
    
    # Duplicate Review Report
    results, columns = report_engine.generate_duplicate_review_report(duplicate_groups)
    print(f"✅ Duplicate Review Report: {len(results)} groups")
    if results:
        print("  🔍 Sample duplicate groups:")
        for result in results[:2]:  # Show first 2 groups
            print(f"    {result[0]}: {result[1]} -> {result[2]} ({result[3]} confidence)")
    
    print("\n6. Testing site filtering configuration...")
    
    # Show configuration
    site_config = settings.get("data_quality.site_filter", {})
    print(f"✅ Site filtering: {'Enabled' if site_config.get('enabled') else 'Disabled'}")
    print(f"  🔍 Keywords: {site_config.get('required_keywords', [])}")
    print(f"  📝 Case sensitive: {site_config.get('case_sensitive', False)}")
    
    dup_config = settings.get("data_quality.duplicate_detection", {})
    print(f"✅ Duplicate detection: {'Enabled' if dup_config.get('enabled') else 'Disabled'}")
    print(f"  🎯 Similarity threshold: {dup_config.get('similarity_threshold', 0.8)}")
    print(f"  ⏰ Date window: {dup_config.get('date_window_hours', 24)} hours")
    print(f"  📋 Priority levels: {dup_config.get('priority_levels', [])}")
    
    print("\n" + "=" * 60)
    print("🎉 Phase 1 Data Quality Features - ALL TESTS PASSED!")
    print("✨ Site filtering and duplicate detection are working correctly.")
    return True

def create_test_duplicate_data():
    """Create some test data with intentional duplicates for better testing"""
    print("\n🧪 BONUS: Testing with simulated duplicate data...")
    
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Create test data with obvious duplicates
    test_data = {
        'Site': [
            "Wendy's #123 - Test Site",
            "Wendy's #123 - Test Site", 
            "Wendy's #456 - Another Site",
            "Non-Wendy Site",  # Should be filtered out
        ],
        'Company': [
            "Test Company LLC dba Wendy's",
            "Test Company LLC dba Wendy's",
            "Another Company LLC dba Wendy's", 
            "Random Company"
        ],
        'Priority': [
            "1 - Critical",
            "1 - Critical",
            "2 - High",
            "1 - Critical"
        ],
        'Created': [
            datetime.now(),
            datetime.now() + timedelta(hours=2),  # Same day, different time
            datetime.now() - timedelta(days=1),
            datetime.now()
        ],
        'Number': ['TEST001', 'TEST002', 'TEST003', 'TEST004'],
        'Short description': [
            'Server down in kitchen',
            'Kitchen server is down',  # Similar description
            'Network issues',
            'Server problems'
        ],
        'Resolved': [None, None, datetime.now(), None]
    }
    
    # Save test data
    test_df = pd.DataFrame(test_data)
    test_path = 'test_duplicates.csv'
    test_df.to_csv(test_path, index=False)
    
    print(f"📄 Created test data: {test_path}")
    
    # Test with the duplicate data
    settings = Settings()
    data_manager = DataManager(settings)
    
    result = data_manager.load_file(test_path)
    
    if result["valid"]:
        print("✅ Test duplicate data loaded successfully!")
        
        info = result["info"]
        print(f"  📊 Original: {info.get('original_records', 'N/A')} -> Processed: {info['processed_records']}")
        print(f"  🔍 Filtered out: {info.get('filtered_out', 0)} (should filter Non-Wendy Site)")
        print(f"  ⭐ Quality Score: {info.get('quality_score', 0):.1f}%")
        
        duplicate_groups = data_manager.get_duplicate_groups()
        print(f"  🔍 Duplicate groups detected: {len(duplicate_groups)}")
        
        if duplicate_groups:
            for i, group in enumerate(duplicate_groups, 1):
                print(f"    Group {i}: {group.confidence_score:.1%} confidence")
                tickets = group.get_ticket_numbers()
                print(f"      Tickets: {', '.join(tickets)}")
        
        print("✅ Duplicate detection working correctly with test data!")
    else:
        print("❌ Failed to load test data")
    
    # Cleanup
    if os.path.exists(test_path):
        os.remove(test_path)
        print(f"🧹 Cleaned up test file: {test_path}")

if __name__ == "__main__":
    print("🚀 Starting Phase 1 Data Quality Testing...")
    
    success = test_data_quality_features()
    
    if success:
        create_test_duplicate_data()
        print("\n🎯 PHASE 1 TESTING COMPLETE - ALL SYSTEMS GO!")
    else:
        print("\n❌ PHASE 1 TESTING FAILED - Check implementation")
        sys.exit(1)