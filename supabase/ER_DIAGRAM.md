# BPS Enrollment Dashboard - Entity Relationship Diagram

## Schema Architecture: Star Schema

This database follows a **star schema** design pattern, optimized for analytical queries and dashboard visualizations.

```
                                    ┌─────────────────────┐
                                    │      SCHOOLS        │
                                    │   (DIMENSION)       │
                                    ├─────────────────────┤
                                    │ PK school_id        │
                                    │    school_name      │
                                    │    district_code    │
                                    │    district_name    │
                                    │    org_type         │
                                    └──────────┬──────────┘
                                               │
                                               │ Referenced by all fact tables
                                               │
           ┌───────────────────────────────────┼───────────────────────────────────┐
           │                                   │                                   │
           │                                   │                                   │
    ┌──────▼──────┐                    ┌──────▼──────┐                    ┌──────▼──────┐
    │ ENROLLMENT  │                    │ MCAS_RESULTS│                    │ GRADUATION  │
    │   (FACT)    │                    │   (FACT)    │                    │   RATES     │
    ├─────────────┤                    ├─────────────┤                    │   (FACT)    │
    │ PK id       │                    │ PK id       │                    ├─────────────┤
    │ FK school_id│                    │ FK school_id│                    │ PK id       │
    │    year     │                    │    year     │                    │ FK school_id│
    │    grades   │                    │    grade    │                    │    year     │
    │    demo %   │                    │    subject  │                    │    type     │
    │    pop %    │                    │    group    │                    │    cohort   │
    └─────────────┘                    │    scores   │                    │    outcomes │
                                       └─────────────┘                    └─────────────┘

           │                                   │                                   │
           │                                   │                                   │
    ┌──────▼──────┐                    ┌──────▼──────┐                    ┌──────▼──────┐
    │ CLASS_SIZE  │                    │ ATTENDANCE  │                    │ ATTRITION   │
    │   (FACT)    │                    │   (FACT)    │                    │   (FACT)    │
    ├─────────────┤                    ├─────────────┤                    ├─────────────┤
    │ PK id       │                    │ PK id       │                    │ PK id       │
    │ FK school_id│                    │ FK school_id│                    │ FK school_id│
    │    year     │                    │    year     │                    │    year     │
    │    subject  │                    │    period   │                    │    group    │
    │    avg_size │                    │    group    │                    │    grades % │
    │    demo %   │                    │    rates    │                    └─────────────┘
    └─────────────┘                    └─────────────┘

           │                                   │                                   │
           │                                   │                                   │
    ┌──────▼──────┐                    ┌──────▼──────┐                    ┌──────▼──────┐
    │  MOBILITY   │                    │ DISCIPLINE  │                    │EXPENDITURES │
    │   (FACT)    │                    │   (FACT)    │                    │   (FACT)    │
    ├─────────────┤                    ├─────────────┤                    ├─────────────┤
    │ PK id       │                    │ PK id       │                    │ PK id       │
    │ FK school_id│                    │ FK school_id│                    │    dist_code│
    │    year     │                    │    year     │                    │    year     │
    │    group    │                    │    group    │                    │    category │
    │    churn %  │                    │    offense  │                    │    value    │
    │    stability│                    │    types %  │                    └─────────────┘
    └─────────────┘                    └─────────────┘
                                                                           ┌─────────────┐
                                                                           │ACCOUNTABIL- │
                                                                           │    ITY      │
                                                                           │   (FACT)    │
                                                                           ├─────────────┤
                                                                           │ PK id       │
                                                                           │ FK school_id│
                                                                           │    year     │
                                                                           │    level    │
                                                                           │    metrics  │
                                                                           └─────────────┘
```

## Table Relationships

### Dimension Tables
- **schools**: Master dimension containing all schools, districts, and state-level aggregates

### Fact Tables (All reference schools dimension)
1. **enrollment**: Grade-level enrollment, demographics, and selected populations
2. **mcas_results**: Test scores by grade, subject, and student group
3. **graduation_rates**: Graduation outcomes for high schools
4. **class_size**: Average class sizes by subject and demographics
5. **attendance**: Attendance rates and chronic absenteeism
6. **attrition**: Student attrition rates by grade level
7. **mobility**: Student mobility and stability metrics
8. **discipline**: Disciplinary incidents by offense type
9. **expenditures**: District-level spending by category
10. **accountability**: School accountability ratings and classifications

## Grain Definitions

| Table | Grain (One row per...) |
|-------|------------------------|
| schools | Unique school/district organization |
| enrollment | School + Year |
| mcas_results | School + Year + Grade + Subject + Student Group |
| graduation_rates | School + Year + Graduation Type + Student Group |
| class_size | School + Year + Subject |
| attendance | School + Year + Period + Student Group |
| attrition | School + Year + Student Group |
| mobility | School + Year + Student Group |
| discipline | School + Year + Student Group + Offense Type |
| expenditures | District + Year + Category + Subcategory |
| accountability | School + Year |

## Key Design Features

### 1. Star Schema Benefits
- **Simple Queries**: Fact tables directly join to dimension (no complex joins)
- **Query Performance**: Optimized for aggregations and filtering
- **Easy to Understand**: Clear separation between dimensions and facts

### 2. Indexing Strategy
- **Primary Keys**: All tables have surrogate keys (BIGSERIAL)
- **Foreign Keys**: Fact tables reference schools via school_id
- **Composite Indexes**: (school_id, school_year) for time-series queries
- **Filter Indexes**: Frequently filtered columns (student_group, subject, grade)
- **Partial Indexes**: Only index non-NULL values for metric columns

### 3. Data Integrity
- **Unique Constraints**: Prevent duplicate data at grain level
- **Check Constraints**: Validate categorical values (org_type, grad_rate_type)
- **NOT NULL Constraints**: Enforce required fields
- **Foreign Keys**: Ensure referential integrity to schools dimension

### 4. Metadata Tracking
- **created_at**: Timestamp for ETL audit trail
- **updated_at**: Timestamp for schools dimension updates (via trigger)

## Query Patterns

### Pattern 1: Single School Time Series
```sql
SELECT school_year, total_enrollment
FROM enrollment
WHERE school_id = '00350123'
ORDER BY school_year;
```
**Indexes Used**: `idx_enrollment_school_year`

### Pattern 2: School Comparison
```sql
SELECT s.school_name, e.high_needs_pct
FROM enrollment e
JOIN schools s ON e.school_id = s.school_id
WHERE e.school_year = 2025
  AND s.org_type = 'School'
  AND s.district_code = '00350000'
ORDER BY e.high_needs_pct DESC;
```
**Indexes Used**: `idx_enrollment_year`, `idx_schools_district`, `idx_enrollment_high_needs`

### Pattern 3: Multi-Metric Dashboard
```sql
SELECT
  s.school_name,
  e.total_enrollment,
  e.high_needs_pct,
  a.attendance_rate,
  m.meeting_exceeding_pct
FROM schools s
LEFT JOIN enrollment e ON s.school_id = e.school_id AND e.school_year = 2025
LEFT JOIN attendance a ON s.school_id = a.school_id AND a.school_year = 2025
LEFT JOIN mcas_results m ON s.school_id = m.school_id AND m.school_year = 2025
WHERE s.org_type = 'School' AND s.district_code = '00350000';
```
**Indexes Used**: Multiple composite indexes on (school_id, school_year)

### Pattern 4: Trend Analysis with Filtering
```sql
SELECT
  school_year,
  AVG(high_needs_pct) as avg_high_needs
FROM enrollment
WHERE school_id IN ('school1', 'school2', 'school3')
GROUP BY school_year
ORDER BY school_year;
```
**Indexes Used**: `idx_enrollment_school_year`

## Data Volume Estimates

Assuming:
- 109 schools (as documented)
- 5 years of data (2020-2025)
- Average 10 student groups per metric

| Table | Estimated Rows | Notes |
|-------|----------------|-------|
| schools | ~110 | 109 schools + Boston district |
| enrollment | ~550 | 110 orgs × 5 years |
| mcas_results | ~55,000 | 109 schools × 5 years × 3 subjects × 3 grades × 10 groups |
| graduation_rates | ~15,000 | ~50 high schools × 5 years × 3 types × 10 groups |
| class_size | ~50,000 | 109 schools × 5 years × ~100 subjects |
| attendance | ~5,500 | 109 schools × 5 years × 10 groups |
| attrition | ~5,500 | 109 schools × 5 years × 10 groups |
| mobility | ~5,500 | 109 schools × 5 years × 10 groups |
| discipline | ~50,000 | 109 schools × 5 years × 10 groups × ~10 offense types |
| expenditures | ~500 | 1 district × 5 years × ~100 categories |
| accountability | ~550 | 109 schools × 5 years |
| **TOTAL** | **~193,000** | Manageable for PostgreSQL |

## Storage Considerations

- **Total Estimated Size**: < 100 MB (with indexes)
- **Supabase Free Tier**: 500 MB database (sufficient)
- **Query Performance**: Excellent for this data volume
- **No Partitioning Needed**: Data volume too small to benefit

## Future Enhancements

### Potential Additions:
1. **student_groups dimension table**: Normalize demographic/population categories
2. **calendar dimension table**: Support fiscal year vs school year queries
3. **Materialized views**: Pre-aggregate common dashboard queries
4. **Partitioning**: If data expands to 50+ years
5. **Geographic data**: Add latitude/longitude for map visualizations

### Not Recommended:
- **Over-normalization**: Would complicate queries without significant benefit
- **Snowflake schema**: Additional dimension tables add join complexity
- **Separate history tables**: Data volume doesn't justify it
