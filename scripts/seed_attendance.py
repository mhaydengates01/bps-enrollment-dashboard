"""
Seed script for the 'attendance' fact table.

This script:
- Reads attendance data from CSV
- Validates and transforms data (handles percentages, decimals, nulls)
- Inserts data into the Supabase 'attendance' table
- Provides detailed error handling and logging

Usage:
    python scripts/seed_attendance.py [--dry-run]

Environment Variables Required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_SERVICE_KEY - Service role key (not anon key!)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scripts/seed_attendance.log')
    ]
)
logger = logging.getLogger(__name__)

# CSV file path
DATA_DIR = Path('data/data/raw')
CSV_FILE = DATA_DIR / 'student_attendance' / 'Student_Attendance_20251204.csv'


# ============================================================================
# DATA TRANSFORMATION HELPERS
# ============================================================================

def parse_decimal(value) -> Optional[float]:
    """
    Parse decimal from string, handling percentages and empty values.

    Examples:
        '93.2%' -> 93.20
        '11.9' -> 11.90
        '' -> None
        'N' -> None

    Args:
        value: Raw value from CSV

    Returns:
        Decimal or None
    """
    if pd.isna(value) or value == '' or value == 'N':
        return None

    try:
        # Remove % sign if present and convert to float
        value_str = str(value).replace('%', '').replace(',', '')
        return float(value_str)
    except (ValueError, AttributeError):
        return None


# ============================================================================
# DATA VALIDATION
# ============================================================================

class AttendanceRecord:
    """Represents a validated attendance record."""

    def __init__(self, **kwargs):
        self.school_year = kwargs.get('school_year')
        self.attendance_period = kwargs.get('attendance_period')
        self.school_id = kwargs.get('school_id')
        self.student_group = kwargs.get('student_group')
        self.attendance_rate = kwargs.get('attendance_rate')
        self.avg_days_absent = kwargs.get('avg_days_absent')
        self.absent_10plus_days_pct = kwargs.get('absent_10plus_days_pct')
        self.chronic_absent_10_pct = kwargs.get('chronic_absent_10_pct')
        self.chronic_absent_20_pct = kwargs.get('chronic_absent_20_pct')
        self.unexcused_absent_10_pct = kwargs.get('unexcused_absent_10_pct')

    def to_dict(self) -> Dict:
        """Convert to dictionary for Supabase insert."""
        return {
            'school_year': self.school_year,
            'attendance_period': self.attendance_period,
            'school_id': self.school_id,
            'student_group': self.student_group,
            'attendance_rate': self.attendance_rate,
            'avg_days_absent': self.avg_days_absent,
            'absent_10plus_days_pct': self.absent_10plus_days_pct,
            'chronic_absent_10_pct': self.chronic_absent_10_pct,
            'chronic_absent_20_pct': self.chronic_absent_20_pct,
            'unexcused_absent_10_pct': self.unexcused_absent_10_pct,
        }

    def __repr__(self):
        return f"AttendanceRecord(year={self.school_year}, school_id={self.school_id}, period={self.attendance_period}, group={self.student_group})"


def validate_attendance_record(row: pd.Series) -> Optional[AttendanceRecord]:
    """
    Validate and transform a single attendance record from CSV.

    Args:
        row: Pandas Series representing a CSV row

    Returns:
        AttendanceRecord if valid, None if invalid
    """
    errors = []

    # Extract and validate required fields
    school_year_raw = row.get('SY')
    attendance_period = str(row.get('ATTEND_PERIOD', '')).strip()
    school_id = str(row.get('ORG_CODE', '')).strip()
    student_group = str(row.get('STU_GRP', '')).strip()

    # Parse school_year as integer
    try:
        school_year = int(school_year_raw) if pd.notna(school_year_raw) else None
    except (ValueError, TypeError):
        school_year = None

    # Validate school_year (required)
    if school_year is None:
        errors.append("Missing SY (school_year)")
    elif school_year < 2000 or school_year > 2100:
        errors.append(f"Invalid school_year {school_year} (must be 2000-2100)")

    # Validate attendance_period (required, non-empty)
    if not attendance_period or attendance_period == 'nan':
        errors.append("Missing ATTEND_PERIOD")

    # Validate school_id (required, non-empty)
    if not school_id or school_id == 'nan':
        errors.append("Missing ORG_CODE (school_id)")

    # Validate student_group (required, non-empty)
    if not student_group or student_group == 'nan':
        errors.append("Missing STU_GRP (student_group)")

    # If critical validation errors, log and return None
    if errors:
        logger.warning(
            f"Invalid record: {', '.join(errors)} | "
            f"SY={row.get('SY')}, ORG_CODE={row.get('ORG_CODE')}, "
            f"ATTEND_PERIOD={row.get('ATTEND_PERIOD')}, STU_GRP={row.get('STU_GRP')}"
        )
        return None

    # Parse all metric fields (nulls are OK)
    try:
        record = AttendanceRecord(
            school_year=school_year,
            attendance_period=attendance_period,
            school_id=school_id,
            student_group=student_group,
            attendance_rate=parse_decimal(row.get('ATTEND_RATE')),
            avg_days_absent=parse_decimal(row.get('CNT_AVG_ABS')),
            absent_10plus_days_pct=parse_decimal(row.get('PCT_ABS_10_DAYS')),
            chronic_absent_10_pct=parse_decimal(row.get('PCT_CHRON_ABS_10')),
            chronic_absent_20_pct=parse_decimal(row.get('PCT_CHRON_ABS_20')),
            unexcused_absent_10_pct=parse_decimal(row.get('PCT_UNEXC_10_DAYS')),
        )

        return record

    except Exception as e:
        logger.error(f"Error creating attendance record: {str(e)} | Row: {row.to_dict()}")
        return None


# ============================================================================
# DATA EXTRACTION
# ============================================================================

def extract_attendance_records() -> List[AttendanceRecord]:
    """
    Extract attendance records from CSV file.

    Returns:
        List of validated AttendanceRecord objects
    """
    logger.info("="*80)
    logger.info(f"Reading attendance data from: {CSV_FILE.name}")
    logger.info("="*80)

    if not CSV_FILE.exists():
        logger.error(f"CSV file not found: {CSV_FILE}")
        return []

    try:
        # Read CSV
        df = pd.read_csv(CSV_FILE, low_memory=False)
        logger.info(f"Loaded {len(df)} rows from CSV")

        # Validate each record
        valid_records = []
        invalid_count = 0

        for idx, row in df.iterrows():
            record = validate_attendance_record(row)
            if record:
                valid_records.append(record)
            else:
                invalid_count += 1

        logger.info("="*80)
        logger.info(f"Validation complete: {len(valid_records)} valid, {invalid_count} invalid")
        logger.info("="*80)

        return valid_records

    except FileNotFoundError:
        logger.error(f"File not found: {CSV_FILE}")
        return []
    except pd.errors.EmptyDataError:
        logger.error(f"Empty CSV file: {CSV_FILE}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV: {str(e)}")
        return []


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def get_supabase_client() -> Optional[Client]:
    """
    Create and return Supabase client.

    Returns:
        Supabase client or None if configuration is invalid
    """
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url:
        logger.error("SUPABASE_URL environment variable not set")
        return None

    if not supabase_key:
        logger.error("SUPABASE_SERVICE_KEY environment variable not set")
        return None

    try:
        client = create_client(supabase_url, supabase_key)
        logger.info("Successfully connected to Supabase")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        return None


def insert_attendance_records(supabase: Client, records: List[AttendanceRecord],
                               batch_size: int = 100, dry_run: bool = False) -> bool:
    """
    Insert attendance records into Supabase database.

    Args:
        supabase: Supabase client
        records: List of AttendanceRecord objects
        batch_size: Number of records to insert per batch
        dry_run: If True, don't actually insert data

    Returns:
        True if successful, False otherwise
    """
    logger.info("="*80)
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Inserting {len(records)} attendance records")
    logger.info("="*80)

    if dry_run:
        logger.info("DRY RUN MODE - No data will be inserted")
        for i, record in enumerate(records[:5], 1):
            logger.info(f"Sample {i}: {record}")
        logger.info("...")
        return True

    # Convert to list of dicts
    record_dicts = [record.to_dict() for record in records]

    # Insert in batches
    total_inserted = 0
    total_errors = 0

    for i in range(0, len(record_dicts), batch_size):
        batch = record_dicts[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(record_dicts) + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")

        try:
            # Use upsert to handle duplicates gracefully
            response = supabase.table('attendance').upsert(
                batch,
                on_conflict='school_id,school_year,attendance_period,student_group'
            ).execute()

            total_inserted += len(batch)
            logger.info(f"[OK] Batch {batch_num} inserted successfully")

        except Exception as e:
            total_errors += len(batch)
            logger.error(f"[ERROR] Error inserting batch {batch_num}: {str(e)}")

            # Try inserting one at a time to identify problem records
            logger.info("Attempting individual inserts for this batch...")
            for record in batch:
                try:
                    supabase.table('attendance').upsert(record).execute()
                    total_inserted += 1
                except Exception as individual_error:
                    total_errors += 1
                    logger.error(
                        f"Failed to insert attendance for school {record['school_id']} "
                        f"year {record['school_year']} period {record['attendance_period']} "
                        f"group {record['student_group']}: {str(individual_error)}"
                    )

    logger.info("="*80)
    logger.info(f"Insert complete: {total_inserted} successful, {total_errors} errors")
    logger.info("="*80)

    return total_errors == 0


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv

    logger.info("BPS Enrollment Dashboard - Attendance Table Seeding Script")
    logger.info(f"Dry Run Mode: {dry_run}")
    logger.info("")

    # Step 1: Extract attendance records from CSV
    records = extract_attendance_records()

    if not records:
        logger.error("No attendance records extracted. Exiting.")
        return 1

    # Step 2: Get Supabase client
    supabase = get_supabase_client()

    if not supabase:
        logger.error("Failed to connect to Supabase. Exiting.")
        return 1

    # Step 3: Insert attendance records
    success = insert_attendance_records(supabase, records, dry_run=dry_run)

    if success:
        logger.info("[SUCCESS] Attendance seeding completed successfully!")
        return 0
    else:
        logger.error("[FAILED] Attendance seeding completed with errors. Check logs for details.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
