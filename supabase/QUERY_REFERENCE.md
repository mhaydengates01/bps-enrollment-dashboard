# Query Reference Guide

Quick reference for common dashboard queries. Use these patterns when building React components.

---

## Table of Contents
1. [Basic Queries](#basic-queries)
2. [Time Series Queries](#time-series-queries)
3. [School Comparison Queries](#school-comparison-queries)
4. [Filtering Patterns](#filtering-patterns)
5. [Aggregation Queries](#aggregation-queries)
6. [Multi-Table Joins](#multi-table-joins)
7. [Supabase Client Examples](#supabase-client-examples)

---

## Basic Queries

### Get All BPS Schools
```sql
SELECT school_id, school_name
FROM schools
WHERE org_type = 'School'
  AND district_code = '00350000'  -- Boston Public Schools
ORDER BY school_name;
```

### Get Enrollment for One School
```sql
SELECT *
FROM enrollment
WHERE school_id = '00350525'
ORDER BY school_year;
```

### Get Latest Year's Data
```sql
SELECT *
FROM enrollment
WHERE school_year = 2025
  AND school_id IN (
    SELECT school_id FROM schools WHERE org_type = 'School' AND district_code = '00350000'
  );
```

---

## Time Series Queries

### Enrollment Trend (Single School)
```sql
SELECT
  school_year,
  total_enrollment,
  high_needs_pct,
  english_learner_pct
FROM enrollment
WHERE school_id = '00350525'
ORDER BY school_year;
```

### MCAS Proficiency Trend (Single School, ELA, Grade 5)
```sql
SELECT
  school_year,
  meeting_exceeding_pct,
  student_count
FROM mcas_results
WHERE school_id = '00350525'
  AND subject_code = 'ELA'
  AND test_grade = '05'
  AND student_group = 'All Students'
ORDER BY school_year;
```

### Attendance Trend (District-Wide Average)
```sql
SELECT
  school_year,
  AVG(attendance_rate) as avg_attendance,
  AVG(chronic_absent_10_pct) as avg_chronic_absent
FROM attendance
WHERE school_id IN (
    SELECT school_id FROM schools WHERE org_type = 'School' AND district_code = '00350000'
  )
  AND attendance_period = 'End of Year'
  AND student_group = 'All Students'
GROUP BY school_year
ORDER BY school_year;
```

---

## School Comparison Queries

### Compare High Needs Percentage (2025)
```sql
SELECT
  s.school_name,
  e.total_enrollment,
  e.high_needs_pct
FROM enrollment e
JOIN schools s ON e.school_id = s.school_id
WHERE e.school_year = 2025
  AND s.org_type = 'School'
  AND s.district_code = '00350000'
  AND e.high_needs_pct IS NOT NULL
ORDER BY e.high_needs_pct DESC;
```

### Compare MCAS Performance (2025, ELA, All Grades)
```sql
SELECT
  s.school_name,
  AVG(m.meeting_exceeding_pct) as avg_proficiency,
  SUM(m.student_count) as total_tested
FROM mcas_results m
JOIN schools s ON m.school_id = s.school_id
WHERE m.school_year = 2025
  AND m.subject_code = 'ELA'
  AND m.student_group = 'All Students'
  AND s.org_type = 'School'
  AND s.district_code = '00350000'
GROUP BY s.school_id, s.school_name
HAVING SUM(m.student_count) > 0
ORDER BY avg_proficiency DESC;
```

### Top 10 Schools by Enrollment
```sql
SELECT
  s.school_name,
  e.total_enrollment
FROM enrollment e
JOIN schools s ON e.school_id = s.school_id
WHERE e.school_year = 2025
  AND s.org_type = 'School'
  AND s.district_code = '00350000'
ORDER BY e.total_enrollment DESC
LIMIT 10;
```

---

## Filtering Patterns

### Schools Serving High Needs Population (>70%)
```sql
SELECT
  s.school_name,
  e.high_needs_pct,
  e.total_enrollment
FROM enrollment e
JOIN schools s ON e.school_id = s.school_id
WHERE e.school_year = 2025
  AND s.org_type = 'School'
  AND e.high_needs_pct > 70
ORDER BY e.high_needs_pct DESC;
```

### Schools with Chronic Absenteeism Issues (>20%)
```sql
SELECT
  s.school_name,
  a.chronic_absent_10_pct,
  a.attendance_rate
FROM attendance a
JOIN schools s ON a.school_id = s.school_id
WHERE a.school_year = 2025
  AND a.attendance_period = 'End of Year'
  AND a.student_group = 'All Students'
  AND a.chronic_absent_10_pct > 20
  AND s.org_type = 'School'
ORDER BY a.chronic_absent_10_pct DESC;
```

### Elementary Schools Only (Grades PK-5)
```sql
SELECT
  s.school_name,
  e.total_enrollment,
  (e.pk_count + e.k_count + e.grade_1_count + e.grade_2_count +
   e.grade_3_count + e.grade_4_count + e.grade_5_count) as elementary_count
FROM enrollment e
JOIN schools s ON e.school_id = s.school_id
WHERE e.school_year = 2025
  AND s.org_type = 'School'
  AND (e.grade_6_count IS NULL OR e.grade_6_count = 0)  -- No middle school grades
ORDER BY elementary_count DESC;
```

---

## Aggregation Queries

### District Summary Statistics (2025)
```sql
SELECT
  COUNT(*) as school_count,
  SUM(total_enrollment) as total_students,
  AVG(high_needs_pct) as avg_high_needs_pct,
  AVG(english_learner_pct) as avg_el_pct,
  MIN(total_enrollment) as smallest_school,
  MAX(total_enrollment) as largest_school
FROM enrollment
WHERE school_year = 2025
  AND school_id IN (
    SELECT school_id FROM schools WHERE org_type = 'School' AND district_code = '00350000'
  );
```

### Enrollment by Grade Level (District-Wide, 2025)
```sql
SELECT
  SUM(pk_count) as pre_k,
  SUM(k_count) as kindergarten,
  SUM(grade_1_count + grade_2_count + grade_3_count + grade_4_count + grade_5_count) as elementary,
  SUM(grade_6_count + grade_7_count + grade_8_count) as middle,
  SUM(grade_9_count + grade_10_count + grade_11_count + grade_12_count) as high_school
FROM enrollment
WHERE school_year = 2025
  AND school_id IN (
    SELECT school_id FROM schools WHERE org_type = 'School' AND district_code = '00350000'
  );
```

### Demographic Breakdown (District-Wide, 2025)
```sql
-- Note: This calculates counts from percentages (approximate)
SELECT
  SUM(total_enrollment * asian_pct / 100) as asian,
  SUM(total_enrollment * black_african_american_pct / 100) as black,
  SUM(total_enrollment * hispanic_latino_pct / 100) as hispanic,
  SUM(total_enrollment * white_pct / 100) as white,
  SUM(total_enrollment * multi_race_non_hisp_pct / 100) as multi_race
FROM enrollment
WHERE school_year = 2025
  AND school_id IN (
    SELECT school_id FROM schools WHERE org_type = 'School' AND district_code = '00350000'
  );
```

---

## Multi-Table Joins

### School Profile (All Metrics for One School, 2025)
```sql
SELECT
  s.school_name,
  s.district_name,
  e.total_enrollment,
  e.high_needs_pct,
  a.attendance_rate,
  a.chronic_absent_10_pct,
  ROUND(AVG(m.meeting_exceeding_pct), 2) as avg_mcas_proficiency
FROM schools s
LEFT JOIN enrollment e ON s.school_id = e.school_id AND e.school_year = 2025
LEFT JOIN attendance a ON s.school_id = a.school_id
  AND a.school_year = 2025
  AND a.attendance_period = 'End of Year'
  AND a.student_group = 'All Students'
LEFT JOIN mcas_results m ON s.school_id = m.school_id
  AND m.school_year = 2025
  AND m.student_group = 'All Students'
WHERE s.school_id = '00350525'
GROUP BY s.school_id, s.school_name, s.district_name,
         e.total_enrollment, e.high_needs_pct,
         a.attendance_rate, a.chronic_absent_10_pct;
```

### Dashboard Summary (Multiple Metrics for All Schools, 2025)
```sql
SELECT
  s.school_id,
  s.school_name,
  e.total_enrollment,
  e.high_needs_pct,
  e.english_learner_pct,
  a.attendance_rate,
  a.chronic_absent_10_pct,
  ROUND(AVG(m.meeting_exceeding_pct), 2) as avg_mcas_proficiency
FROM schools s
LEFT JOIN enrollment e ON s.school_id = e.school_id AND e.school_year = 2025
LEFT JOIN attendance a ON s.school_id = a.school_id
  AND a.school_year = 2025
  AND a.attendance_period = 'End of Year'
  AND a.student_group = 'All Students'
LEFT JOIN mcas_results m ON s.school_id = m.school_id
  AND m.school_year = 2025
  AND m.student_group = 'All Students'
WHERE s.org_type = 'School' AND s.district_code = '00350000'
GROUP BY s.school_id, s.school_name,
         e.total_enrollment, e.high_needs_pct, e.english_learner_pct,
         a.attendance_rate, a.chronic_absent_10_pct
ORDER BY s.school_name;
```

---

## Supabase Client Examples

### Setup (supabaseClient.js)
```javascript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

### Query: Get All Schools
```javascript
import { supabase } from './supabaseClient';

export async function getBPSSchools() {
  const { data, error } = await supabase
    .from('schools')
    .select('school_id, school_name')
    .eq('org_type', 'School')
    .eq('district_code', '00350000')
    .order('school_name');

  if (error) throw error;
  return data;
}
```

### Query: Get Enrollment Trend
```javascript
export async function getEnrollmentTrend(schoolId) {
  const { data, error } = await supabase
    .from('enrollment')
    .select('school_year, total_enrollment, high_needs_pct')
    .eq('school_id', schoolId)
    .order('school_year');

  if (error) throw error;
  return data;
}
```

### Query: Get School Profile with Multiple Tables
```javascript
export async function getSchoolProfile(schoolId, year = 2025) {
  // Get school info
  const { data: school, error: schoolError } = await supabase
    .from('schools')
    .select('*')
    .eq('school_id', schoolId)
    .single();

  if (schoolError) throw schoolError;

  // Get enrollment
  const { data: enrollment, error: enrollmentError } = await supabase
    .from('enrollment')
    .select('*')
    .eq('school_id', schoolId)
    .eq('school_year', year)
    .single();

  if (enrollmentError) throw enrollmentError;

  // Get attendance
  const { data: attendance, error: attendanceError } = await supabase
    .from('attendance')
    .select('*')
    .eq('school_id', schoolId)
    .eq('school_year', year)
    .eq('attendance_period', 'End of Year')
    .eq('student_group', 'All Students')
    .single();

  if (attendanceError) throw attendanceError;

  // Get MCAS (average across subjects)
  const { data: mcas, error: mcasError } = await supabase
    .from('mcas_results')
    .select('meeting_exceeding_pct')
    .eq('school_id', schoolId)
    .eq('school_year', year)
    .eq('student_group', 'All Students');

  if (mcasError) throw mcasError;

  const avgMcas = mcas.length > 0
    ? mcas.reduce((sum, r) => sum + (r.meeting_exceeding_pct || 0), 0) / mcas.length
    : null;

  return {
    school,
    enrollment,
    attendance,
    avgMcas
  };
}
```

### Query: Filter Schools with Conditions
```javascript
export async function getHighNeedsSchools(year = 2025, threshold = 70) {
  const { data, error } = await supabase
    .from('enrollment')
    .select(`
      school_id,
      high_needs_pct,
      total_enrollment,
      schools (
        school_name
      )
    `)
    .eq('school_year', year)
    .gte('high_needs_pct', threshold)
    .order('high_needs_pct', { ascending: false });

  if (error) throw error;
  return data;
}
```

### Query: Aggregate Data
```javascript
export async function getDistrictSummary(year = 2025) {
  // Supabase doesn't support SUM/AVG directly in the query builder well,
  // so we fetch data and calculate in JavaScript

  const { data, error } = await supabase
    .from('enrollment')
    .select('total_enrollment, high_needs_pct, english_learner_pct')
    .eq('school_year', year)
    .in('school_id', (await supabase
      .from('schools')
      .select('school_id')
      .eq('org_type', 'School')
      .eq('district_code', '00350000')
    ).data.map(s => s.school_id));

  if (error) throw error;

  return {
    schoolCount: data.length,
    totalStudents: data.reduce((sum, s) => sum + (s.total_enrollment || 0), 0),
    avgHighNeedsPct: data.reduce((sum, s) => sum + (s.high_needs_pct || 0), 0) / data.length,
    avgElPct: data.reduce((sum, s) => sum + (s.english_learner_pct || 0), 0) / data.length
  };
}
```

---

## Custom Hooks Pattern

### useSchoolProfile.js
```javascript
import { useState, useEffect } from 'react';
import { getSchoolProfile } from '../services/supabaseClient';

export function useSchoolProfile(schoolId, year) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const profile = await getSchoolProfile(schoolId, year);
        setData(profile);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (schoolId) {
      fetchData();
    }
  }, [schoolId, year]);

  return { data, loading, error };
}
```

### Usage in Component
```javascript
function SchoolDashboard({ schoolId }) {
  const { data, loading, error } = useSchoolProfile(schoolId, 2025);

  if (loading) return <Skeleton />;
  if (error) return <Alert variant="destructive">{error}</Alert>;
  if (!data) return <EmptyState />;

  return (
    <div>
      <h1>{data.school.school_name}</h1>
      <Card>
        <CardTitle>Enrollment: {data.enrollment.total_enrollment}</CardTitle>
        <CardContent>
          High Needs: {data.enrollment.high_needs_pct}%
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## Performance Tips

1. **Always use indexes**: Queries on school_id, school_year are indexed
2. **Limit results**: Use LIMIT for large result sets
3. **Avoid SELECT ***: Select only needed columns
4. **Use single()**: For queries expected to return one row
5. **Batch requests**: Use Promise.all() for parallel queries
6. **Cache responses**: Store frequently accessed data in React Context

---

## Common Patterns Summary

| Pattern | SQL | Supabase.js |
|---------|-----|-------------|
| Filter | `WHERE school_id = X` | `.eq('school_id', X)` |
| Range | `WHERE year >= X AND year <= Y` | `.gte('year', X).lte('year', Y)` |
| Sort | `ORDER BY name` | `.order('name')` |
| Limit | `LIMIT 10` | `.limit(10)` |
| Join | `JOIN schools s ON ...` | `.select('*, schools(*)')` |
| Aggregate | `AVG(value)` | Fetch and calculate in JS |
| Count | `COUNT(*)` | `.select('*', { count: 'exact' })` |

---

## Need Help?

- **Supabase Docs**: https://supabase.com/docs/reference/javascript
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **SQL Tutorial**: https://www.postgresqltutorial.com/
