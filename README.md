# Reportoid - IT Stability & Operations Health Monitor

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)

A powerful desktop application for analyzing IT support ticket data and generating comprehensive stability reports. Transform your raw ticket exports into clear, actionable insights about operational health across franchise locations.

## ✨ Key Features

### 📊 **Comprehensive Reporting**
- **Critical Hotspots**: Identify sites with recurring critical issues (with sample ticket numbers)
- **Site Scorecard**: Performance metrics with MTTR analysis
- **Green List**: Recognize stable, well-performing locations
- **Franchise Overview**: Company-level performance comparison
- **Equipment Analysis**: Breakdown by hardware/software categories
- **📋 Incident Details**: Individual ticket view showing exact cases from your data
- **🔍 Site Drill-Down**: Deep-dive analysis for specific locations
- **📤 Export Filtered Data**: Export raw data matching your current filters

### 🔍 **Advanced Filtering**
- Date range filtering with preset options
- Priority level multi-selection
- Company and site cascading filters
- Dynamic category/subcategory relationships
- Real-time filter application with result counts

### 📈 **Smart Analytics**
- Mean Time to Resolution (MTTR) calculations
- Critical incident trend analysis
- Performance benchmarking across locations
- Automated status indicators (🔴 High Risk, 🟡 Medium, 🟢 Good)
- Equipment failure pattern recognition

### 💾 **Flexible Data Handling**
- CSV and Excel file support
- Automatic column detection and mapping
- Robust date format parsing
- Data validation with helpful error messages
- Export results in multiple formats

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/reportoid.git
cd reportoid

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Basic Usage

1. **Load Data**: Click "📁 Load Data" and select your ticket CSV/Excel file
2. **Apply Filters**: Set date ranges, priorities, companies, or sites as needed
3. **Generate Reports**: Click any report button to analyze your data
4. **Export Results**: Save reports as CSV or Excel files

## 📋 Data Requirements

### Required Columns:
- **Site**: Location identifier
- **Priority**: Issue priority (1 - Critical, 2 - High, 3 - Medium, 4 - Low) 
- **Created**: Issue creation timestamp
- **Company**: Franchise company name

### Optional Columns:
- **Number**: Ticket ID
- **Short description**: Issue description
- **Category**: Equipment/issue category
- **Subcategory**: Specific issue type
- **Resolved**: Resolution timestamp

### Sample Data Format:
```csv
Site,Number,Priority,Created,Resolved,Company,Category,Subcategory
Wendy's #8120,CS001,1 - Critical,6/2/2025 9:24,6/2/2025 15:06,Delight Ohio River LLC,POS,Terminal Down
Wendy's #1852,CS002,3 - Medium,6/2/2025 12:08,6/11/2025 11:04,Wendpark LLC,CFC,Sales issues
```

## 📊 Understanding Reports

### Critical Hotspots Report
- **Purpose**: Identify locations with multiple critical incidents
- **Threshold**: Configurable (default: 2+ critical incidents)
- **Use Case**: Focus immediate attention on problematic sites

### Site Scorecard Report
- **Metrics**: Total tickets, critical %, MTTR, longest open issue
- **Status Indicators**: 
  - 🔴 High Risk: >48h average resolution time
  - 🟡 Medium Risk: 24-48h average resolution time
  - 🟢 Good: <24h average resolution time

### Green List Report
- **Purpose**: Recognize stable operations with zero critical incidents
- **Benefits**: Identify best practices and reward performance

### Equipment Analysis Report
- **Breakdown**: Issues by category and subcategory
- **Insights**: Most problematic equipment types and failure modes
- **Value**: Inform maintenance and replacement decisions

## 🏗️ Architecture

```
reportoid/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── stability_monitor/      # Main application package
│   ├── config/            # Settings and configuration
│   ├── controllers/       # Application logic controllers
│   ├── models/           # Data models and business logic
│   ├── views/            # User interface components
│   ├── utils/            # Utility functions
│   └── tests/            # Test files and sample data
├── test_app.py           # Component tests
├── test_gui.py           # GUI tests
└── GETTING_STARTED.md    # Detailed usage guide
```

## 🧪 Testing

Run component tests:
```bash
python test_app.py
```

Run GUI tests:
```bash
python test_gui.py
```

## 🛠️ Technical Details

- **Framework**: Python 3.8+ with Tkinter GUI
- **Data Processing**: Pandas for efficient data manipulation
- **Architecture**: MVC pattern with clear separation of concerns
- **Date Handling**: Flexible parsing supporting multiple formats
- **Export**: CSV and Excel output with configurable options

## 📖 Documentation

- **[Getting Started Guide](GETTING_STARTED.md)**: Comprehensive setup and usage instructions
- **Built-in Help**: Access help system through the application menu
- **Data Validation**: Automatic validation with helpful error messages

## 🤝 Contributing

This project follows defensive security practices:
- Input validation and sanitization
- Secure file handling
- No external network dependencies
- Local data processing only

## 📄 License

MIT License - see LICENSE file for details.

## 🎯 Use Cases

### IT Operations Teams
- Monitor help desk performance across locations
- Identify recurring technical issues
- Track resolution time improvements
- Generate executive summary reports

### Franchise Management
- Compare operational stability between locations
- Recognize high-performing sites
- Identify sites needing additional support
- Make data-driven resource allocation decisions

### Equipment Planning
- Analyze failure patterns by equipment type
- Prioritize maintenance and replacement schedules
- Identify systemic technical issues
- Optimize support resource deployment

---

**Transform your IT operations data into actionable insights with Reportoid! 🚀**
