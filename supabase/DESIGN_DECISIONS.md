# Database Schema Design Decisions

## Executive Summary

This document explains the key design decisions for the BPS Enrollment Dashboard database schema, including:
- Star schema architecture choice
- Normalization strategy
- Table structure and naming conventions
- Indexing approach
- Data type selections
- Trade-offs and alternatives considered

---

## 1. Overall Architecture: Star Schema

### Decision
Implement a **star schema** with one dimension table (schools) and multiple fact tables (one per data source).

### Rationale
1. **Query Simplicity**: Dashboard queries typically filter by school and year, then aggregate metrics. Star schema provides direct joins without complex navigation.

2. **Query Performance**: Analytical queries benefit from denormalized fact tables. No expensive joins across multiple normalized tables.

3. **Development Speed**: Easier to understand and query for frontend developers. Matches the natural structure of dashboard visualizations.

4. **Data Volume**: With ~200K total rows, normalization overhead outweighs benefits. Star schema performs excellently at this scale.

### Alternative Considered
**3rd Normal Form (3NF)**
- Would create separate tables for: grades, subjects, demographics, student groups, etc.
- **Rejected**: Too many joins for dashboard queries. Adds complexity without significant storage savings.

---

## 2. Dimension Tables: Minimalist Approach

### Decision
Create only **one dimension table** (schools), not separate dimensions for student groups, years, subjects, etc.

### Rationale
1. **Student Groups Are Not Uniform**: Different tables use different student group breakdowns:
   - Enrollment: Race/ethnicity, gender, selected populations
   - MCAS: Custom demographic groupings
   - Attendance: Varied groupings by period

   Creating a single student_groups dimension would require complex mapping logic.

2. **Low Cardinality**: Student group values are low cardinality (~10-20 unique values). Storing as TEXT in fact tables adds minimal overhead.

3. **Flexible Groupings**: Some analyses may need custom groupings (e.g., "Students of Color" = combining multiple race categories). Easier with TEXT fields.

4. **Subjects & Grades**: Only appear in 2-3 tables each. Not worth dimension table overhead.

### Trade-offs
- **Pro**: Simpler schema, flexible querying, faster development
- **Con**: No central validation of student group values, potential typos in data
- **Mitigation**: Data validation in ETL pipeline (n8n workflows)

### Alternative Considered
**Full Dimensional Model**
- Separate dimensions for: student_groups, school_years, subjects, grades, offense_types, etc.
- **Rejected**: Over-engineering for data volume. Adds complexity without performance benefit.

---

## 3. Fact Table Strategy: One Per Data Source

### Decision
Create **separate fact tables for each CSV data source** (enrollment, mcas_results, attendance, etc.) rather than normalizing into fewer tables.

### Rationale
1. **Different Grains**: Each data source has a unique grain:
   - Enrollment: School + Year
   - MCAS: School + Year + Grade + Subject + Student Group
   - Attendance: School + Year + Period + Student Group

   Combining would require sparse columns or complex pivoting.

2. **Independent Update Cycles**: Different reports may update at different times. Separate tables allow independent ETL workflows.

3. **Query Performance**: Dashboard components typically query one metric type at a time (enrollment chart, MCAS chart, etc.). Separate tables avoid scanning irrelevant data.

4. **Schema Evolution**: If DESE changes report structure, only one table needs modification.

### Trade-offs
- **Pro**: Clear data ownership, optimized queries, independent ETL
- **Con**: More tables to manage (10 fact tables)
- **Acceptable**: PostgreSQL handles this easily

### Alternative Considered
**Entity-Attribute-Value (EAV) Model**
- Single fact table with columns: school_id, year, metric_name, metric_value
- **Rejected**: Terrible for analytical queries. No type safety. Requires pivoting for every query.

---

## 4. Denormalization: Demographics in Enrollment Table

### Decision
Store demographic percentages (race, gender, populations) as **separate columns** in the enrollment table rather than normalizing into separate rows.

### Current Structure (Chosen)
```sql
CREATE TABLE enrollment (
  school_id TEXT,
  school_year INTEGER,
  asian_pct DECIMAL(5,2),
  black_african_american_pct DECIMAL(5,2),
  hispanic_latino_pct DECIMAL(5,2),
  -- etc.
);
```

### Alternative Structure (Rejected)
```sql
CREATE TABLE enrollment_demographics (
  school_id TEXT,
  school_year INTEGER,
  demographic_type TEXT,  -- 'asian', 'black', 'hispanic', etc.
  percentage DECIMAL(5,2)
);
```

### Rationale
1. **Query Simplicity**: Dashboard queries typically select multiple demographics at once:
   ```sql
   -- Current approach (simple)
   SELECT school_name, asian_pct, black_african_american_pct, hispanic_latino_pct
   FROM enrollment;

   -- Normalized approach (requires pivoting)
   SELECT school_name,
     MAX(CASE WHEN demographic_type = 'asian' THEN percentage END) as asian_pct,
     MAX(CASE WHEN demographic_type = 'black' THEN percentage END) as black_pct
   FROM enrollment_demographics
   GROUP BY school_name;
   ```

2. **Chart Rendering**: ApexCharts expects data in wide format (columns = series). Current structure matches this.

3. **Fixed Schema**: DESE report structure is stable. Unlikely to add/remove demographic categories frequently.

4. **Type Safety**: Separate columns allow proper data types and constraints per metric.

### Trade-offs
- **Pro**: Simple queries, matches dashboard needs, better performance
- **Con**: Schema changes needed if DESE adds new demographics
- **Acceptable**: Rare event, easily handled with ALTER TABLE

---

## 5. Naming Conventions

### Decision
Use **snake_case** for all tables and columns, with descriptive full names.

### Examples
- Table: `enrollment` (not `Enrollment` or `tblEnrollment`)
- Column: `black_african_american_pct` (not `BAAPercent` or `baa_pct`)
- Foreign Key: `school_id` (not `SchoolID` or `schoolId`)

### Rationale
1. **PostgreSQL Standard**: snake_case is idiomatic for PostgreSQL
2. **SQL Readability**: No need for quoted identifiers
3. **Consistency**: Matches Supabase conventions and JavaScript/React conventions
4. **Descriptive**: Full names aid understanding (`english_learner_pct` vs `el_pct`)

### Trade-offs
- **Pro**: Clear, consistent, readable SQL
- **Con**: Longer names require more typing
- **Mitigation**: Use SQL aliases, code completion in IDE

---

## 6. Data Types

### Decision Summary

| Data Category | PostgreSQL Type | Rationale |
|---------------|-----------------|-----------|
| Identifiers | TEXT | Variable length, no numeric meaning |
| Year | INTEGER | Simple, efficient for range queries |
| Counts | INTEGER | Sufficient for student counts (max ~5000/school) |
| Percentages | DECIMAL(5,2) | Precision to 2 decimals (e.g., 23.45%) |
| Scores | DECIMAL(6,2) | MCAS scaled scores (e.g., 485.50) |
| Amounts | DECIMAL(15,2) | Financial values up to trillions |
| Timestamps | TIMESTAMPTZ | Time zone aware for ETL tracking |

### Key Decisions Explained

#### School IDs: TEXT vs INTEGER
**Decision**: TEXT
- **Why**: IDs are codes ('00350525'), not numbers. Leading zeros matter.
- **Alternative**: INTEGER with LPAD() for display - rejected as unnecessary complexity

#### Percentages: DECIMAL(5,2) vs FLOAT
**Decision**: DECIMAL(5,2)
- **Why**: Exact representation (23.45% is exactly 23.45, not 23.4500000001)
- **Range**: 0.00% to 999.99% (sufficient, DESE uses 0-100%)
- **Alternative**: FLOAT - rejected due to floating point precision issues in aggregations

#### Year: INTEGER vs DATE
**Decision**: INTEGER
- **Why**: Source data uses year only (2025), not full dates
- **Simplicity**: Direct comparison (year = 2025) vs (EXTRACT(YEAR FROM date) = 2025)
- **Alternative**: DATE with July 1st as school year start - rejected as over-engineering

---

## 7. Indexing Strategy

### Primary Keys
**Decision**: Surrogate keys (BIGSERIAL) for all tables

**Rationale**:
- Stable: Never changes even if business keys (school_id, year) are corrected
- Simple: Single column foreign keys
- Performance: Integer joins faster than composite text joins
- Supabase compatibility: Works well with Supabase auto-generated APIs

### Foreign Keys
**Decision**: Reference schools(school_id) from all fact tables

**Rationale**:
- Referential integrity: Prevents orphaned facts
- Query optimization: Helps query planner with join selectivity
- Documentation: Makes relationships explicit

**Trade-off**: Adds overhead to INSERT operations
- **Acceptable**: ETL is batch process, not real-time

### Composite Indexes
**Decision**: Create (school_id, school_year) indexes on all fact tables

**Rationale**:
- **Primary query pattern**: Filter by school and year together
- **Order matters**: (school_id, year) supports both:
  - WHERE school_id = X AND year = Y
  - WHERE school_id = X (year range)
- **Not reversed**: (year, school_id) less useful for dashboard

### Partial Indexes
**Decision**: Index metric columns with `WHERE column IS NOT NULL`

**Example**:
```sql
CREATE INDEX idx_enrollment_high_needs
ON enrollment(high_needs_pct)
WHERE high_needs_pct IS NOT NULL;
```

**Rationale**:
- **Smaller indexes**: Only index rows with data
- **Faster queries**: When filtering on metrics, NULL rows excluded
- **Dashboard use case**: Charts filtering by high_needs_pct don't need NULL rows

### Indexes NOT Created
**Decision**: No full-text search indexes (yet)

**Rationale**:
- Not in MVP requirements
- Can add later if school name autocomplete is needed
- Consider: `CREATE INDEX idx_schools_name_gin ON schools USING GIN(to_tsvector('english', school_name));`

---

## 8. Constraints

### Unique Constraints
**Decision**: Add UNIQUE constraints matching the grain of each fact table

**Examples**:
```sql
-- Enrollment: one row per school per year
CONSTRAINT unique_enrollment_school_year UNIQUE(school_id, school_year)

-- MCAS: one row per school/year/grade/subject/group
CONSTRAINT unique_mcas_result UNIQUE(school_id, school_year, test_grade, subject_code, student_group)
```

**Rationale**:
- **Data quality**: Prevents duplicate rows from ETL errors
- **Index benefit**: UNIQUE constraints create indexes automatically
- **Documentation**: Explicitly defines grain for developers

### Check Constraints
**Decision**: Use sparingly, only for critical categorical values

**Examples**:
```sql
CONSTRAINT chk_org_type CHECK (org_type IN ('School', 'District', 'State'))
CONSTRAINT chk_grad_rate_type CHECK (graduation_rate_type IN ('4-Year Graduation Rate', '5-Year Graduation Rate', '6-Year Graduation Rate'))
```

**Rationale**:
- **Data quality**: Prevents typos in critical categorical columns
- **Limited use**: Only for stable, small value sets
- **Not for**: Student groups (too many variants), subjects (evolving list)

### NOT NULL Constraints
**Decision**: Require NOT NULL for dimensional attributes, allow NULL for metrics

**Rationale**:
- **Dimensions**: school_id, school_year must exist (define the grain)
- **Metrics**: high_needs_pct, attendance_rate can be NULL (missing data, suppressed for privacy)

---

## 9. Handling Missing Data

### Decision
Store missing/suppressed values as **NULL**, not special strings like 'N/A' or '<5'.

### Rationale
1. **SQL Semantics**: NULL is the correct way to represent "unknown" in SQL
2. **Aggregations**: AVG(), SUM() automatically exclude NULLs
3. **Type Safety**: Prevents mixing strings ('N/A') with numbers in DECIMAL columns

### Transformation Rules (ETL)
```javascript
// In n8n workflows
value === '' ? null : value        // Empty string → NULL
value === 'N/A' ? null : value     // N/A → NULL
value === '<5' ? null : value      // Privacy suppression → NULL
```

### Dashboard Handling
```javascript
// In React components
const displayValue = value ?? 'N/A';  // NULL → 'N/A' for display
```

---

## 10. Accountability Table: Placeholder Approach

### Decision
Create accountability table with **placeholder columns**, finalize after examining Excel files.

### Rationale
1. **Unknown Structure**: Excel files may have complex multi-sheet structures
2. **Incremental Development**: Can load other tables while investigating Excel
3. **Flexibility**: Easy to ALTER TABLE once structure is known

### Next Steps
1. Manually open one Excel file to examine structure
2. Update accountability table schema
3. Design Excel-to-PostgreSQL transformation in n8n

---

## 11. Row Level Security (RLS)

### Decision
**Disabled for MVP**, can enable later if authentication is added.

### Rationale
- **Public dashboard**: No login required in current scope
- **Read-only**: No user-generated data to protect
- **Performance**: RLS adds overhead to every query

### Future Implementation
If authentication is added:
```sql
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read access" ON schools FOR SELECT USING (true);
CREATE POLICY "Admin full access" ON schools USING (auth.role() = 'admin');
```

---

## 12. Audit Columns

### Decision
Add **created_at** to all tables, **updated_at** only to schools dimension.

### Rationale
- **created_at**: Useful for debugging ETL issues ("When was this row loaded?")
- **updated_at**: Only needed for mutable tables. Fact tables are insert-only.
- **No deleted_at**: No soft delete requirement (can add later if needed)

### Implementation
```sql
created_at TIMESTAMPTZ DEFAULT NOW()
```
- Automatically populated on INSERT
- Uses server time (Supabase server time zone)

---

## 13. Views: Data Quality Helper

### Decision
Create **optional views** for data quality monitoring, not for querying business logic.

### Example: school_data_coverage view
Shows which schools have data in each table across years.

**Use case**: ETL verification
- "Did all schools load for 2025?"
- "Which schools are missing MCAS data?"

**Not used for**: Dashboard queries (too slow)

---

## 14. Performance Considerations

### Expected Query Performance
With proper indexes, all dashboard queries should complete in **< 100ms**.

| Query Pattern | Estimated Rows Scanned | Expected Time |
|---------------|------------------------|---------------|
| Single school time series | ~5 rows | < 10ms |
| All schools for one year | ~109 rows | < 20ms |
| Multi-table join | ~109 rows per table | < 50ms |
| Aggregation (district average) | ~109 rows | < 30ms |

### Scaling Considerations
Current design scales to:
- **1000 schools**: Excellent performance
- **50 years of data**: Still excellent
- **Real-time updates**: Would need additional indexes

**Not optimized for**: Millions of rows per table (not expected)

---

## 15. Trade-offs Summary

| Decision | Pros | Cons | Mitigations |
|----------|------|------|-------------|
| Star Schema | Simple queries, fast | Denormalized data | Storage cheap, data volume small |
| One dimension table | Simple, flexible | No validation | ETL validation |
| Separate fact tables | Clear ownership, optimized | More tables | PostgreSQL handles well |
| Wide tables (demographics) | Query simplicity | Schema changes harder | DESE structure stable |
| TEXT for identifiers | Preserves codes | Larger than INTEGER | Negligible at this scale |
| DECIMAL for percentages | Exact precision | Slower than FLOAT | Speed difference negligible |
| Surrogate keys | Stable, simple joins | Extra column | Storage negligible |
| Partial indexes | Smaller, faster | Maintenance complexity | Worth it for key metrics |

---

## 16. Future Enhancements

### Could Add Later (If Needed)
1. **Materialized Views**: Pre-aggregate common dashboard queries
   ```sql
   CREATE MATERIALIZED VIEW district_summary AS
   SELECT school_year, AVG(high_needs_pct) as avg_high_needs
   FROM enrollment
   GROUP BY school_year;
   ```

2. **student_groups Dimension**: If student group validation becomes critical

3. **Full-Text Search**: If school name autocomplete is needed

4. **Geographic Data**: Add lat/lon columns to schools for map visualizations

5. **Partitioning**: If data grows beyond 50 years (unlikely)

### Should NOT Add
1. **Event Sourcing**: Overkill for append-only data
2. **Temporal Tables**: No requirement to track historical corrections
3. **Graph Database**: Relationships are simple (school → facts)

---

## Conclusion

This schema design prioritizes:
1. **Query Simplicity**: Matches dashboard query patterns
2. **Development Speed**: Easy to understand and use
3. **Performance**: Optimized indexes for dashboard filters
4. **Flexibility**: Can evolve as requirements change

The star schema approach is appropriate for:
- Analytical workloads (not transactional)
- Read-heavy dashboards (not real-time writes)
- Fixed schema from external source (DESE reports)
- Small to medium data volumes (< 1M rows)

This design should serve the BPS Enrollment Dashboard well for the 4-week development timeline and beyond.
