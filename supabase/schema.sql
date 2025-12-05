-- ============================================================================
-- BPS ENROLLMENT DASHBOARD - DATABASE SCHEMA
-- ============================================================================
-- Purpose: PostgreSQL schema for Boston Public Schools enrollment dashboard
-- Database: Supabase (PostgreSQL 15+)
-- Design: Star schema with dimension tables and fact tables per data source
-- Naming: snake_case for all tables and columns
-- ============================================================================

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Schools Dimension Table
-- -----------------------------------------------------------------------------
-- Purpose: Master table for all schools and districts in the dataset
-- Grain: One row per unique school/district organization
-- Notes: ORG_TYPE can be 'School', 'District', 'State'
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schools (
    school_id TEXT PRIMARY KEY,  -- Maps to ORG_CODE from CSV
    school_name TEXT NOT NULL,   -- Maps to ORG_NAME from CSV
    district_code TEXT NOT NULL, -- Maps to DIST_CODE from CSV
    district_name TEXT NOT NULL, -- Maps to DIST_NAME from CSV
    org_type TEXT NOT NULL,      -- 'School', 'District', or 'State'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_org_type CHECK (org_type IN ('School', 'District', 'State'))
);

-- Indexes for schools dimension
CREATE INDEX idx_schools_district ON schools(district_code);
CREATE INDEX idx_schools_org_type ON schools(org_type);
CREATE INDEX idx_schools_name ON schools(school_name); -- For autocomplete/search

-- Comments for schools table
COMMENT ON TABLE schools IS 'Dimension table containing all schools and districts in the dataset';
COMMENT ON COLUMN schools.school_id IS 'Unique identifier for school/district (ORG_CODE from DESE)';
COMMENT ON COLUMN schools.org_type IS 'Type of organization: School, District, or State';


-- ============================================================================
-- FACT TABLES - ENROLLMENT & DEMOGRAPHICS
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Enrollment Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store enrollment counts by grade, race/ethnicity, gender, and populations
-- Grain: One row per school per year
-- Source: Enrollment__Grade,_Race_Ethnicity,_Gender,_and_Selected_Populations_20251204.csv
-- Notes:
--   - Contains grade-level enrollment (PK through Grade 12)
--   - Demographic percentages (race/ethnicity)
--   - Gender counts and percentages
--   - Selected populations (EL, FLNE, HN, LI, ECD, SWD)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enrollment (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,        -- Maps to SY (e.g., 2025)
    school_id TEXT NOT NULL REFERENCES schools(school_id),

    -- Grade-level enrollment counts
    total_enrollment INTEGER,            -- TOTAL_CNT
    pk_count INTEGER,                    -- PK_CNT (Pre-Kindergarten)
    k_count INTEGER,                     -- K_CNT (Kindergarten)
    grade_1_count INTEGER,               -- G1_CNT
    grade_2_count INTEGER,               -- G2_CNT
    grade_3_count INTEGER,               -- G3_CNT
    grade_4_count INTEGER,               -- G4_CNT
    grade_5_count INTEGER,               -- G5_CNT
    grade_6_count INTEGER,               -- G6_CNT
    grade_7_count INTEGER,               -- G7_CNT
    grade_8_count INTEGER,               -- G8_CNT
    grade_9_count INTEGER,               -- G9_CNT
    grade_10_count INTEGER,              -- G10_CNT
    grade_11_count INTEGER,              -- G11_CNT
    grade_12_count INTEGER,              -- G12_CNT
    sp_count INTEGER,                    -- SP_CNT (Special Program)

    -- Race/Ethnicity percentages
    american_indian_pct DECIMAL(5,2),    -- AIAN_PCT
    asian_pct DECIMAL(5,2),              -- AS_PCT
    black_african_american_pct DECIMAL(5,2), -- BAA_PCT
    hispanic_latino_pct DECIMAL(5,2),    -- HL_PCT
    multi_race_non_hisp_pct DECIMAL(5,2), -- MNHL_PCT
    native_hawaiian_pacific_pct DECIMAL(5,2), -- NHPI_PCT
    white_pct DECIMAL(5,2),              -- WH_PCT

    -- Gender
    female_pct DECIMAL(5,2),             -- FE_PCT
    male_pct DECIMAL(5,2),               -- MA_PCT
    non_binary_pct DECIMAL(5,2),         -- NB_PCT

    -- Selected Populations (counts and percentages)
    english_learner_count INTEGER,       -- EL_CNT
    english_learner_pct DECIMAL(5,2),    -- EL_PCT
    former_english_learner_count INTEGER, -- FLNE_CNT
    former_english_learner_pct DECIMAL(5,2), -- FLNE_PCT
    high_needs_count INTEGER,            -- HN_CNT
    high_needs_pct DECIMAL(5,2),         -- HN_PCT
    low_income_count INTEGER,            -- LI_CNT
    low_income_pct DECIMAL(5,2),         -- LI_PCT
    economically_disadvantaged_count INTEGER, -- ECD_CNT
    economically_disadvantaged_pct DECIMAL(5,2), -- ECD_PCT
    students_with_disabilities_count INTEGER, -- SWD_CNT
    students_with_disabilities_pct DECIMAL(5,2), -- SWD_PCT

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_enrollment_school_year UNIQUE(school_id, school_year)
);

-- Indexes for enrollment queries
CREATE INDEX idx_enrollment_school_year ON enrollment(school_id, school_year);
CREATE INDEX idx_enrollment_year ON enrollment(school_year);
CREATE INDEX idx_enrollment_high_needs ON enrollment(high_needs_pct) WHERE high_needs_pct IS NOT NULL;
CREATE INDEX idx_enrollment_total ON enrollment(total_enrollment) WHERE total_enrollment IS NOT NULL;

COMMENT ON TABLE enrollment IS 'Fact table containing enrollment counts by grade, demographics, and selected populations';


-- ============================================================================
-- FACT TABLES - ACADEMIC PERFORMANCE
-- ============================================================================

-- -----------------------------------------------------------------------------
-- MCAS Results Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store MCAS test achievement results
-- Grain: One row per school per year per grade per subject per student group
-- Source: MCAS_Achievement_Results_20251204.csv
-- Notes: Contains performance levels (M+E, E, M, PM, NM) and scaled scores
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mcas_results (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,
    school_id TEXT NOT NULL REFERENCES schools(school_id),
    test_grade TEXT NOT NULL,            -- TEST_GRADE (e.g., '05', '06')
    subject_code TEXT NOT NULL,          -- SUBJECT_CODE (ELA, MTH, SCI)
    student_group TEXT NOT NULL,         -- STU_GRP (demographics)

    -- Performance level counts and percentages
    meeting_exceeding_count INTEGER,     -- M_PLUS_E_CNT
    meeting_exceeding_pct DECIMAL(5,2),  -- M_PLUS_E_PCT
    exceeding_count INTEGER,             -- E_CNT
    exceeding_pct DECIMAL(5,2),          -- E_PCT
    meeting_count INTEGER,               -- M_CNT
    meeting_pct DECIMAL(5,2),            -- M_PCT
    partially_meeting_count INTEGER,     -- PM_CNT
    partially_meeting_pct DECIMAL(5,2),  -- PM_PCT
    not_meeting_count INTEGER,           -- NM_CNT
    not_meeting_pct DECIMAL(5,2),        -- NM_PCT

    -- Test participation and scores
    student_count INTEGER,               -- STU_CNT
    student_participation_pct DECIMAL(5,2), -- STU_PART_PCT
    avg_scaled_score DECIMAL(6,2),       -- AVG_SCALED_SCORE
    avg_student_growth_percentile DECIMAL(5,2), -- AVG_SGP
    avg_sgp_included DECIMAL(5,2),       -- AVG_SGP_INCL
    achievement_percentile INTEGER,      -- ACH_PERCENTILE

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_mcas_result UNIQUE(school_id, school_year, test_grade, subject_code, student_group)
);

-- Indexes for MCAS queries
CREATE INDEX idx_mcas_school_year ON mcas_results(school_id, school_year);
CREATE INDEX idx_mcas_subject ON mcas_results(subject_code);
CREATE INDEX idx_mcas_grade ON mcas_results(test_grade);
CREATE INDEX idx_mcas_student_group ON mcas_results(student_group);
CREATE INDEX idx_mcas_proficiency ON mcas_results(meeting_exceeding_pct) WHERE meeting_exceeding_pct IS NOT NULL;

COMMENT ON TABLE mcas_results IS 'Fact table containing MCAS test achievement results by grade, subject, and student group';


-- -----------------------------------------------------------------------------
-- Graduation Rates Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store high school graduation rates and outcomes
-- Grain: One row per school per year per graduation rate type per student group
-- Source: High_School_Graduation_Rates_20251204.csv
-- Notes: Includes 4-year, 5-year, and 6-year graduation rates
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS graduation_rates (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,       -- SY (cohort year)
    school_id TEXT NOT NULL REFERENCES schools(school_id),
    graduation_rate_type TEXT NOT NULL, -- GRAD_RATE_TYPE (4-Year, 5-Year, 6-Year)
    student_group TEXT NOT NULL,        -- STU_GRP

    cohort_count INTEGER,               -- COHORT_CNT
    graduated_pct DECIMAL(5,2),         -- GRAD_PCT
    still_in_school_pct DECIMAL(5,2),   -- IN_SCH_PCT
    non_grad_completer_pct DECIMAL(5,2), -- NON_GRAD_PCT
    ged_pct DECIMAL(5,2),               -- GED_PCT
    dropout_pct DECIMAL(5,2),           -- DRPOUT_PCT
    excluded_pct DECIMAL(5,2),          -- EXCLUD_PCT

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_graduation_rate UNIQUE(school_id, school_year, graduation_rate_type, student_group),
    CONSTRAINT chk_grad_rate_type CHECK (graduation_rate_type IN ('4-Year Graduation Rate', '5-Year Graduation Rate', '6-Year Graduation Rate'))
);

-- Indexes for graduation queries
CREATE INDEX idx_graduation_school_year ON graduation_rates(school_id, school_year);
CREATE INDEX idx_graduation_type ON graduation_rates(graduation_rate_type);
CREATE INDEX idx_graduation_student_group ON graduation_rates(student_group);
CREATE INDEX idx_graduation_rate ON graduation_rates(graduated_pct) WHERE graduated_pct IS NOT NULL;

COMMENT ON TABLE graduation_rates IS 'Fact table containing high school graduation rates and outcomes';


-- ============================================================================
-- FACT TABLES - SCHOOL ENVIRONMENT
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Class Size Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store class size statistics by subject and demographics
-- Grain: One row per school per year per subject
-- Source: Class_Size_by_Gender,_Race_Ethnicity,_and_Selected_Populations_20251204.csv
-- Notes: Contains average class size and demographic breakdowns
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS class_size (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,
    school_id TEXT NOT NULL REFERENCES schools(school_id),
    subject TEXT NOT NULL,              -- SUBJ

    total_classes_count INTEGER,        -- TOT_CLSS_CNT
    avg_class_size DECIMAL(5,2),        -- AVG_CLSS_CNT
    total_students_count INTEGER,       -- TOT_STU_CNT

    -- Demographic percentages in classes
    american_indian_pct DECIMAL(5,2),   -- AIAN_PCT
    asian_pct DECIMAL(5,2),             -- AS_PCT
    black_african_american_pct DECIMAL(5,2), -- BAA_PCT
    hispanic_latino_pct DECIMAL(5,2),   -- HL_PCT
    multi_race_non_hisp_pct DECIMAL(5,2), -- MNHL_PCT
    native_hawaiian_pacific_pct DECIMAL(5,2), -- NHPI_PCT
    white_pct DECIMAL(5,2),             -- WH_PCT
    female_pct DECIMAL(5,2),            -- FE_PCT
    male_pct DECIMAL(5,2),              -- MA_PCT
    english_learner_pct DECIMAL(5,2),   -- EL_PCT
    low_income_pct DECIMAL(5,2),        -- LI_PCT
    economically_disadvantaged_pct DECIMAL(5,2), -- ECD_PCT
    students_with_disabilities_pct DECIMAL(5,2), -- SWD_PCT

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_class_size UNIQUE(school_id, school_year, subject)
);

-- Indexes for class size queries
CREATE INDEX idx_class_size_school_year ON class_size(school_id, school_year);
CREATE INDEX idx_class_size_subject ON class_size(subject);
CREATE INDEX idx_class_size_avg ON class_size(avg_class_size) WHERE avg_class_size IS NOT NULL;

COMMENT ON TABLE class_size IS 'Fact table containing class size statistics by subject and demographics';


-- -----------------------------------------------------------------------------
-- Student Attendance Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store attendance rates and chronic absenteeism
-- Grain: One row per school per year per attendance period per student group
-- Source: Student_Attendance_20251204.csv
-- Notes: Can have multiple periods per year (End of Year, March, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,
    attendance_period TEXT NOT NULL,     -- ATTEND_PERIOD (e.g., 'End of Year', 'March')
    school_id TEXT NOT NULL REFERENCES schools(school_id),
    student_group TEXT NOT NULL,         -- STU_GRP

    attendance_rate DECIMAL(5,2),        -- ATTEND_RATE
    avg_days_absent DECIMAL(5,2),        -- CNT_AVG_ABS
    absent_10plus_days_pct DECIMAL(5,2), -- PCT_ABS_10_DAYS
    chronic_absent_10_pct DECIMAL(5,2),  -- PCT_CHRON_ABS_10
    chronic_absent_20_pct DECIMAL(5,2),  -- PCT_CHRON_ABS_20
    unexcused_absent_10_pct DECIMAL(5,2), -- PCT_UNEXC_10_DAYS

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_attendance UNIQUE(school_id, school_year, attendance_period, student_group)
);

-- Indexes for attendance queries
CREATE INDEX idx_attendance_school_year ON attendance(school_id, school_year);
CREATE INDEX idx_attendance_period ON attendance(attendance_period);
CREATE INDEX idx_attendance_student_group ON attendance(student_group);
CREATE INDEX idx_attendance_rate ON attendance(attendance_rate) WHERE attendance_rate IS NOT NULL;
CREATE INDEX idx_attendance_chronic ON attendance(chronic_absent_10_pct) WHERE chronic_absent_10_pct IS NOT NULL;

COMMENT ON TABLE attendance IS 'Fact table containing attendance rates and chronic absenteeism data';


-- -----------------------------------------------------------------------------
-- Student Attrition Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store student attrition rates by grade level
-- Grain: One row per school per year per student group
-- Source: Student_Attrition_20251204.csv
-- Notes: Contains attrition percentages for each grade (K-12) and overall
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attrition (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,
    school_id TEXT NOT NULL REFERENCES schools(school_id),
    student_group TEXT NOT NULL,        -- STU_GRP

    -- Attrition percentages by grade
    kindergarten_pct DECIMAL(5,2),      -- GK_PCT
    grade_1_pct DECIMAL(5,2),           -- G01_PCT
    grade_2_pct DECIMAL(5,2),           -- G02_PCT
    grade_3_pct DECIMAL(5,2),           -- G03_PCT
    grade_4_pct DECIMAL(5,2),           -- G04_PCT
    grade_5_pct DECIMAL(5,2),           -- G05_PCT
    grade_6_pct DECIMAL(5,2),           -- G06_PCT
    grade_7_pct DECIMAL(5,2),           -- G07_PCT
    grade_8_pct DECIMAL(5,2),           -- G08_PCT
    grade_9_pct DECIMAL(5,2),           -- G09_PCT
    grade_10_pct DECIMAL(5,2),          -- G10_PCT
    grade_11_pct DECIMAL(5,2),          -- G11_PCT
    grade_all_pct DECIMAL(5,2),         -- GRD_ALL

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_attrition UNIQUE(school_id, school_year, student_group)
);

-- Indexes for attrition queries
CREATE INDEX idx_attrition_school_year ON attrition(school_id, school_year);
CREATE INDEX idx_attrition_student_group ON attrition(student_group);
CREATE INDEX idx_attrition_overall ON attrition(grade_all_pct) WHERE grade_all_pct IS NOT NULL;

COMMENT ON TABLE attrition IS 'Fact table containing student attrition rates by grade level';


-- -----------------------------------------------------------------------------
-- Student Mobility Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store student mobility and stability rates
-- Grain: One row per school per year per student group
-- Source: Student_Mobility_Rate_20251204.csv
-- Notes: Tracks student churn, intake, and stability
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mobility (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,
    school_id TEXT NOT NULL REFERENCES schools(school_id),
    student_group TEXT NOT NULL,        -- STU_GRP

    churn_enrollment_count INTEGER,     -- CHURN_ENROLL_CNT
    churn_pct DECIMAL(5,2),             -- CHURN_PCT
    intake_pct DECIMAL(5,2),            -- INTAKE_PCT
    stable_enrollment_count INTEGER,    -- STAB_ENROLL_CNT
    stability_pct DECIMAL(5,2),         -- STAB_PCT

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_mobility UNIQUE(school_id, school_year, student_group)
);

-- Indexes for mobility queries
CREATE INDEX idx_mobility_school_year ON mobility(school_id, school_year);
CREATE INDEX idx_mobility_student_group ON mobility(student_group);
CREATE INDEX idx_mobility_stability ON mobility(stability_pct) WHERE stability_pct IS NOT NULL;

COMMENT ON TABLE mobility IS 'Fact table containing student mobility and stability metrics';


-- -----------------------------------------------------------------------------
-- Student Discipline Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store disciplinary incident data
-- Grain: One row per school per year per student group per offense type
-- Source: Student_Discipline_20251204.csv
-- Notes: Contains counts of students and incidents, plus discipline type percentages
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS discipline (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,
    school_id TEXT NOT NULL REFERENCES schools(school_id),
    student_group TEXT NOT NULL,        -- STU_GRP
    offense_type TEXT NOT NULL,         -- OFFENSE

    student_count INTEGER,              -- STU_CNT (total students in group)
    students_disciplined_count INTEGER, -- STU_DISCIPL_CNT
    in_school_suspension_pct DECIMAL(5,2),    -- IN_SUSP_PCT
    out_of_school_suspension_pct DECIMAL(5,2), -- OUT_SUSP_PCT
    expulsion_pct DECIMAL(5,2),         -- EXP_PCT
    alternative_setting_pct DECIMAL(5,2), -- ALT_SETTING_PCT
    emergency_removal_pct DECIMAL(5,2), -- EMERG_RMVL_PCT
    arrest_pct DECIMAL(5,2),            -- ARREST_PCT
    law_enforcement_referral_pct DECIMAL(5,2), -- LAWENF_REF_PCT

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_discipline UNIQUE(school_id, school_year, student_group, offense_type)
);

-- Indexes for discipline queries
CREATE INDEX idx_discipline_school_year ON discipline(school_id, school_year);
CREATE INDEX idx_discipline_student_group ON discipline(student_group);
CREATE INDEX idx_discipline_offense ON discipline(offense_type);

COMMENT ON TABLE discipline IS 'Fact table containing disciplinary incident data by offense type';


-- ============================================================================
-- FACT TABLES - FINANCIAL
-- ============================================================================

-- -----------------------------------------------------------------------------
-- Expenditures Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store district expenditure data by spending category
-- Grain: One row per district per year per spending indicator/category
-- Source: District_Expenditures_by_Spending_Category_20251204.csv
-- Notes: This is district-level only (not school-level)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expenditures (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,
    district_code TEXT NOT NULL,        -- DIST_CODE
    district_name TEXT NOT NULL,        -- DIST_NAME
    indicator_category TEXT NOT NULL,   -- IND_CAT (e.g., 'Student Enrollment')
    indicator_subcategory TEXT NOT NULL, -- IND_SUBCAT (e.g., 'In-District FTE Pupils')
    indicator_value DECIMAL(15,2),      -- IND_VALUE
    indicator_value_type TEXT NOT NULL, -- IND_VALUE_TYPE (e.g., 'Count', 'Dollars', 'Percent')

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_expenditure UNIQUE(district_code, school_year, indicator_category, indicator_subcategory)
);

-- Indexes for expenditure queries
CREATE INDEX idx_expenditure_district_year ON expenditures(district_code, school_year);
CREATE INDEX idx_expenditure_category ON expenditures(indicator_category);
CREATE INDEX idx_expenditure_subcategory ON expenditures(indicator_subcategory);

COMMENT ON TABLE expenditures IS 'Fact table containing district expenditure data by spending category';
COMMENT ON COLUMN expenditures.indicator_value_type IS 'Type of value: Count, Dollars, Percent, or Ratio';


-- -----------------------------------------------------------------------------
-- Accountability Fact Table
-- -----------------------------------------------------------------------------
-- Purpose: Store district accountability ratings and classifications
-- Grain: One row per district per year
-- Source: accountability_YYYY.xlsx files converted to CSV (2020-2025)
-- Notes:
--   - Data is DISTRICT-LEVEL only (not individual schools)
--   - Column name for progress metric varies by year:
--     * 2020-2021: "Overall Improvement Toward Improvement Targets (%)"
--     * 2022: "Progress Toward Improvement Targets (%)"
--     * 2023-2025: "Cumulative Progress Toward Improvement Targets (%)"
--   - All should be loaded into progress_toward_targets_pct column
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accountability (
    id BIGSERIAL PRIMARY KEY,
    school_year INTEGER NOT NULL,
    district_code TEXT NOT NULL,        -- Maps to District Code from CSV
    district_name TEXT NOT NULL,        -- Maps to District Name from CSV

    -- Accountability classification
    overall_classification TEXT NOT NULL, -- "Not requiring assistance or intervention" or "Requiring assistance or intervention"
    reason_for_classification TEXT,     -- e.g., "Substantial progress toward targets", "Meeting or exceeding targets", etc.

    -- Progress metric (column name varies by year, but all go here)
    progress_toward_targets_pct DECIMAL(5,2), -- Can be NULL (some districts have no value)

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_accountability UNIQUE(district_code, school_year),
    CONSTRAINT chk_overall_classification CHECK (
        overall_classification IN (
            'Not requiring assistance or intervention',
            'Requiring assistance or intervention'
        )
    )
);

-- Indexes for accountability queries
CREATE INDEX idx_accountability_district_year ON accountability(district_code, school_year);
CREATE INDEX idx_accountability_year ON accountability(school_year);
CREATE INDEX idx_accountability_classification ON accountability(overall_classification);
CREATE INDEX idx_accountability_progress ON accountability(progress_toward_targets_pct) WHERE progress_toward_targets_pct IS NOT NULL;

COMMENT ON TABLE accountability IS 'Fact table containing district-level accountability ratings and classifications';
COMMENT ON COLUMN accountability.overall_classification IS 'Whether district requires assistance or intervention';
COMMENT ON COLUMN accountability.reason_for_classification IS 'Reason category for classification (e.g., meeting targets, in need of support)';
COMMENT ON COLUMN accountability.progress_toward_targets_pct IS 'Progress toward improvement targets (column name varies by year in source data)';


-- ============================================================================
-- UTILITY FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for schools table
CREATE TRIGGER update_schools_updated_at
    BEFORE UPDATE ON schools
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- Note: RLS policies depend on your authentication requirements
-- For now, assuming public read access for dashboard
-- Uncomment and customize if you need authentication

-- Enable RLS on tables
-- ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE enrollment ENABLE ROW LEVEL SECURITY;
-- ... etc for other tables

-- Example policy for public read access
-- CREATE POLICY "Public read access" ON schools FOR SELECT USING (true);
-- CREATE POLICY "Public read access" ON enrollment FOR SELECT USING (true);


-- ============================================================================
-- DATA QUALITY VIEWS (OPTIONAL)
-- ============================================================================

-- View to identify schools with data for each year
CREATE OR REPLACE VIEW school_data_coverage AS
SELECT
    s.school_id,
    s.school_name,
    s.district_name,
    s.org_type,
    COALESCE(e.years_with_enrollment, 0) as years_with_enrollment,
    COALESCE(m.years_with_mcas, 0) as years_with_mcas,
    COALESCE(a.years_with_attendance, 0) as years_with_attendance
FROM schools s
LEFT JOIN (
    SELECT school_id, COUNT(DISTINCT school_year) as years_with_enrollment
    FROM enrollment GROUP BY school_id
) e ON s.school_id = e.school_id
LEFT JOIN (
    SELECT school_id, COUNT(DISTINCT school_year) as years_with_mcas
    FROM mcas_results GROUP BY school_id
) m ON s.school_id = m.school_id
LEFT JOIN (
    SELECT school_id, COUNT(DISTINCT school_year) as years_with_attendance
    FROM attendance GROUP BY school_id
) a ON s.school_id = a.school_id;

COMMENT ON VIEW school_data_coverage IS 'View showing which schools have data in each fact table across years';


-- ============================================================================
-- HELPFUL QUERIES FOR DASHBOARD DEVELOPMENT
-- ============================================================================

-- Query 1: Get all schools with enrollment for a specific year
-- SELECT * FROM enrollment e
-- JOIN schools s ON e.school_id = s.school_id
-- WHERE e.school_year = 2025 AND s.org_type = 'School';

-- Query 2: Compare school vs district averages
-- SELECT
--   s.school_name,
--   e.high_needs_pct as school_high_needs_pct,
--   d.high_needs_pct as district_high_needs_pct
-- FROM enrollment e
-- JOIN schools s ON e.school_id = s.school_id
-- JOIN enrollment d ON d.school_id = s.district_code
-- WHERE e.school_year = 2025 AND s.org_type = 'School';

-- Query 3: Enrollment trends over time
-- SELECT school_year, SUM(total_enrollment) as total
-- FROM enrollment
-- WHERE school_id = 'SOME_SCHOOL_ID'
-- GROUP BY school_year
-- ORDER BY school_year;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
