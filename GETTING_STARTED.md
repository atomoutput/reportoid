# IT Stability Monitor - Getting Started

## Installation

1. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application:**
   ```bash
   python main.py
   ```

## Quick Start

### 1. Load Your Data
- Click **"📁 Load Data"** button
- Select your CSV or Excel file with ticket data
- The application will automatically detect columns and validate data
- View any warnings or errors in the popup dialog

### 2. Apply Filters (Optional)
- **Date Range**: Enter start and end dates (YYYY-MM-DD format)
- **Priority**: Check/uncheck priority levels (Critical, High, Medium, Low)
- **Company**: Select specific franchise company
- **Site**: Select specific site (filtered by company selection)
- **Advanced Filters**: Click "▼ Advanced Filters" for category/subcategory filtering

### 3. Generate Reports
Click any report button to generate analysis:

#### Core Reports:
- **🚨 Critical Hotspots**: Sites with multiple critical incidents
- **📊 Site Scorecard**: Performance metrics for all sites  
- **✅ Green List**: Sites with zero critical incidents
- **🏢 Franchise Overview**: Company-level performance comparison

#### Enhanced Reports:
- **🔧 Equipment Analysis**: Issues by equipment category
- **🔄 Repeat Offenders**: Sites with recurring problems
- **⏱️ Resolution Tracking**: SLA compliance tracking
- **📈 Workload Trends**: Ticket volume patterns

### 4. Export Results
- **Export All**: Click "💾 Export" to save current report results
- **Export Selected**: Select specific rows, then click "Export Selected"
- Choose CSV or Excel format

## Data Requirements

Your data file should contain these columns:

### Required Columns:
- **Site**: Location identifier
- **Priority**: Issue priority (1 - Critical, 2 - High, 3 - Medium, 4 - Low)
- **Created**: Issue creation date/time
- **Company**: Franchise company name

### Optional Columns:
- **Number**: Ticket number/ID
- **Short description**: Issue description
- **Category**: Equipment/issue category
- **Subcategory**: Specific issue type
- **Resolved**: Resolution date/time

## Sample Data Format

```csv
Site,Number,Short description,Category,Subcategory,Priority,Created,Resolved,Company
Wendy's #8120,CS0298093,Server Issue,CFC,Sales issues,3 - Medium,6/2/2025 9:24,6/17/2025 15:06,Delight Ohio River LLC
Wendy's #1852,CS0299168,Labor Report Issue,CFC,Labor issues,1 - Critical,6/2/2025 12:08,6/11/2025 11:04,Wendpark LLC
```

## Understanding Reports

### Critical Hotspots Report
Shows sites with 2+ critical incidents (configurable threshold).
**Use Case**: Identify locations needing immediate attention.

**Columns**:
- Site, Company, Critical Count, Latest Incident, Days Since Last

### Site Scorecard Report  
Comprehensive performance metrics for all sites.
**Use Case**: Overall health assessment and comparison.

**Columns**:
- Site, Company, Total Tickets, Critical Count, Critical %, Avg MTTR, Longest Open, Status

**Status Indicators**:
- 🔴 High Risk: >48 hour average resolution time
- 🟡 Medium Risk: 24-48 hour average resolution time  
- 🟢 Good: <24 hour average resolution time

### Green List Report
Sites with zero critical incidents in the timeframe.
**Use Case**: Recognize stable, well-performing locations.

### Franchise Overview Report
Company-level aggregation and benchmarking.
**Use Case**: Compare franchise performance, identify best practices.

## Tips & Best Practices

### Filtering Strategy:
1. Start with full dataset to understand overall patterns
2. Apply date filters for specific time periods
3. Filter by priority for focused analysis
4. Use company/site filters for detailed investigation

### Report Workflow:
1. **Critical Hotspots** → Identify problem sites
2. **Site Scorecard** → Analyze performance metrics
3. **Equipment Analysis** → Find systemic issues
4. **Franchise Overview** → Compare company performance

### Data Quality:
- Ensure consistent date formats
- Standardize priority values
- Clean site and company names for accurate grouping
- Verify category/subcategory relationships

## Troubleshooting

### Common Issues:

**"Missing required columns" error:**
- Check that your file has: Site, Priority, Created, Company columns
- Column names are case-sensitive

**Date parsing warnings:**
- Ensure dates are in consistent format (MM/DD/YYYY or YYYY-MM-DD)
- Check for empty date cells

**No results in reports:**
- Verify your filters aren't too restrictive
- Check that you have data in the selected date range
- Ensure priority values match expected format

**Performance issues with large files:**
- The application can handle thousands of records
- For very large datasets (>50K records), consider filtering by date range

## Testing

Run component tests:
```bash
python test_app.py
```

Run GUI test:
```bash
python test_gui.py
```

## Support

The application includes:
- Built-in data validation with helpful error messages
- Automatic column mapping suggestions
- Progress indicators for long operations
- Export functionality for all reports
- Status updates and informative dialogs

For additional help, use the Help menu in the application or refer to the comprehensive feature specification document.