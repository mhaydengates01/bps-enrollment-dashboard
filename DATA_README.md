# BPS Enrollment Dashboard - Data Documentation

## Overview

This document outlines the data sourcing strategy, scope decisions, and implementation approach for the Boston Public Schools Enrollment Dashboard project.

## Data Source

**Primary Source:** Massachusetts Department of Elementary and Secondary Education (DESE) - School and District Profiles  
**URL:** https://profiles.doe.mass.edu/statereport/

**Rationale:** DESE is the authoritative source for Massachusetts public school data, providing comprehensive, regularly updated, and standardized reporting across all BPS schools.

## Data Scope

### Time Period
**Selected Range:** 2020-2025 (5 years)

**Rationale:**
- Captures recent trends while remaining manageable within the 4-week project timeline
- Includes pandemic context (2020-2021) and recovery period (2022-2024)
- Ensures data consistency and completeness across all selected reports
- Provides sufficient historical context for meaningful trend analysis
- All selected reports have complete data availability for this period

### Selected Reports

#### Must Have (Week 1-2)
**Student Enrollment and Indicators:**
1. Enrollment by Grade
2. Enrollment by Race/Gender
3. Enrollment by Selected Population (English Learners, Students with Disabilities, High Needs, Economically Disadvantaged)
4. Student Attendance Report

**Assessment and Accountability:**
5. Accountability Report
6. MCAS Achievement Results

#### High Priority (Week 2)
**Student Enrollment and Indicators:**
7. Class Size by Gender and Selected Populations
8. Attrition

**Finance:**
9. Per Pupil Expenditure

#### Optional Enhancements (Week 3)
10. Mobility Rate Report
11. Student Discipline
12. Graduation Rates (high schools only)

**Selection Criteria:**
- Focus on metrics relevant to underprivileged schools and educational equity
- Emphasis on enrollment patterns, demographic trends, and resource allocation
- Balance between comprehensiveness and project timeline feasibility

## Data Collection Approach

### Strategy: Hybrid Manual Download + Automated Processing

#### Phase 1: Manual Download
- Navigate DESE website and manually download CSV/Excel files for each report
- Download all reports for years 2020-2025
- Organize files in structured directory format

**File Organization Structure:**
```
/data/raw/
  enrollment_by_grade/
    2020.csv
    2021.csv
    2022.csv
    2023.csv
    2024.csv
  enrollment_by_race_gender/
  enrollment_selected_populations/
  student_attendance/
  accountability_report/
  mcas_achievement/
  class_size_selected_populations/
  attrition/
  per_pupil_expenditure/
  [optional reports if time permits]
```

#### Phase 2: Automated Processing with n8n

**n8n Workflow Components:**
1. Read binary files from organized directory structure
2. Parse CSV/Excel files using Spreadsheet File node
3. Transform and clean data:
   - Standardize column names
   - Filter for BPS schools only
   - Handle missing values and data type conversions
4. Load processed data into Supabase via REST API
5. Log processing results (success/failure, row counts)

**Workflow Pattern:**
```
[Read Binary Files] 
  → [Spreadsheet File Parser]
  → [Data Transformation Function]
  → [Split In Batches]
  → [HTTP Request to Supabase]
  → [Logging]
```

### Rationale for Hybrid Approach

**Why Manual Download:**
- DESE does not provide a public API
- Building scrapers for 9 report types across 5 years would consume significant project time
- Manual download is time-efficient (2-3 hours vs. 1-2 days of scraper development)
- Reduces risk of broken automation mid-project
- Allows focus on core dashboard functionality and visualizations

**Why Automated Processing:**
- Ensures consistent data cleaning and transformation logic
- Repeatable process if additional years are added later
- Demonstrates technical competency with workflow automation
- Can be triggered manually or scheduled for future updates
- Maintains data quality and integrity through standardized processing

## Future Extensibility

The selected scope and approach allow for future enhancements:
- Additional years of historical data can be added using the same processing workflow
- Optional reports (10-12) can be incorporated without architectural changes
- Automation of downloads can be implemented post-launch if DESE structure permits
- Data refresh mechanisms can be added for ongoing dashboard maintenance
