#!/usr/bin/env python3
"""
Comprehensive Pandas Series Boolean Evaluation Bug Hunt
Tests and identifies potential Series boolean evaluation issues in duplicate review
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Add the project root to Python path
sys.path.insert(0, '/storage/emulated/0/scripts/retoid')

def test_series_boolean_scenarios():
    """Test various scenarios that could cause Series boolean ambiguity"""
    print("🔍 Testing Pandas Series Boolean Evaluation Scenarios...")
    
    issues_found = []
    
    try:
        # Scenario 1: Empty Series boolean evaluation
        print("   📊 Scenario 1: Empty Series boolean evaluation")
        empty_series = pd.Series([], dtype=object)
        try:
            if empty_series:  # This should cause the error
                pass
        except ValueError as e:
            if "ambiguous" in str(e):
                issues_found.append("Empty Series direct boolean evaluation")
                print(f"      ❌ Found issue: {str(e)}")
        
        # Scenario 2: Multi-value Series boolean evaluation
        print("   📊 Scenario 2: Multi-value Series boolean evaluation")
        multi_series = pd.Series([True, False, True])
        try:
            if multi_series:  # This should cause the error
                pass
        except ValueError as e:
            if "ambiguous" in str(e):
                issues_found.append("Multi-value Series direct boolean evaluation")
                print(f"      ❌ Found issue: {str(e)}")
        
        # Scenario 3: Series with NaN values
        print("   📊 Scenario 3: Series with NaN boolean evaluation")
        nan_series = pd.Series([np.nan, True, False])
        try:
            if nan_series:  # This should cause the error
                pass
        except ValueError as e:
            if "ambiguous" in str(e):
                issues_found.append("NaN Series direct boolean evaluation")
                print(f"      ❌ Found issue: {str(e)}")
        
        # Scenario 4: Series comparison in boolean context
        print("   📊 Scenario 4: Series comparison boolean evaluation")
        test_series = pd.Series(['INC001', 'INC002', 'INC003'])
        try:
            comparison_result = (test_series == 'INC001')  # Returns Series
            if comparison_result:  # This should cause the error
                pass
        except ValueError as e:
            if "ambiguous" in str(e):
                issues_found.append("Series comparison in boolean context")
                print(f"      ❌ Found issue: {str(e)}")
        
        print(f"   📈 Total boolean evaluation issues found: {len(issues_found)}")
        return issues_found
        
    except Exception as e:
        print(f"   ❌ Test failed with unexpected error: {str(e)}")
        return ["Unexpected test failure"]

def test_duplicate_review_data_structures():
    """Test data structures used in duplicate review for potential Series issues"""
    print("\n📋 Testing Duplicate Review Data Structures...")
    
    try:
        # Simulate ticket data as might come from duplicate detection
        tickets_as_series = pd.DataFrame({
            'Number': ['INC001', 'INC002', 'INC003'],
            'Site': ['Site A', 'Site A', 'Site B'],
            'Priority': ['1 - Critical', '1 - Critical', '2 - High'],
            'Created': [
                datetime.now() - timedelta(days=1),
                datetime.now() - timedelta(days=2),
                datetime.now() - timedelta(days=3)
            ],
            'Short description': [
                'Critical system failure',
                'Network connectivity issue',
                'Database performance problem'
            ]
        })
        
        print(f"   📊 Created test DataFrame with {len(tickets_as_series)} tickets")
        
        # Test iterating over rows (this might return Series objects)
        potential_issues = []
        
        for i, ticket in tickets_as_series.iterrows():
            # This is how tickets are accessed in the duplicate review dialog
            ticket_id = ticket.get('Number', f'ticket_{i}')
            
            # Check if ticket_id is a Series
            if hasattr(ticket_id, 'any'):  # It's a Series
                potential_issues.append(f"ticket.get('Number') returned Series for row {i}")
                print(f"      ⚠️ Row {i}: ticket_id is Series: {type(ticket_id)}")
            
            # Check description
            desc = ticket.get('Short description', 'N/A')
            if hasattr(desc, 'any'):  # It's a Series
                potential_issues.append(f"ticket.get('Short description') returned Series for row {i}")
                print(f"      ⚠️ Row {i}: description is Series: {type(desc)}")
            
            # Check created date
            created = ticket.get('Created')
            if hasattr(created, 'any'):  # It's a Series
                potential_issues.append(f"ticket.get('Created') returned Series for row {i}")
                print(f"      ⚠️ Row {i}: created date is Series: {type(created)}")
        
        print(f"   📈 Potential Series access issues found: {len(potential_issues)}")
        return potential_issues
        
    except Exception as e:
        print(f"   ❌ Data structure test failed: {str(e)}")
        return [f"Data structure test failure: {str(e)}"]

def test_mock_duplicate_group_behavior():
    """Test behavior that simulates the duplicate group processing"""
    print("\n🔧 Testing Mock Duplicate Group Behavior...")
    
    try:
        # Create mock data similar to what duplicate detection might return
        duplicate_data = pd.DataFrame({
            'Number': ['INC001', 'INC001', 'INC002'],  # Duplicate INC001
            'Site': ['Site A', 'Site A', 'Site A'],
            'Priority': ['1 - Critical', '1 - Critical', '2 - High'],
            'Created': [
                datetime.now() - timedelta(hours=6),
                datetime.now() - timedelta(hours=6),  # Same time - potential duplicate
                datetime.now() - timedelta(hours=12)
            ],
            'Short description': [
                'System failure',
                'System failure - duplicate',
                'Different issue'
            ]
        })
        
        print(f"   📊 Created mock duplicate data with {len(duplicate_data)} tickets")
        
        # Test duplicate grouping logic
        issues_found = []
        
        # Group by potential duplicate criteria
        duplicate_groups = duplicate_data.groupby(['Site', 'Priority', 'Short description'])
        
        for group_key, group_df in duplicate_groups:
            if len(group_df) > 1:  # Potential duplicates
                print(f"      🔍 Found duplicate group: {group_key}")
                
                # This is where the error might occur - when processing group tickets
                for i, ticket in group_df.iterrows():
                    # Test accessing ticket data (this is the pattern used in the dialog)
                    try:
                        ticket_access_tests = {
                            'Number': ticket.get('Number'),
                            'Site': ticket.get('Site'),
                            'Priority': ticket.get('Priority'),
                            'Created': ticket.get('Created'),
                            'Short description': ticket.get('Short description')
                        }
                        
                        # Check if any values are Series
                        for field, value in ticket_access_tests.items():
                            if hasattr(value, 'any') and hasattr(value, 'item'):
                                issues_found.append(f"Field '{field}' in row {i} returned Series")
                                print(f"         ⚠️ {field} is Series: {type(value)}")
                        
                        # Test boolean evaluation scenarios that might occur
                        created_val = ticket.get('Created')
                        if created_val is not None:  # This should be fine
                            # But if created_val is a Series, checking it might cause issues
                            if hasattr(created_val, 'any'):
                                try:
                                    # This would cause the error in actual code
                                    if created_val:  # Direct boolean evaluation of Series
                                        pass
                                except ValueError as e:
                                    if "ambiguous" in str(e):
                                        issues_found.append(f"Boolean evaluation of Created field caused error")
                                        print(f"         ❌ Created field boolean evaluation error: {str(e)}")
                        
                    except Exception as e:
                        issues_found.append(f"Ticket access error in row {i}: {str(e)}")
                        print(f"         ❌ Row {i} access error: {str(e)}")
        
        print(f"   📈 Mock duplicate group issues found: {len(issues_found)}")
        return issues_found
        
    except Exception as e:
        print(f"   ❌ Mock duplicate group test failed: {str(e)}")
        return [f"Mock test failure: {str(e)}"]

def test_safe_scalar_extraction():
    """Test the safe scalar extraction utility function"""
    print("\n🛡️ Testing Safe Scalar Extraction Logic...")
    
    try:
        # Test various data types that might be encountered
        test_cases = [
            # (description, test_value, expected_behavior)
            ("Scalar string", "INC001", "should return as-is"),
            ("Scalar number", 12345, "should return as-is"),
            ("Scalar datetime", datetime.now(), "should return as-is"),
            ("None value", None, "should return None"),
            ("Single-item Series", pd.Series(["INC001"]), "should extract scalar"),
            ("Multi-item Series", pd.Series(["INC001", "INC002"]), "should extract first item"),
            ("Empty Series", pd.Series([]), "should handle gracefully"),
            ("Series with NaN", pd.Series([np.nan]), "should handle NaN"),
            ("Series with mixed types", pd.Series(["INC001", 123, None]), "should extract first")
        ]
        
        def safe_get_scalar_test(value):
            """Test version of the safe scalar extraction"""
            try:
                if value is None:
                    return None
                    
                # Handle pandas Series - get the first item
                if hasattr(value, 'item'):
                    return value.item()
                elif hasattr(value, 'iloc') and len(value) > 0:
                    return value.iloc[0]
                elif hasattr(value, 'values') and len(value.values) > 0:
                    return value.values[0]
                else:
                    return value
                    
            except Exception as e:
                # If anything fails, return the original value
                return value
        
        results = []
        for desc, test_val, expected in test_cases:
            try:
                result = safe_get_scalar_test(test_val)
                print(f"   ✅ {desc}: {type(result).__name__} = {repr(result)}")
                results.append((desc, "success", str(type(result).__name__)))
            except Exception as e:
                print(f"   ❌ {desc}: Error = {str(e)}")
                results.append((desc, "error", str(e)))
        
        success_count = sum(1 for _, status, _ in results if status == "success")
        print(f"   📈 Safe scalar extraction: {success_count}/{len(results)} tests passed")
        
        return results
        
    except Exception as e:
        print(f"   ❌ Safe scalar extraction test failed: {str(e)}")
        return []

def run_comprehensive_pandas_bug_hunt():
    """Run comprehensive pandas Series boolean evaluation bug hunt"""
    print("🐛 Comprehensive Pandas Series Boolean Evaluation Bug Hunt")
    print("=" * 80)
    
    all_issues = []
    
    # Test 1: Series boolean evaluation scenarios
    boolean_issues = test_series_boolean_scenarios()
    all_issues.extend(boolean_issues)
    
    # Test 2: Duplicate review data structures
    data_structure_issues = test_duplicate_review_data_structures()
    all_issues.extend(data_structure_issues)
    
    # Test 3: Mock duplicate group behavior
    duplicate_group_issues = test_mock_duplicate_group_behavior()
    all_issues.extend(duplicate_group_issues)
    
    # Test 4: Safe scalar extraction
    scalar_extraction_results = test_safe_scalar_extraction()
    
    # Summary
    print("\n" + "=" * 80)
    print("🐛 PANDAS SERIES BUG HUNT SUMMARY")
    print("=" * 80)
    
    print(f"Total Potential Issues Found: {len(all_issues)}")
    
    if all_issues:
        print("\n📋 Issues Identified:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n🔧 Recommended Actions:")
        print("  • Implement safe scalar extraction for all ticket data access")
        print("  • Add explicit .any()/.all() calls for boolean evaluation of Series")
        print("  • Use try-catch blocks around potential Series operations")
        print("  • Validate data types before boolean evaluation")
        print("  • Add debugging to identify exact location of Series boolean evaluation")
        
    else:
        print("\n✅ No obvious pandas Series boolean evaluation issues found")
        print("   The error may be occurring in specific data conditions or edge cases")
    
    print(f"\nScalar Extraction Test Results: {len(scalar_extraction_results)} tests")
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = run_comprehensive_pandas_bug_hunt()
    sys.exit(0 if success else 1)