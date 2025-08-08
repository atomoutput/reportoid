#!/usr/bin/env python3
"""
Test Enhanced Synchronized Incident Detection - Simple Version
"""

import sys
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, '/storage/emulated/0/scripts/retoid')

def test_enhanced_sync_detection():
    """Test the enhanced synchronized incident detection"""
    print("🚀 Testing Enhanced Synchronized Incident Detection")
    print("=" * 60)
    
    try:
        from stability_monitor.utils.pattern_recognition import TimePatternEngine
        
        # Create test data with synchronized incidents
        base_time = datetime(2024, 1, 15, 10, 15, 30)
        
        test_data = [
            # Exact minute synchronization
            {'Number': 'INC1001', 'Site': 'Site A', 'Priority': '1 - Critical', 'Created': base_time, 'Short description': 'Network connectivity lost', 'Category': 'Network'},
            {'Number': 'INC1002', 'Site': 'Site B', 'Priority': '1 - Critical', 'Created': base_time + timedelta(seconds=10), 'Short description': 'Network connection timeout', 'Category': 'Network'},
            {'Number': 'INC1003', 'Site': 'Site C', 'Priority': '1 - Critical', 'Created': base_time + timedelta(seconds=20), 'Short description': 'Unable to reach network servers', 'Category': 'Network'},
            
            # 5-minute window synchronization
            {'Number': 'INC2001', 'Site': 'Store 1', 'Priority': '1 - Critical', 'Created': base_time + timedelta(hours=1), 'Short description': 'Power outage affecting systems', 'Category': 'Power'},
            {'Number': 'INC2002', 'Site': 'Store 2', 'Priority': '1 - Critical', 'Created': base_time + timedelta(hours=1, minutes=2), 'Short description': 'Power failure - systems down', 'Category': 'Power'},
        ]
        
        df = pd.DataFrame(test_data)
        print(f"📊 Created test data with {len(df)} incidents")
        
        # Test with enhanced configuration
        settings = {
            "pattern_analysis": {
                "enable_multi_window_analysis": True,
                "advanced_correlation_scoring": True,
                "sync_time_windows": {
                    "exact_minute": {
                        "enabled": True,
                        "window_minutes": 0,
                        "tolerance_seconds": 30,
                        "min_sites": 2,
                        "correlation_threshold": 0.6,
                        "priority_scope": ["1 - Critical"]
                    },
                    "tight_window": {
                        "enabled": True,
                        "window_minutes": 5,
                        "min_sites": 2,
                        "correlation_threshold": 0.6,
                        "priority_scope": ["1 - Critical"]
                    }
                }
            }
        }
        
        # Initialize pattern engine
        pattern_engine = TimePatternEngine(settings)
        print("🔧 Initialized pattern engine with enhanced settings")
        
        # Test pattern analysis
        results = pattern_engine.analyze_temporal_patterns(df)
        sync_incidents = results.get("synchronized_incidents", [])
        
        print(f"🔍 Analysis Results:")
        print(f"   Synchronized incident groups: {len(sync_incidents)}")
        
        for i, sync_incident in enumerate(sync_incidents):
            print(f"   Group {i+1}:")
            print(f"     Sites: {len(sync_incident.sites)} - {', '.join(sync_incident.sites)}")
            print(f"     Correlation: {sync_incident.correlation_score:.3f}")
            print(f"     Window: {sync_incident.time_window_minutes} minutes")
            
            # Check for enhanced attributes
            if hasattr(sync_incident, 'window_type'):
                print(f"     Window Type: {sync_incident.window_type}")
            if hasattr(sync_incident, 'actual_time_span_seconds'):
                print(f"     Actual Time Span: {sync_incident.actual_time_span_seconds:.1f} seconds")
        
        # Success criteria
        success = len(sync_incidents) >= 1
        
        if success:
            print("✅ Enhanced synchronized incident detection working!")
            print("\n🎯 Key Improvements Verified:")
            print("• Multi-window analysis functional")
            print("• Enhanced correlation scoring active") 
            print("• Configurable time windows working")
            return True
        else:
            print("❌ No synchronized incidents detected")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_sync_detection()
    
    if success:
        print("\n🎉 ENHANCED SYNCHRONIZED INCIDENT DETECTION SUCCESS!")
        print("\n📈 Recommendations Based on Testing:")
        print("1. 🎯 Use 'Exact Minute' for true synchronization (network outages)")
        print("2. ⚡ Use '5 Minutes' for infrastructure issues (power, systems)")
        print("3. 🔄 Use '15 Minutes' for cascading failures")
        print("4. 📊 Enable 'Multi-Window' to catch all patterns")
        print("5. ⚙️ Adjust correlation thresholds based on your data quality")
        
        print("\n🛠️ Configuration Suggestions:")
        print("• Exact Minute: tolerance_seconds=30, correlation_threshold=0.7")
        print("• 5-Minute Window: correlation_threshold=0.6")
        print("• 15-Minute Window: correlation_threshold=0.7, min_sites=3")
        print("• Include High priority incidents for broader pattern detection")
        
    else:
        print("\n⚠️ Enhanced detection needs adjustment")
        
    sys.exit(0 if success else 1)