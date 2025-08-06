# IT Stability Monitor - Complete Application Workflow Analysis

## 🚀 **Application Startup Flow**

### **1. Application Launch**
```bash
python main.py
```

**What Happens:**
1. **Settings Initialization**: Loads default configuration from `settings.py`
   - UI preferences (window size, theme)
   - Data processing rules (date formats, required columns)
   - Quality thresholds (duplicate detection, site filtering)
   - Report parameters (MTTR targets, critical thresholds)

2. **Main Window Creation**: 
   - Creates 1200x800 window with minimum 1024x768
   - Initializes tabbed interface with "Analysis & Reports" and "Data Quality" tabs

3. **Controller Setup**: 
   - Initializes `DataManager`, `ReportEngine`, `AuditTrailManager`
   - Sets up all UI callbacks and event handlers
   - Creates audit database if enabled

4. **UI State**: All buttons disabled until data is loaded

---

## 📁 **Step 1: Data Loading Workflow**

### **User Action: Click "📁 Load Data" or File → Load Data**

**File Selection:**
- Opens file dialog for CSV/Excel files
- Supported formats: `.csv`, `.xlsx`, `.xls`
- User selects their IT ticket data file

**Data Processing Pipeline:**
```
File Selected → Validation → Preprocessing → Quality Analysis → UI Update
```

#### **1A. Data Validation**
```python
# DataManager.load_file()
1. File format detection (CSV vs Excel)
2. Column mapping and validation
3. Required columns check: Site, Priority, Created, Company
4. Optional columns: Number, Short description, Category, Subcategory, Resolved
```

**Validation Results:**
- ✅ **Success**: Continues to preprocessing
- ❌ **Failure**: Shows error dialog with missing columns/format issues

#### **1B. Data Preprocessing** 
```python
# DataManager._preprocess_data()
1. Date parsing with multiple format support:
   - "%m/%d/%Y %H:%M" 
   - "%Y-%m-%d %H:%M:%S"
   - "%m/%d/%Y"
   - "%Y-%m-%d"

2. Data cleaning:
   - Handles missing values
   - Standardizes priority levels
   - Creates category mappings

3. Column standardization:
   - Maps user columns to internal schema
   - Validates data types
```

#### **1C. Site Filtering (Phase 1 Feature)**
```python
# DataQualityManager.apply_site_filtering()
Default: Filter for Wendy's locations only
- Searches Site column for "wendy" keyword (case-insensitive)
- Removes non-Wendy's tickets from analysis
- Tracks filtering statistics
```

**Filter Results:**
- Shows warning if tickets were filtered out
- Updates status: "Site filter removed X tickets from Y non-Wendy's sites"

#### **1D. Quality Analysis (Phase 3 Feature)**
```python
# DataQualityManager.generate_quality_report()
1. Duplicate Detection:
   - Multi-factor similarity scoring
   - Cross-site incident correlation
   - Confidence-based classification

2. Data Quality Scoring:
   - Completeness assessment
   - Consistency validation
   - Integrity checks

3. Recommendation Generation:
   - Actionable quality improvements
   - Priority suggestions for review
```

#### **1E. UI Updates**
**Main Window Updates:**
- Status bar: "Loaded X records from Y total"
- Data info: "Sites: X | Companies: Y | Categories: Z"
- Date range display if available
- Enables all report buttons and filters

**Filter Dropdowns Populated:**
- Company list (auto-populated from data)
- Site list (filtered based on company selection)
- Category/Subcategory lists (with hierarchical relationship)

**Data Quality Tab Updates:**
- Quality Score: X% (excellent/good/needs improvement)
- Duplicate Groups: X potential groups found
- Manual Review Queue: X groups requiring review

**Success Dialog:**
```
Data loaded successfully!

Records processed: 1,245
Sites: 23
Companies: 1 (Wendy's)
Categories: 8
Date range: 2024-01-01 to 2024-12-31

Quality Score: 87.3%
Duplicate Groups: 3 (2 requiring manual review)
```

---

## 🔍 **Step 2: Data Filtering Workflow**

### **Filter Panel Options:**

#### **2A. Date Range Filtering**
**Preset Buttons:**
- Last 7 Days
- Last 30 Days  
- Last 90 Days
- This Year
- All Time

**Custom Date Entry:**
- From: YYYY-MM-DD
- To: YYYY-MM-DD
- Clear button to reset

#### **2B. Priority Filtering**
**Checkboxes:**
- ☑️ Critical (C)
- ☑️ High (H)
- ☑️ Medium (M)
- ☑️ Low (L)

#### **2C. Location Filtering**
**Company Dropdown:**
- All companies or specific selection
- Auto-populates from data
- Search functionality (type to filter)
- 🔍 Focus button

**Site Dropdown:**
- Cascades based on company selection
- Search functionality
- Shows all sites for selected company
- 🔍 Focus button

#### **2D. Advanced Filters (Collapsible)**
**Category/Subcategory:**
- Hierarchical relationship
- Category selection updates subcategory options
- Search functionality in both dropdowns

**Filter Controls:**
- "Clear All" - Resets all filters
- "Apply Filters" - Manually refresh results

### **Auto-Filtering Behavior:**
- Filters apply automatically on change
- Cascading updates (company → sites, category → subcategories) 
- Real-time result count updates
- Maintains filter state across report switches

---

## 📊 **Step 3: Report Generation Workflow**

### **Report Categories:**

#### **3A. Core Operational Reports**

**🚨 Critical Hotspots**
```python
# ReportEngine.generate_critical_hotspots()
Purpose: Identify sites with highest critical incident rates
Metrics: Critical incidents/total tickets, average resolution time
Threshold: Configurable (default: >2 critical incidents)
Output: Ranked list with impact scores
```

**📊 Site Scorecard** 
```python
# ReportEngine.generate_site_scorecard()
Purpose: Performance scoring for each site
Metrics: Resolution time, incident volume, critical rate
Scoring: 0-100 scale with color coding
Output: Sortable grid with performance indicators
```

**✅ Green List**
```python
# ReportEngine.generate_green_list()
Purpose: Well-performing sites meeting all targets
Criteria: Low critical rate, fast MTTR, stable trends
Output: Sites to celebrate/use as benchmarks
```

**🏢 Franchise Overview**
```python
# ReportEngine.generate_franchise_overview()
Purpose: High-level operational health summary
Metrics: Total incidents, trends, top issues
Output: Executive dashboard view
```

#### **3B. Enhanced Analysis Reports**

**🔧 Equipment Analysis**
```python
# ReportEngine.generate_equipment_analysis()
Purpose: Equipment-related failure patterns
Focus: Hardware, software, infrastructure issues
Output: Equipment category breakdown with trends
```

**🔄 Repeat Offenders**
```python
# ReportEngine.generate_repeat_offenders()
Purpose: Sites with recurring issues
Logic: Multiple incidents same category/timeframe
Output: Sites needing intervention focus
```

**⏱️ Resolution Tracking**
```python
# ReportEngine.generate_resolution_tracking()
Purpose: MTTR analysis and SLA compliance
Metrics: Average resolution time by priority/category
Output: Performance vs targets with trends
```

**📈 Workload Trends**
```python
# ReportEngine.generate_workload_trends()
Purpose: Volume patterns and resource planning
Analysis: Time-based incident patterns
Output: Staffing and resource recommendations
```

#### **3C. Detailed Investigation Reports**

**📋 Incident Details**
```python
# ReportEngine.generate_incident_details()
Purpose: Complete incident listing with all fields
Use Case: Detailed investigation and audit
Output: Full ticket data export
```

**🔍 Site Drill-Down**
```python
# Interactive drill-down by selecting site in results
Purpose: Deep dive into specific site issues
Trigger: Select site from report → click "Site Drill-Down"
Output: Site-specific incident analysis
```

#### **3D. Phase 2: Advanced Analytics Reports**

**🏗️ Stability Dashboard**
```python
# ReportEngine.generate_system_stability_dashboard()
Purpose: Overall system health metrics
Analysis: Stability scoring, benchmark comparison
Features: Trend analysis, predictive insights
Output: Executive stability overview
```

**🔍 Pattern Analysis**
```python
# ReportEngine.generate_time_pattern_analysis()
Purpose: Temporal pattern detection
Analysis: Synchronized incidents, recurring patterns
Features: Cross-site correlation, time clustering
Output: Pattern insights and root cause suggestions
```

**💡 Stability Insights**
```python
# ReportEngine.generate_stability_insights()
Purpose: AI-generated operational insights
Analysis: System-wide trends and anomalies
Features: Actionable recommendations
Output: Strategic improvement suggestions
```

**📊 Quality Report**
```python
# ReportEngine.generate_data_quality_report()
Purpose: Data integrity and completeness analysis
Analysis: Missing fields, inconsistencies, duplicates
Output: Data improvement recommendations
```

### **Report Generation Flow:**
1. **Filter Application**: Applies current filters to dataset
2. **Data Validation**: Checks if filtered data is sufficient
3. **Progress Display**: Shows "Generating [report] report..." with progress bar
4. **Report Processing**: Runs specific report algorithm
5. **Results Display**: Updates main results grid
6. **Status Update**: Shows record count and report type

---

## 📤 **Step 4: Export Workflow**

### **Export Options:**

#### **4A. Single Report Export**
**💾 Export Current**
- Exports currently displayed report
- CSV format with timestamp
- Includes applied filter information
- File name: `[ReportType]_[Date]_[Time].csv`

#### **4B. Comprehensive Export**
**📊 Export All Reports** 
```python
# AppController._handle_export_comprehensive()
Creates Excel file with multiple sheets:
- Summary sheet with metadata
- Each report type as separate sheet
- Applied filters documented
- Generation timestamp included
```

**Sheet Structure:**
- **Summary**: Filters applied, generation info, record counts
- **Critical_Hotspots**: Full critical sites analysis
- **Site_Scorecard**: All sites performance metrics
- **Green_List**: Well-performing sites
- **Franchise_Overview**: Executive summary data
- **[Additional sheets for each enabled report type]**

#### **4C. Filtered Data Export**
**📤 Export Filtered Data**
- Exports raw filtered dataset
- All columns included
- Respects current filter settings
- Use case: Further analysis in external tools

#### **4D. Selection-Based Export**
**Export Selected**
- Available when items selected in results grid
- Exports only selected rows
- Same format as full export
- Use case: Sharing specific findings

---

## 🛠️ **Step 5: Phase 3 - Manual Review Workflow**

### **Data Quality Tab Interface:**

#### **5A. Quality Overview Panel**
**Displays:**
- **Quality Score**: 87.3% with color coding (Green/Yellow/Red)
- **Duplicates**: X potential groups found
- **Review Queue**: Y groups requiring manual review

**Action Buttons:**
- **🔄 Refresh Quality Analysis**: Re-runs quality assessment
- **🤖 Auto-Process High Confidence**: Merges duplicates >95% confidence
- **📤 Export Audit Log**: Downloads audit trail

#### **5B. Duplicate Review Workflow**

**Queue Management:**
```
Filter Options:
- All Groups
- High Confidence (>90%)
- Manual Review Required (70-90%)
- Low Confidence (<70%)
```

**Review Queue Display:**
| Group ID | Primary Ticket | Duplicates | Confidence | Site | Created | Status | Action Needed |
|----------|---------------|------------|------------|------|---------|---------|---------------|
| DUP001   | INC001        | INC002, INC003 | 94.2% | Wendy's #123 | 2024-01-15 | Pending | Manual Review |

**Review Actions:**
1. **👁️ Review Selected**: Opens detailed comparison dialog
2. **⚡ Batch Process**: Processes multiple groups simultaneously

#### **5C. Duplicate Review Dialog**

**Side-by-Side Comparison:**
- **Field Comparison Table**:
  - Ticket #, Site, Priority, Created, Description, Category
  - **Red highlighting** for differences
  - **Green highlighting** for matches

**Detailed View Tab:**
- Complete ticket information
- Confidence scoring breakdown
- Similarity factors analysis

**Review Decision Options:**
1. **✅ Merge as Duplicates**: 
   - Requires review notes (optional)
   - Creates audit entry
   - Updates ticket status

2. **❌ Dismiss (Not Duplicates)**:
   - Requires explanation notes (mandatory)
   - Creates audit entry
   - Removes from review queue

3. **⏭️ Skip for Now**:
   - Returns to queue
   - No audit entry
   - Can review later

#### **5D. Audit Trail Management**

**Audit Trail View:**
| Timestamp | Action | User | Description | Affected Tickets | Status |
|-----------|--------|------|-------------|------------------|---------|
| 2024-01-15 14:30 | merge_duplicates | admin | Network outage duplicates | INC001,INC002 | Success |
| 2024-01-15 14:25 | dismiss_duplicates | admin | Different root causes | INC003,INC004 | Success |

**Audit Features:**
- **Filter by Action Type**: All/Merge/Dismiss/Manual/Reversals
- **🔄 Refresh**: Updates audit display
- **Export Capability**: CSV/JSON format
- **Action Reversal**: Undo previous decisions (where applicable)

**Audit Entry Details:**
- **Action ID**: Unique identifier
- **User Tracking**: Who performed action
- **Timestamp**: When action occurred
- **Description**: Human-readable summary
- **Affected Tickets**: List of ticket IDs
- **Metadata**: Confidence scores, reasoning
- **Reversibility**: Whether action can be undone

---

## ⚙️ **Step 6: Settings and Configuration**

### **Settings Dialog** (⚙️ Settings button)

**Categories:**
1. **UI Preferences**
   - Window size defaults
   - Theme selection
   - Display preferences

2. **Data Processing**
   - Date format preferences
   - Column mapping rules
   - Required vs optional fields

3. **Quality Management**
   - Duplicate detection thresholds
   - Site filtering rules
   - Auto-review confidence levels

4. **Report Parameters**
   - MTTR targets by priority
   - Critical incident thresholds
   - Color coding rules

5. **Export Options**
   - Default export format
   - Timestamp preferences  
   - Filter documentation

---

## 🔄 **Step 7: Refresh and Update Workflow**

### **Refresh Options:**

**🔄 Refresh Button (Main)**
- Re-applies current filters
- Regenerates current report
- Updates all display elements

**🔄 Refresh Quality Analysis**
- Re-runs duplicate detection
- Updates quality scoring
- Refreshes manual review queue

**Auto-Refresh Triggers:**
- Filter changes
- Data modifications
- Manual review decisions
- Settings updates

---

## 📋 **Complete User Journey Example**

### **Scenario: IT Manager Monday Morning Review**

**Step 1: Launch & Load**
```
1. User starts application
2. Clicks "📁 Load Data"
3. Selects "weekend_tickets.xlsx"
4. Reviews load summary: "47 tickets, 12 sites, 1 critical issue"
5. Notes quality warning: "2 duplicate groups requiring review"
```

**Step 2: Critical Issue Assessment**
```
1. Clicks "🚨 Critical Hotspots" 
2. Sees Wendy's #456 has 3 critical incidents
3. Clicks "🔍 Site Drill-Down" for detailed analysis
4. Reviews specific incidents: network, POS, phone system
5. Notes pattern: all incidents Friday 8 PM
```

**Step 3: Quality Review**
```
1. Switches to "Data Quality" tab
2. Reviews duplicate queue: 2 groups pending
3. Clicks "👁️ Review Selected" for first group
4. Sees network incidents at 3 locations within 10 minutes
5. Clicks "✅ Merge as Duplicates" with note: "Same outage event"
6. Reviews second group, clicks "❌ Dismiss": "Different issues"
```

**Step 4: Weekly Report Generation**
```
1. Sets date filter to "Last 7 Days"
2. Clicks "📊 Export All Reports"
3. Saves comprehensive Excel report
4. Shares with team via email
5. Sets reminder to review duplicate queue daily
```

**Total Time: 10-15 minutes for comprehensive weekly analysis**

---

## 🎯 **Workflow Optimization Features**

### **Efficiency Enhancements:**
- **Keyboard Shortcuts**: Ctrl+O (load), Ctrl+E (export), F5 (refresh)
- **Filter Persistence**: Maintains settings across sessions
- **Auto-Save**: Settings and preferences saved automatically
- **Batch Operations**: Process multiple items simultaneously
- **Smart Defaults**: Learns from user patterns
- **Progress Indicators**: Clear feedback on long operations
- **Error Recovery**: Graceful handling of issues with user guidance

### **Power User Features:**
- **Advanced Filtering**: Complex multi-criteria filtering
- **Custom Exports**: Configurable output formats
- **Audit Trail**: Complete action history with reversal
- **Quality Automation**: High-confidence auto-processing
- **Pattern Recognition**: Automated trend identification
- **Predictive Insights**: AI-generated recommendations

This comprehensive workflow supports both quick operational reviews and deep analytical investigations, making it suitable for daily operations, weekly planning, and strategic analysis.