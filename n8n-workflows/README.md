# n8n Workflows for BPS Enrollment Dashboard

This directory contains n8n workflow JSON files for ETL processes that ingest data from the Massachusetts DESE Socrata API into Supabase.

## Available Workflows

### 1. MCAS API to Supabase (`mcas_api_to_supabase.json`)

Fetches MCAS Achievement Results from the Socrata API and inserts them into the `mcas_results` table in Supabase.

**What it does:**
- Fetches MCAS data for Boston Public Schools (district code: `00350000`)
- Filters for school years 2021-2025
- Uses pagination to fetch all ~75,748 records (1,000 records per request)
- Transforms API field names to match database schema
- Converts data types (strings to integers, percentages to decimals)
- Handles NULL values in optional fields (e.g., `ach_percentile`)
- Maps `org_code` from API to `school_id` in database
- Uses UPSERT to prevent duplicates on re-runs

**Workflow nodes:**
1. **Start** - Manual trigger
2. **Fetch MCAS Data (Paginated)** - HTTP Request with built-in pagination
3. **Transform API Fields to Database Schema** - Edit Fields node for field mapping
4. **Insert to Supabase** - Supabase node with UPSERT operation

## How to Import

1. Open your n8n instance
2. Click "Import from File" in the workflows menu
3. Select the desired JSON file (e.g., `mcas_api_to_supabase.json`)
4. Configure credentials:
   - **Supabase API**: Add your Supabase URL and service role key
5. Test the workflow with "Execute Workflow"

## Prerequisites

### Supabase Credentials
You'll need to add Supabase credentials in n8n:
- **URL**: Your Supabase project URL (e.g., `https://xxxxx.supabase.co`)
- **Service Role Key**: Your Supabase service role key (not anon key!)

### Database Schema
Ensure your Supabase database has the required table:
```sql
-- See ../supabase/schema.sql for full schema
CREATE TABLE mcas_results (
  id BIGSERIAL PRIMARY KEY,
  school_year INTEGER NOT NULL,
  school_id VARCHAR(20) NOT NULL,
  test_grade VARCHAR(10) NOT NULL,
  subject_code VARCHAR(20) NOT NULL,
  student_group VARCHAR(100) NOT NULL,
  -- ... other fields
  UNIQUE(school_id, school_year, test_grade, subject_code, student_group)
);
```

## Field Mappings

### API → Database Schema

| API Field | Database Column | Transformation |
|-----------|----------------|----------------|
| `sy` | `school_year` | String → Integer |
| `org_code` | `school_id` | Direct mapping (answers "missing school code" concern) |
| `test_grade` | `test_grade` | Direct mapping |
| `subject_code` | `subject_code` | Direct mapping |
| `stu_grp` | `student_group` | Direct mapping |
| `m_plus_e_cnt` | `meeting_exceeding_count` | String → Integer, remove commas |
| `m_plus_e_pct` | `meeting_exceeding_pct` | Decimal × 100 (0.25 → 25.0) |
| `e_cnt` | `exceeding_count` | String → Integer |
| `e_pct` | `exceeding_pct` | Decimal × 100 |
| `m_cnt` | `meeting_count` | String → Integer |
| `m_pct` | `meeting_pct` | Decimal × 100 |
| `pm_cnt` | `partially_meeting_count` | String → Integer |
| `pm_pct` | `partially_meeting_pct` | Decimal × 100 |
| `nm_cnt` | `not_meeting_count` | String → Integer |
| `nm_pct` | `not_meeting_pct` | Decimal × 100 |
| `stu_cnt` | `student_count` | String → Integer |
| `stu_part_pct` | `student_participation_pct` | Decimal × 100 |
| `avg_scaled_score` | `avg_scaled_score` | String → Float |
| `avg_sgp` | `avg_student_growth_percentile` | String → Float |
| `avg_sgp_incl` | `avg_sgp_included` | String → Float |
| `ach_percentile` | `achievement_percentile` | String → Integer, handle NULL/NA |

## NULL Handling

The workflow handles NULL/missing values for all optional fields:
- API fields that are `null`, empty, or `"N"` are converted to `null` in the database
- The `achievement_percentile` field specifically checks for `"N"` values and converts them to `null`
- Database schema allows NULL for all metric fields (only composite keys are required)

## Pagination Details

- **API Limit**: 1,000 records per request (Socrata API limit)
- **Total Records**: ~75,748 for Boston 2021-2025
- **Pagination Method**: Offset-based (`$offset` increments by 1,000)
- **Completion Condition**: Stops when fewer than 1,000 records are returned

## Monitoring

After running the workflow, you can verify the data:
```sql
-- Check total records inserted
SELECT COUNT(*) FROM mcas_results;

-- Check distribution by year
SELECT school_year, COUNT(*)
FROM mcas_results
GROUP BY school_year
ORDER BY school_year;

-- Check for Boston schools only
SELECT DISTINCT school_id, COUNT(*)
FROM mcas_results
GROUP BY school_id;
```

## Troubleshooting

**Issue**: Workflow fails with "credential not found"
- **Solution**: Add Supabase credentials in n8n settings

**Issue**: Duplicate key violations
- **Solution**: Workflow uses UPSERT - duplicates are expected and handled automatically

**Issue**: API rate limiting
- **Solution**: Add delays between batches in the HTTP Request node options

**Issue**: Missing school_id values
- **Solution**: The API's `org_code` field is mapped to `school_id` - this is the school identifier

## Next Steps

After successfully importing MCAS data, you can create additional workflows for:
- Enrollment data
- Attendance data
- Demographics data
- Other DESE datasets

Follow the same pattern:
1. HTTP Request with pagination
2. Edit Fields for transformation
3. Supabase UPSERT for insertion
