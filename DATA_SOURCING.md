# BPS Enrollment Dashboard - Data Documentation

## Overview

This document outlines the data sourcing strategy, scope decisions, and implementation approach for the Boston Public Schools Enrollment Dashboard project.

## Data Sources

### Primary Source: Massachusetts E2C Hub (Education-to-Career Research and Data Hub)
**URL:** https://educationtocareer.data.mass.gov/  
**Format:** CSV files downloaded via web interface

**Rationale:** 
- E2C Hub provides comprehensive, machine-readable datasets that consolidate multiple years and report types
- Clean, standardized CSV format eliminates need for Excel file processing
- Single downloads replace multiple year-by-year report exports
- Official Massachusetts state education data portal with regularly updated datasets
- Built on Socrata platform (API available for future automation if needed)

### Secondary Source: DESE School and District Profiles
**URL:** https://profiles.doe.mass.edu/statereport/  
**Format:** Excel files (when E2C Hub datasets unavailable)

**Usage:** Fallback for report types not available on E2C Hub (e.g., Accountability Reports)

## Data Scope

### Geographic Scope
**Focus:** Boston Public Schools District (District Code: 00350000)
- District-level aggregate data
- Individual school-level data (109 schools as of 2024)

**Filter Strategy:** 
- Large datasets (those triggering E2C Hub's size warning) filtered by `DISTRICT_NAME = "Boston"` before download
- Smaller datasets downloaded in full (all Massachusetts districts) and filtered during processing
- Filtering approach determined by practical download constraints rather than uniform policy

### Time Period
**Selected Range:** 2020-2024 (5 years)

**Rationale:**
- Captures recent trends while remaining manageable within the 4-week project timeline
- Includes pandemic context (2020-2021) and recovery period (2022-2024)
- Ensures data consistency and completeness across all selected reports
- Provides sufficient historical context for meaningful trend analysis
- All selected reports have complete data availability for this period

### Selected Datasets

#### Core Enrollment Data (E2C Hub - Single Consolidated Dataset)
**Dataset:** "Enrollment - Grade, Race, Ethnicity, Gender and Selected Populations" (t8td-gens)
- **Source:** https://educationtocareer.data.mass.gov/Students-and-Teachers/Enrollment-Grade-Race-Ethnicity-Gender-and-Selecte/t8td-gens
- **Replaces:** Three separate DESE reports:
  1. Enrollment by Grade
  2. Enrollment by Race/Gender  
  3. Enrollment by Selected Populations
- **Contains:**
  - Student counts by grade (PK through G12, Special)
  - Race/ethnicity percentages (7 categories: AIAN, Asian, Black/African American, Hispanic/Latino, Multi-race, NHPI, White)
  - Gender percentages (Female, Male, Non-Binary)
  - Selected populations counts & percentages:
    - EL (English Learners)
    - FLNE (First Language Not English)
    - HN (High Needs)
    - LI (Low Income - historical)
    - ECD (Economically Disadvantaged - current)
    - SWD (Students with Disabilities)
- **Years Available:** 1992-2025 (filtered to 2020-2024 for project)
- **Granularity:** State, District, and School levels

#### Assessment Data (E2C Hub)
**Dataset:** "MCAS Achievement Results" (i9w6-niyt)
- **Source:** https://educationtocareer.data.mass.gov/Assessment-and-Accountability/MCAS-Achievement-Results/i9w6-niyt
- **Contains:**
  - Next Generation MCAS results (2017-present)
  - Achievement levels by percentage: Meeting/Exceeding, Partially Meeting, Not Meeting
  - Participation rates
  - Average scaled scores
  - Student Growth Percentile (SGP)
  - Breakdowns by: subject (ELA, Math, Science), grade, student group
- **Years Available:** 2017-2025 (filtered to 2020-2024 for project)
- **Granularity:** State, District, and School levels

#### Graduation Outcomes (E2C Hub)
**Dataset:** "High School Graduation Rates" (n2xa-p822)
- **Source:** https://educationtocareer.data.mass.gov/Assessment-and-Accountability/High-School-Graduation-Rates/n2xa-p822
- **Contains:**
  - 4-year and 5-year graduation rates
  - Non-graduates still in school
  - GED completers
  - Dropout counts
  - Breakdowns by student group (demographics, ELL, SWD, economically disadvantaged)
- **Years Available:** Multi-year dataset (filtered to 2020-2024 for project)
- **Granularity:** District and School levels (high schools only)

#### Student Retention (E2C Hub)
**Dataset:** "Student Attrition"
- **Source:** E2C Hub
- **Contains:**
  - Attrition rates by grade and student group
  - Students leaving district
- **Years Available:** Multi-year dataset (filtered to 2020-2024 for project)
- **Downloaded:** Full dataset (all MA districts)
- **Note:** Replaces "Attrition" and "Dropout Report" from original plan

#### Student Attendance (E2C Hub)
**Dataset:** "Student Attendance"
- **Source:** E2C Hub  
- **Contains:**
  - Attendance rates
  - Chronic absenteeism data
  - Breakdowns by student group
- **Years Available:** Multi-year dataset (filtered to 2020-2024 for project)
- **Downloaded:** Full dataset (all MA districts)

#### Student Discipline (E2C Hub)
**Dataset:** "Student Discipline"
- **Source:** E2C Hub
- **Contains:**
  - Discipline incident counts
  - Suspension and expulsion rates
  - Breakdowns by student group and incident type
- **Years Available:** Multi-year dataset (filtered to 2020-2024 for project)
- **Downloaded:** Full dataset (all MA districts)

#### Student Mobility Rate (E2C Hub)
**Dataset:** "Student Mobility Rate"
- **Source:** E2C Hub
- **Contains:**
  - Student mobility rates (students entering/leaving district mid-year)
  - Stability indicators
  - Breakdowns by student group
- **Years Available:** Multi-year dataset (filtered to 2020-2024 for project)
- **Downloaded:** Full dataset (all MA districts)

#### Class Size (E2C Hub)
**Dataset:** "Class Size by Gender, Race, Ethnicity and Selected Populations" (35yv-uxv5)
- **Source:** https://educationtocareer.data.mass.gov/Students-and-Teachers/Class-Size-by-Gender-Race-Ethnicity-and-Selected-P/35yv-uxv5
- **Contains:**
  - Average class sizes by grade level
  - Breakdowns by gender, race/ethnicity, and selected populations
- **Years Available:** Multi-year dataset (filtered to 2020-2024 for project)
- **Granularity:** District and School levels

#### Financial Data (E2C Hub)
**Dataset:** "District Expenditures by Spending Category"
- **Source:** E2C Hub (dataset ID to be confirmed)
- **Contains:**
  - Spending by category (instruction, administration, transportation, etc.)
  - Total expenditures
  - Can derive per-pupil spending by combining with enrollment data
- **Replaces:** Per Pupil Expenditure Excel reports (which only go to 2023)
- **Years Available:** Multi-year dataset (filtered to 2020-2024 for project)

#### Accountability Data (DESE Profiles - Excel Fallback)
**Report:** Accountability Report
- **Source:** https://profiles.doe.mass.edu/statereport/accountability.aspx
- **Format:** Excel files (manual download)
- **Reason:** Not available as consolidated dataset on E2C Hub
- **Contains:**
  - Overall accountability percentages
  - Meeting/Exceeding targets
  - Progress metrics
- **Download Approach:** 
  - Filter: District = Boston
  - Years: 2020-2024 (5 files)
  - Manual download and processing

## Data Collection Implementation

### Strategy: Direct CSV Downloads from E2C Hub

#### Phase 1: Download E2C Hub Datasets (Week 1)

**Process:**
1. Navigate to E2C Hub dataset page in web browser
2. If dataset triggers "large dataset warning":
   - Click "Filter" button
   - Apply filter: `DISTRICT_NAME = "Boston"`
3. Click "Export" button
4. Select "CSV" format
5. Download file
6. Save to appropriate `/data/raw/` directory

**Datasets Filtered Before Download (Large Files):**
- MCAS Achievement Results (i9w6-niyt)
- Class Size by Gender, Race, Ethnicity and Selected Populations (35yv-uxv5)

**Datasets Downloaded in Full (Smaller Files):**
- Enrollment - Grade, Race, Ethnicity, Gender and Selected Populations (t8td-gens)
- High School Graduation Rates (n2xa-p822)
- Student Attrition
- Student Attendance
- Student Discipline
- Student Mobility Rate
- District Expenditures by Spending Category

**Benefits:**
- ✅ Flexibility: Unfiltered datasets allow for state-level comparisons if needed
- ✅ Pragmatic: Only filter when necessary due to file size
- ✅ Single file per report type (vs. 5 files per report for year-by-year)
- ✅ Clean, machine-readable CSV format
- ✅ No Excel formatting issues to resolve
- ✅ Consistent data structure across years
- ✅ Manual process is time-efficient (under 1 hour for all downloads)

**File Organization Structure:**
```
/data/
├── raw/
│   ├── accountability_report/
│   │   ├── accountability_2020.xlsx
│   │   ├── accountability_2021.xlsx
│   │   ├── accountability_2022.xlsx
│   │   ├── accountability_2023.xlsx
│   │   ├── accountability_2024.xlsx
│   │   └── accountability_2025.xlsx
│   ├── class_size/
│   │   └── Class_Size_by_Gender_Race_Ethnicity_and_Selected_Populations_20251204.csv
│   ├── district_expenditures_spending_category/
│   │   └── District_Expenditures_by_Spending_Category_20251204.csv
│   ├── enrollment/
│   │   └── Enrollment_Grade_Race_Ethnicity_Gender_and_Selected_Populations_20251204.csv
│   ├── graduation_rates/
│   │   └── High_School_Graduation_Rates_20251204.csv
│   ├── mcas_achievement_results/
│   │   ├── MCAS_Achievement_Results_20251204.csv
│   │   └── School and District Profiles - Massachusetts Department of Elementary and Secondary Education.pdf
│   ├── student_attendance/
│   │   └── Student_Attendance_20251204.csv
│   ├── student_attrition/
│   │   └── Student_Attrition_20251204.csv
│   ├── student_discipline/
│   │   └── Student_Discipline_20251204.csv
│   └── student_mobility_rate/
│       └── Student_Mobility_Rate_20251204.csv
└── processed/
    ├── accountability_report/
    ├── class_size/
    ├── district_expenditures/
    ├── enrollment/
    ├── graduation_rates/
    ├── mcas_achievement/
    ├── student_attendance/
    ├── student_attrition/
    ├── student_discipline/
    └── student_mobility_rate/
```

**Notes on File Organization:**
- E2C Hub CSV files include download date in filename (20251204 = December 4, 2025)
- Larger datasets (MCAS, Class Size) filtered to Boston before download
- Smaller datasets downloaded in full, will be filtered during Python processing
- Accountability reports remain as separate Excel files by year (not available on E2C Hub)
- PDF documentation file included with MCAS data for reference

#### Phase 2: Data Preparation (Week 1-2)

**Minimal Processing Approach:**

Since E2C Hub CSVs are clean and PyCharm's import tool handles basic data type conversions, processing is minimal:

1. **For Pre-Filtered CSVs** (MCAS, Class Size):
   - Already filtered to Boston
   - Ready for direct import

2. **For Full-State CSVs** (Enrollment, Graduation, etc.):
   - Option A: Filter to Boston using PyCharm's import filters during import
   - Option B: Create simple Python filter script if needed:
     ```python
     import pandas as pd
     
     df = pd.read_csv('Enrollment_Full.csv', dtype=str)
     df_boston = df[df['DIST_NAME'] == 'Boston']
     df_boston.to_csv('Enrollment_Boston.csv', index=False)
     ```

3. **For Accountability Excel Files**:
   - Use pandas to read Excel → export as CSV for PyCharm import
   - Or import directly if PyCharm supports .xlsx

4. **Data Type Handling**:
   - PyCharm import wizard handles most type conversions
   - Only create cleaning scripts if import fails with specific errors

**Processing Scripts Created As Needed:**
- Store in `/scripts/data_processing/`
- Document any transformations applied
- Keep scripts simple and focused on specific issues

**Philosophy:** Start with direct import, only add processing when necessary. Avoid premature optimization of ETL pipeline.

#### Phase 3: Load to Supabase (Week 2)

**Selected Method: PyCharm Database Tool CSV Import**

**Process:**
1. Design database schema (see schema.sql)
2. Connect PyCharm to Supabase PostgreSQL database
   - Host: [project].supabase.co
   - Port: 5432
   - Database: postgres
   - Credentials from Supabase Dashboard
3. Create tables using SQL schema file
4. Use PyCharm's "Import Data from File" feature:
   - Right-click table → Import Data from File
   - Select corresponding CSV file
   - Map CSV columns to table columns
   - Execute import
5. Verify data loaded correctly with test queries

**Why PyCharm Database Tool:**
- ✅ **Integrated workflow** - Already using PyCharm for development
- ✅ **Visual interface** - See column mappings and preview data
- ✅ **No custom scripts needed** - Built-in PostgreSQL import functionality
- ✅ **Perfect for one-time load** - Data doesn't change frequently
- ✅ **Professional Edition feature** - Available in PyCharm Professional
- ✅ **Direct PostgreSQL connection** - Supabase is PostgreSQL-compatible

**Alternative Methods (if needed):**
1. **Python Script with supabase-py:** For complex data transformations or cleaning
2. **Supabase Dashboard Import:** Browser-based CSV upload if PyCharm unavailable
3. **n8n Workflow:** Only if implementing automated refresh mechanism

**Data Preparation:**
- Most E2C Hub CSVs are clean and ready for direct import
- If import issues occur (data type mismatches, formatting), create minimal Python cleaning script
- Document any data transformations in processing notes

### Rationale for Updated Approach

**Why E2C Hub Instead of Year-by-Year Excel Downloads:**
- **Efficiency:** Single CSV download vs. 5+ Excel files per report type
- **Data Quality:** Pre-cleaned, standardized format eliminates Excel formatting issues
- **Consistency:** All years use identical schema and field definitions
- **Maintainability:** Future updates only require re-downloading one file per report
- **Demonstrates Best Practices:** Using official data portals instead of manual exports

**Why Some Reports Still Manual (Accountability):**
- Not all DESE reports have been migrated to E2C Hub yet
- Excel download remains necessary for gaps in E2C Hub coverage
- Hybrid approach balances efficiency with comprehensive data collection

**Why PyCharm Database Tool for Data Loading:**
- **Integrated Development Environment:** No context switching from coding to data loading
- **Visual Import Interface:** Preview data and map columns before import
- **One-Time Load Appropriate:** Data is historical and doesn't require frequent updates
- **Reduces Complexity:** Focuses development time on dashboard functionality rather than ETL scripts
- **Professional Tooling:** Leverages PyCharm Professional's built-in database features

**Why n8n is Optional:**
- Primary focus is dashboard functionality, not ETL automation
- PyCharm import provides sufficient capability for one-time data load
- n8n demonstrates technical capability if time permits in Week 3-4
- Can be added as enhancement for production deployment with scheduled refreshes

## Data Dictionary Summary

### Key Fields Across Datasets

**Enrollment Dataset:**
- `SY`: School Year (e.g., "2024" for 2023-2024 school year)
- `DIST_CODE`, `DIST_NAME`: District identifiers
- `ORG_CODE`, `ORG_NAME`, `ORG_TYPE`: Organization identifiers (District or School)
- `TOTAL_CNT`: Total enrollment count
- `[GRADE]_CNT`: Enrollment count by grade (PK_CNT, K_CNT, G1_CNT, etc.)
- `[RACE]_PCT`: Percentage by race/ethnicity (AIAN_PCT, AS_PCT, BAA_PCT, HL_PCT, etc.)
- `FE_PCT`, `MA_PCT`, `NB_PCT`: Gender percentages
- `EL_CNT`, `EL_PCT`: English Learner counts and percentages
- `HN_CNT`, `HN_PCT`: High Needs counts and percentages
- `ECD_CNT`, `ECD_PCT`: Economically Disadvantaged counts and percentages
- `SWD_CNT`, `SWD_PCT`: Students with Disabilities counts and percentages

**MCAS Dataset:**
- `DISTRICT_NAME`, `SCHOOL_NAME`: Location identifiers
- `SCHOOL_YEAR`: Academic year
- `SUBJECT`: ELA, Math, or Science
- `GRADE`: Grade level tested
- `STUDENT_GROUP`: All Students or demographic subgroup
- `PCT_MEETING_EXCEEDING`: Percentage meeting or exceeding expectations
- `PARTICIPATION_RATE`: Test participation percentage
- `AVG_SCALED_SCORE`: Average student score
- `AVG_SGP`: Average Student Growth Percentile

**Graduation Rates Dataset:**
- `COHORT_YEAR`: Graduation cohort year
- `FOUR_YEAR_GRAD_RATE`: 4-year graduation rate percentage
- `FIVE_YEAR_GRAD_RATE`: 5-year graduation rate percentage
- `STUDENT_GROUP`: Demographic or program subgroup

## Data Quality Considerations

### Known Data Limitations

1. **COVID-19 Impact (2020-2021):**
   - Enrollment declines due to pandemic
   - MCAS testing disruptions
   - Attendance data anomalies
   - Dashboard should note pandemic context in visualizations

2. **Economically Disadvantaged Definition Change:**
   - "Low Income" used pre-2015 and 2022+
   - "Economically Disadvantaged" used 2015-2021
   - Not directly comparable across definition changes
   - See DESE Researcher's Guide for details

3. **Small Sample Sizes:**
   - Some student groups may have <6 students
   - Data suppressed for privacy (appears as null/blank)
   - Affects some school-level analyses

4. **School Openings/Closures:**
   - Schools may not have data for all years
   - New schools appear mid-period
   - Closed schools drop from dataset
   - Requires handling null/missing school-year combinations

### Data Validation Steps

1. **Completeness Checks:**
   - Verify all 5 years present for each dataset
   - Check for Boston district record in each year
   - Validate expected school counts (~109-117 schools)

2. **Consistency Checks:**
   - Enrollment totals match sum of grade-level counts
   - Percentages sum to 100% where applicable
   - Cross-reference enrollment with MCAS participation

3. **Range Checks:**
   - Percentages between 0-100%
   - Counts are non-negative integers
   - Dates/years in expected range

## Future Extensibility

### Potential Enhancements

1. **Additional Years:**
   - E2C Hub datasets extend back to 1990s
   - Can incorporate historical trends if desired
   - Same processing scripts work for any year range

2. **Statewide Comparisons:**
   - Download without district filter
   - Compare Boston to other MA districts
   - Benchmark against state averages

3. **School-Level Drill-Downs:**
   - All datasets include school-level data
   - Can add school comparison features
   - Enable principal/administrator use cases

4. **API Integration (Future Enhancement):**
   - E2C Hub built on Socrata platform with REST API support
   - Could automate data refreshes via API calls instead of manual downloads
   - Would require API key registration and implementation
   - Optional enhancement for production deployment

5. **Additional Metrics:**
   - E2C Hub has 100+ datasets
   - Can add: teacher data, course-taking, college enrollment, earnings
   - Expand dashboard scope based on stakeholder feedback

## References

- **E2C Hub:** https://educationtocareer.data.mass.gov/
- **DESE Profiles:** https://profiles.doe.mass.edu/
- **DESE Researcher's Guide:** https://www.doe.mass.edu/infoservices/research/
- **Socrata API Documentation:** https://dev.socrata.com/