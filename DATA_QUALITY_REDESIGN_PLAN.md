# Data Quality Management - Redesign Plan

## 🎯 **Issues Identified**

### **1. Duplicate Detection Logic Error**
**Current Issue**: Duplicate detection is global (cross-site) instead of site-specific
**Problem**: Looking for duplicates across different sites when we should focus on duplicates within individual sites only
**Impact**: Irrelevant duplicate groups, wasted review time

### **2. Missing Ticket Selection & Merge Functionality**
**Current Issue**: No way to select specific tickets within a duplicate group for merging
**Problem**: Interface shows duplicate groups but can't granularly select which tickets to merge
**Impact**: Cannot perform actual data consolidation

### **3. No Data Reprocessing After Manual Review**
**Current Issue**: Manual review decisions don't affect the underlying dataset
**Problem**: Merge/dismiss actions are logged but don't update statistics and reports
**Impact**: Reports still show merged tickets as separate entries

### **4. Analytics Reports Lack Detail Views**
**Current Issue**: Stability Dashboard, Pattern Analysis, Insights show summary only
**Problem**: No drill-down to see underlying data, evidence, or specific tickets
**Impact**: Cannot verify findings or take action on insights

### **5. Analytics Not Integrated with Exports**
**Current Issue**: Advanced analytics are not included in comprehensive exports
**Problem**: Cannot share or document analytical findings
**Impact**: Insights are trapped in the application

---

## 📋 **Detailed Implementation Plan**

### **PHASE 1: Fix Duplicate Detection (Site-Specific)**

#### **1.1 Modify Duplicate Detection Logic**
```python
# Current (WRONG): Cross-site detection
site_mask = pd.Series([True] * len(df), index=df.index)

# New (CORRECT): Same-site only detection
site_mask = df['Site'] == ticket_site
```

**Changes Required:**
- Remove `allow_cross_site` configuration option
- Force duplicate detection to be site-specific only
- Update confidence scoring to focus on same-site similarity factors
- Modify UI to show site name prominently in duplicate groups

#### **1.2 Update Similarity Scoring for Same-Site Logic**
```python
# New weight distribution for same-site duplicates:
weights = {
    'description': 0.6,  # Increase description weight (was 0.4)
    'site': 0.0,         # Remove site factor (always same)
    'date': 0.3,         # Increase date proximity (was 0.2) 
    'priority': 0.1      # Keep priority matching
}
```

---

### **PHASE 2: Implement Ticket Selection & Merge**

#### **2.1 Enhanced Duplicate Review Dialog**
**New Features:**
- **Ticket Checkboxes**: Allow selection of specific tickets to merge
- **Primary Ticket Selection**: Choose which ticket becomes the "master"
- **Merge Preview**: Show what the merged ticket will look like
- **Partial Merge Options**: Merge some but not all tickets in a group

**UI Changes:**
```
[Duplicate Review Dialog]
┌─────────────────────────────────────────┐
│ Group: DUP001 (85.3% confidence)       │
├─────────────────────────────────────────┤
│ ☑️ INC001 [Primary] ← Select as master │
│ ☑️ INC002           ← Include in merge │  
│ ☐ INC003           ← Keep separate     │
├─────────────────────────────────────────┤
│ [Preview Merged Ticket]                 │
│ [✅ Merge Selected] [❌ Dismiss] [Skip] │
└─────────────────────────────────────────┘
```

#### **2.2 Merge Logic Implementation**
```python
class TicketMerger:
    def merge_tickets(self, primary_ticket, tickets_to_merge):
        """
        Merge selected tickets into primary ticket
        - Combines descriptions with timestamps
        - Keeps earliest created date
        - Uses highest priority level
        - Marks merged tickets as inactive
        """
```

---

### **PHASE 3: Data Reprocessing After Manual Review**

#### **3.1 Apply Changes Button**
**New UI Element:**
- Add "Apply Manual Review Changes" button to Data Quality tab
- Button becomes enabled when there are pending manual review decisions
- Shows count of pending changes: "Apply Changes (5 pending)"

#### **3.2 Data Update Pipeline**
```python
def apply_manual_review_changes():
    """
    1. Process all pending merge/dismiss decisions
    2. Update underlying dataset:
       - Mark merged tickets as inactive
       - Update ticket descriptions/fields
       - Recalculate derived metrics
    3. Regenerate quality report
    4. Refresh all report caches
    5. Update UI with new statistics
    """
```

#### **3.3 Ticket Status Tracking**
```python
# Add new columns to dataset:
df['Is_Active'] = True          # False for merged tickets
df['Merged_Into'] = None        # ID of primary ticket if merged
df['Manual_Review_Status'] = 'pending'  # pending/merged/dismissed
```

---

### **PHASE 4: Detailed Analytics Views**

#### **4.1 Stability Dashboard Drill-Down**
**Current**: Shows summary statistics only
**New**: Click on any metric to see underlying tickets

```
[Stability Dashboard]
┌─────────────────────────────────────┐
│ 🏗️ Overall Stability: 87.3%       │ ← Click to see calculation details
│ 📊 Critical Rate: 12.5%            │ ← Click to see critical tickets
│ ⏱️ Avg MTTR: 4.2 hours            │ ← Click to see resolution data
└─────────────────────────────────────┘
```

**Implementation:**
- Add clickable elements to dashboard metrics
- Create detail windows showing:
  - Which tickets contributed to each metric
  - Calculation methodology
  - Time period breakdown
  - Site-specific contributions

#### **4.2 Pattern Analysis Evidence Views**
**Current**: Shows "3 synchronized incidents detected"
**New**: Shows which specific incidents and evidence

```
[Pattern Analysis Details]
┌─────────────────────────────────────────────────────────┐
│ 🔗 Synchronized Incident Event #1                      │
│ Confidence: 94.2% | Time Window: 2024-01-15 14:30-15:00│
├─────────────────────────────────────────────────────────┤
│ Evidence:                                               │
│ • INC001 - Wendy's #123 - Network failure (14:32)     │
│ • INC002 - Wendy's #124 - Network outage (14:35)      │
│ • INC003 - Wendy's #125 - Connectivity lost (14:38)   │
│                                                         │
│ Root Cause Analysis: Network Infrastructure Issue      │
│ Recommendation: Review network vendor SLA              │
│ [📤 Export Incident Group] [🔍 Investigate Further]   │
└─────────────────────────────────────────────────────────┘
```

#### **4.3 Recurring Patterns Detail View**
```
[Recurring Pattern: Wendy's #456]
┌─────────────────────────────────────────────────────┐
│ Pattern: High incidents every Monday morning        │
│ Confidence: 89.7% | Occurrences: 8/10 weeks       │
├─────────────────────────────────────────────────────┤
│ Evidence Tickets:                                   │
│ • 2024-01-08 Mon 09:15 - POS system failure        │
│ • 2024-01-15 Mon 09:32 - Terminal offline          │
│ • 2024-01-22 Mon 08:45 - Payment processing down   │
│ • 2024-01-29 Mon 09:18 - Register connectivity     │
│                                                     │
│ Analysis: Weekend system updates causing instability│
│ [📤 Export Pattern] [🔄 Set Alert] [📋 Create Task]│
└─────────────────────────────────────────────────────┘
```

---

### **PHASE 5: Analytics Export Integration**

#### **5.1 Enhanced Comprehensive Export**
**New Excel Sheets:**
- **Stability_Dashboard**: All dashboard metrics with calculations
- **Pattern_Analysis**: Synchronized incidents with evidence tickets
- **Recurring_Patterns**: Site patterns with supporting data
- **Quality_Review_Log**: All manual review decisions
- **Merged_Tickets**: Before/after merge comparison

#### **5.2 Evidence-Based Exports**
Each analytical finding includes:
- **Summary**: High-level insight
- **Evidence**: List of specific tickets supporting the finding
- **Methodology**: How the analysis was performed
- **Confidence**: Statistical confidence in the finding
- **Recommendations**: Actionable next steps

---

## 🔧 **Implementation Priority Order**

### **Sprint 1: Critical Fixes (Week 1)**
1. ✅ **Fix duplicate detection to be site-specific only**
2. ✅ **Implement ticket selection UI in duplicate review dialog**
3. ✅ **Add Apply Changes button with data reprocessing**

### **Sprint 2: Analytics Enhancement (Week 2)**  
4. ✅ **Create detailed drill-down views for stability dashboard**
5. ✅ **Implement evidence views for pattern analysis**
6. ✅ **Add underlying data display for all analytics**

### **Sprint 3: Export Integration (Week 3)**
7. ✅ **Integrate analytics into comprehensive export system**
8. ✅ **Add evidence-based export sheets**
9. ✅ **Create analytical findings documentation**

---

## 🎯 **Success Criteria**

### **Duplicate Management:**
- ✅ Duplicates detected only within same site
- ✅ Can select specific tickets to merge/keep separate
- ✅ Merge decisions update underlying data and reports
- ✅ Apply button reprocesses data with manual review decisions

### **Analytics Transparency:**
- ✅ Every insight shows supporting evidence (specific tickets)
- ✅ Can drill down from summary to detailed ticket lists
- ✅ Analysis methodology is visible and verifiable
- ✅ Recommendations are actionable with context

### **Export Completeness:**
- ✅ All analytics findings included in comprehensive export
- ✅ Evidence tickets listed for each insight
- ✅ Manual review decisions documented
- ✅ Before/after comparison for merged tickets

### **User Experience:**
- ✅ Clear visual indication of pending changes
- ✅ Obvious path from insight to supporting data
- ✅ Confidence in analytical findings through transparency
- ✅ Ability to act on insights with proper context

This redesign transforms the data quality system from a basic duplicate detector into a comprehensive, transparent, and actionable quality management platform.