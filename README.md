# IT Stability & Operations Health Monitor

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

A powerful desktop application for analyzing IT support ticket data and generating comprehensive stability reports. Transform your raw ticket exports into clear, actionable insights about operational health across franchise locations.

## ✨ Key Features

### 📊 **Comprehensive Analytics & Reporting**
- **Portfolio Stability Metrics**: Track percentage of ALL supported sites with zero critical incidents
- **Critical Hotspots**: Identify sites with recurring critical issues (with sample ticket numbers)
- **Site Scorecard**: Performance metrics with MTTR analysis and stability scoring
- **Green List**: Recognize stable, well-performing locations
- **Franchise Overview**: Company-level performance comparison with volume-weighted metrics
- **Equipment Analysis**: Breakdown by hardware/software categories with failure patterns
- **📋 Incident Details**: Individual ticket view showing exact cases from your data
- **🔍 Site Drill-Down**: Deep-dive analysis for specific locations with contextual insights

### 🎯 **Advanced Analytics Dashboard**
- **Temporal Pattern Recognition**: Detect synchronized incidents across multiple sites
- **Peak Incident Time Analysis**: Identify when problems most commonly occur
- **Site Correlation Matrix**: Discover sites with correlated incident patterns  
- **Seasonal Pattern Detection**: Understand cyclical trends in your data
- **Anomaly Detection**: Automatically flag unusual incident volume spikes
- **Smart Insights Generation**: AI-powered recommendations for operational improvements

### 📈 **Portfolio Management**
- **Total Sites Configuration**: Dynamically adjust total supported sites count
- **Portfolio Coverage Tracking**: Monitor what percentage of sites had incidents
- **Critical Incident Distribution**: Breakdown of sites by critical case count (0, 1, 2, 3, 4+)
- **Portfolio vs Active Site Metrics**: Distinguish between portfolio-wide and activity-based stability
- **Real-time Statistics**: Updated metrics as you review and process data

### 🔍 **Data Quality Management**
- **Smart Duplicate Detection**: Multi-factor algorithm considering description, timing, and priority
- **Manual Review Interface**: Intuitive UI for reviewing and processing duplicate groups
- **Confidence-Based Classification**: High (≥90%), Medium (70-89%), Low (<70%) confidence scoring
- **Visual Feedback System**: Color-coded pending status with detailed action descriptions
- **Batch Processing**: Auto-process high-confidence duplicates or review manually
- **Audit Trail**: Complete tracking of all data quality decisions and actions

### 🔍 **Advanced Filtering & Search**
- Date range filtering with preset options (Last 7 days, Last month, etc.)
- Priority level multi-selection with smart defaults
- Company and site cascading filters with auto-completion
- Dynamic category/subcategory relationships
- Real-time filter application with result counts
- Saved filter configurations for repeated analysis

### 💾 **Flexible Data Handling**
- **Multi-Format Support**: CSV, Excel (.xlsx, .xls) file import
- **Intelligent Column Detection**: Automatic mapping of common ticket fields
- **Robust Date Parsing**: Handles multiple date formats automatically
- **Data Validation**: Comprehensive error checking with helpful guidance
- **Export Options**: Multiple output formats including comprehensive Excel workbooks

### 📤 **Comprehensive Export System**
- **Excel Workbooks**: Multi-sheet exports with formatted reports, analytics, and raw data
- **CSV Exports**: Filtered data export matching current view
- **Analytics Integration**: Export includes stability dashboard, pattern analysis, and insights
- **Audit Logs**: Export complete data quality audit trail
- **Professional Formatting**: Color-coded cells, charts, and summary statistics

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git (for installation from repository)

### Installation

```bash
# Clone the repository
git clone https://github.com/atomoutput/reportoid.git
cd reportoid

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### First Run Workflow

1. **Launch Application**: Run `python main.py` to start the GUI interface
2. **Load Your Data**: 
   - Click **"📁 Load Data"** button
   - Select your CSV or Excel file with ticket data
   - Review any warnings or validation messages
3. **Configure Portfolio Settings**:
   - Use the **"Total Sites"** controls to set your total supported sites count
   - This enables accurate portfolio stability metrics
4. **Apply Filters** (Optional):
   - Set date range for analysis period
   - Select specific companies, sites, or priority levels
   - Use advanced filters for category-specific analysis
5. **Generate Reports**:
   - Use **"Generate Reports"** for comprehensive analysis
   - Try **"Stability Dashboard"** for advanced analytics
   - Review **"Data Quality"** tab for duplicate management
6. **Export Results**:
   - Use **"📤 Export Comprehensive"** for full Excel workbook
   - Export filtered data or specific report sections as needed

## 📁 File Structure

```
reportoid/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── LICENSE                     # MIT License
├── stability_monitor/          # Main application package
│   ├── __init__.py
│   ├── config/
│   │   ├── settings.py         # Application configuration
│   ├── controllers/
│   │   ├── app_controller.py   # Main application logic
│   ├── models/
│   │   ├── data_manager.py     # Data processing and management
│   │   ├── report_engine.py    # Report generation engine
│   ├── utils/
│   │   ├── audit_trail.py      # Data quality audit tracking
│   │   ├── data_quality.py     # Duplicate detection and quality analysis
│   │   ├── date_utils.py       # Date parsing and formatting utilities
│   │   ├── pattern_recognition.py  # Temporal pattern analysis
│   │   ├── stability_analytics.py  # Advanced analytics engine
│   │   └── validators.py       # Data validation utilities
│   └── views/
│       ├── main_window.py      # Main GUI interface
│       ├── quality_management.py  # Data quality management interface
│       └── analytics_drilldown.py # Analytics detail views
├── tests/
│   └── sample_data/
│       └── wowzi.csv           # Sample data for testing
```

## 🔧 Configuration

### Portfolio Settings
The application supports dynamic configuration of total supported sites:

```python
# In stability_monitor/config/settings.py
"total_supported_sites": {
    "enabled": True,
    "count": 250,  # Adjust to your portfolio size
    "last_updated": None,
    "notes": "Total number of sites under IT support coverage"
}
```

### Duplicate Detection
Customize duplicate detection sensitivity:

```python
"duplicate_detection": {
    "site_threshold": 0.8,        # Site name similarity
    "description_threshold": 0.6, # Description similarity  
    "time_window_hours": 24,      # Time window for grouping
    "min_confidence": 0.7         # Minimum confidence for auto-processing
}
```

### Analytics Configuration
Control pattern analysis parameters:

```python
"pattern_analysis": {
    "sync_time_window_minutes": 30,    # Synchronized incident detection
    "correlation_threshold": 0.6,      # Site correlation sensitivity
    "min_incidents_for_pattern": 3     # Minimum incidents to establish pattern
}
```

## 📊 Data Requirements

### Required Columns
Your ticket data should include these columns (column names are automatically detected):
- **Ticket Number/ID**: Unique identifier
- **Site/Location**: Site identifier
- **Priority**: Critical, High, Medium, Low
- **Created Date**: Incident creation timestamp
- **Description**: Incident description text
- **Status**: Current ticket status
- **Company**: Company/franchise identifier

### Optional Columns (Enhance Analysis)
- **Category/Type**: Hardware, Software, Network, etc.
- **Subcategory**: More specific categorization
- **Resolution Date**: For MTTR calculations
- **Assigned Group**: Support team assignments
- **Customer Contact**: Contact information

### Supported Formats
- **CSV Files**: UTF-8 encoding recommended
- **Excel Files**: .xlsx and .xls formats
- **Date Formats**: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, and many others
- **Text Encoding**: UTF-8, Latin-1, Windows-1252

## 📈 Key Metrics & Calculations

### Portfolio Stability
- **Portfolio Stability**: Percentage of ALL supported sites (not just active sites) with zero critical incidents
- **Active Site Stability**: Traditional metric - percentage of sites with incidents that have zero critical cases
- **Portfolio Coverage**: Percentage of supported sites that had any incidents during the period

### Site Performance Scoring
- **Critical Case Density**: Critical incidents per site over time period
- **MTTR Performance**: Mean time to resolution vs target benchmarks
- **Incident Volume Trends**: Month-over-month incident count changes
- **Stability Trend**: Historical stability performance tracking

### Advanced Analytics
- **Synchronized Incidents**: Cross-site incidents within time windows suggesting common root causes
- **Temporal Patterns**: Peak incident times, weekly/monthly patterns, seasonal trends
- **Site Correlation**: Statistical correlation between site incident patterns
- **Anomaly Detection**: Unusual incident volume spikes requiring investigation

## 🛠️ Advanced Features

### Data Quality Management
1. **Duplicate Detection Engine**:
   - Multi-factor similarity scoring
   - Confidence-based classification
   - Manual review with visual feedback
   
2. **Review Interface**:
   - Color-coded pending status
   - Detailed action descriptions
   - Batch processing capabilities
   
3. **Quality Metrics**:
   - Overall data quality score
   - Duplicate detection accuracy
   - Review completion tracking

### Pattern Recognition
1. **Synchronized Incidents**:
   - Detects incidents across multiple sites within time windows
   - Suggests common root causes
   - Correlation scoring and confidence ratings
   
2. **Temporal Analysis**:
   - Peak incident times (hourly, daily, monthly)
   - Recurring patterns (weekly cycles, seasonal trends)
   - Anomaly detection for volume spikes

### Export & Integration
1. **Excel Workbooks**:
   - Multiple formatted sheets (Reports, Analytics, Raw Data)
   - Charts and visualizations
   - Professional formatting with color coding
   
2. **Data Integration**:
   - Export filtered datasets
   - Audit trail exports
   - Analytics results with evidence tables

## 🐛 Troubleshooting

### Common Issues

**Data Loading Errors**:
- Ensure your file has proper column headers
- Check date formats are consistent
- Verify file encoding (UTF-8 recommended)

**Missing Analytics Results**:
- Ensure sufficient data volume (minimum 10 incidents recommended)
- Check date range includes recent data
- Verify sites have meaningful incident patterns

**Duplicate Review Issues**:
- Clear browser cache if using web interface
- Restart application if duplicate queue appears empty
- Check file permissions for audit database

**Performance Issues**:
- Limit analysis to specific date ranges for large datasets
- Use company/site filters to reduce processing load
- Consider batch processing for very large datasets

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export STABILITY_MONITOR_DEBUG=1
python main.py
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

This is a specialized application for IT operations analysis. For feature requests or bug reports, please:

1. Ensure you can reproduce the issue with sample data
2. Include your operating system and Python version
3. Provide relevant error messages or screenshots
4. Describe expected vs actual behavior

## 🆘 Support

For technical support:
1. Check the troubleshooting section above
2. Review the sample data format in `tests/sample_data/`
3. Enable debug mode for detailed error logging
4. Provide complete error messages when reporting issues

---

**Built for IT Operations Teams** - Transform your ticket data into actionable operational intelligence.