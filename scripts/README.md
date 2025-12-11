# BPS Data Seeding Scripts

This directory contains Python scripts for seeding the Supabase database with data from CSV files.

## Prerequisites

1. **Python 3.8+** installed
2. **Supabase project** set up with schema deployed
3. **Service role key** from Supabase (found in Project Settings → API)

## Setup

### 1. Install Dependencies

```bash
pip install -r scripts/requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

**Important:** Use the **service role key**, not the anon key! The service role key has admin privileges needed for bulk inserts.

### 3. Deploy Database Schema

Make sure your Supabase database has the schema deployed:

```bash
# Using Supabase CLI (if installed)
supabase db push

# Or manually run the SQL in the Supabase dashboard:
# Copy contents of supabase/schema.sql into SQL Editor and execute
```

## Usage

### Seed Schools Table

The `seed_schools.py` script populates the `schools` dimension table from multiple CSV sources.

**Dry run (preview without inserting):**
```bash
python scripts/seed_schools.py --dry-run
```

**Actual seeding:**
```bash
python scripts/seed_schools.py
```

**What it does:**
- Reads 8 CSV files from `data/data/raw/`
- Extracts unique school records (ORG_CODE, ORG_NAME, etc.)
- Validates all fields (checks for nulls, invalid org_types)
- Deduplicates by `school_id`
- Inserts into Supabase `schools` table using UPSERT
- Logs detailed progress and errors to console + `seed_schools.log`

**Expected output:**
```
2024-12-09 12:00:00 - INFO - Starting school data collection from all CSV sources
2024-12-09 12:00:05 - INFO - Found 450 unique school records in Enrollment CSV
2024-12-09 12:00:10 - INFO - Found 380 unique school records in MCAS CSV
...
2024-12-09 12:00:30 - INFO - Collection complete: 452 unique schools
2024-12-09 12:00:35 - INFO - ✓ Batch 1/5 inserted successfully
...
2024-12-09 12:01:00 - INFO - ✓ Schools seeding completed successfully!
```

## Troubleshooting

### Error: "SUPABASE_URL environment variable not set"
- Make sure you created a `.env` file in the project root
- Check that the file contains `SUPABASE_URL=...`

### Error: "Missing required columns"
- One of the CSV files is missing expected columns
- Check the log to see which file has issues
- Verify CSV files match expected format from DESE

### Error: "Failed to insert batch"
- Check Supabase connection (is service key correct?)
- Verify schema is deployed (`schools` table exists)
- Check log file for specific validation errors

### Error: "Invalid ORG_TYPE"
- Some CSV rows have org_type values not in ('School', 'District', 'State')
- These records will be skipped (check `seed_schools.log` for details)

## Logs

All scripts write logs to:
- **Console:** Real-time progress
- **Log file:** `scripts/seed_schools.log` (detailed errors and warnings)

## Next Steps

After seeding the schools table, you can seed the fact tables:
- `seed_enrollment.py` (coming soon)
- `seed_mcas.py` (coming soon)
- `seed_attendance.py` (coming soon)
- etc.

## Data Flow

```
CSV Files (data/data/raw/)
    ↓
Python Script (validation, transformation)
    ↓
Supabase PostgreSQL (schools table)
    ↓
React Dashboard (queries via Supabase client)
```
