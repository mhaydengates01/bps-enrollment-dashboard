"""
Seed script for the 'mcas_results' fact table.

This script:
- Reads MCAS achievement results from CSV
- Validates and transforms data (handles counts, percentages, nulls)
- Inserts data into the Supabase 'mcas_results' table
- Provides detailed error handling and logging

Usage:
    python scripts/seed_mcas.py [--dry-run]

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
        logging.FileHandler('scripts/seed_mcas.log')
    ]
)
logger = logging.getLogger(__name__)

# CSV file path
DATA_DIR = Path('data/data/raw')
CSV_FILE = DATA_DIR / 'mcas_achievement_results' / 'MCAS_Achievement_Results_20251204.csv'


# ============================================================================
# DATA TRANSFORMATION HELPERS
# ============================================================================

def parse_int(value) -> Optional[int]:
    """Parse integer from string, handling commas and empty values."""
    if pd.isna(value) or value == '' or value == 'N':
        return None
    try:
        return int(str(value).replace(',', ''))
    except (ValueError, AttributeError):
        return None


def parse_decimal(value) -> Optional[float]:
    """Parse decimal from string, handling percentages and empty values."""
    if pd.isna(value) or value == '' or value == 'N':
        return None
    try:
        value_str = str(value).replace('%', '').replace(',', '')
        return float(value_str)
    except (ValueError, AttributeError):
        return None


# ============================================================================
# DATA VALIDATION
# ============================================================================

class McasRecord:
    """Represents a validated MCAS result record."""

    def __init__(self, **kwargs):
        self.school_year = kwargs.get('school_year')
        self.school_id = kwargs.get('school_id')
        self.test_grade = kwargs.get('test_grade')
        self.subject_code = kwargs.get('subject_code')
        self.student_group = kwargs.get('student_group')

        # Performance levels
        self.meeting_exceeding_count = kwargs.get('meeting_exceeding_count')
        self.meeting_exceeding_pct = kwargs.get('meeting_exceeding_pct')
        self.exceeding_count = kwargs.get('exceeding_count')
        self.exceeding_pct = kwargs.get('exceeding_pct')
        self.meeting_count = kwargs.get('meeting_count')
        self.meeting_pct = kwargs.get('meeting_pct')
        self.partially_meeting_count = kwargs.get('partially_meeting_count')
        self.partially_meeting_pct = kwargs.get('partially_meeting_pct')
        self.not_meeting_count = kwargs.get('not_meeting_count')
        self.not_meeting_pct = kwargs.get('not_meeting_pct')

        # Test participation and scores
        self.student_count = kwargs.get('student_count')
        self.student_participation_pct = kwargs.get('student_participation_pct')
        self.avg_scaled_score = kwargs.get('avg_scaled_score')
        self.avg_student_growth_percentile = kwargs.get('avg_student_growth_percentile')
        self.avg_sgp_included = kwargs.get('avg_sgp_included')
        self.achievement_percentile = kwargs.get('achievement_percentile')

    def to_dict(self) -> Dict:
        """Convert to dictionary for Supabase insert."""
        return {
            'school_year': self.school_year,
            'school_id': self.school_id,
            'test_grade': self.test_grade,
            'subject_code': self.subject_code,
            'student_group': self.student_group,
            'meeting_exceeding_count': self.meeting_exceeding_count,
            'meeting_exceeding_pct': self.meeting_exceeding_pct,
            'exceeding_count': self.exceeding_count,
            'exceeding_pct': self.exceeding_pct,
            'meeting_count': self.meeting_count,
            'meeting_pct': self.meeting_pct,
            'partially_meeting_count': self.partially_meeting_count,
            'partially_meeting_pct': self.partially_meeting_pct,
            'not_meeting_count': self.not_meeting_count,
            'not_meeting_pct': self.not_meeting_pct,
            'student_count': self.student_count,
            'student_participation_pct': self.student_participation_pct,
            'avg_scaled_score': self.avg_scaled_score,
            'avg_student_growth_percentile': self.avg_student_growth_percentile,
            'avg_sgp_included': self.avg_sgp_included,
            'achievement_percentile': self.achievement_percentile,
        }

    def __repr__(self):
        return (f"McasRecord(year={self.school_year}, school_id={self.school_id}, "
                f"grade={self.test_grade}, subject={self.subject_code}, group={self.student_group})")


def validate_mcas_record(row: pd.Series) -> Optional[McasRecord]:
    """
    Validate and transform a single MCAS record from CSV.

    Args:
        row: Pandas Series representing a CSV row

    Returns:
        McasRecord if valid, None if invalid
    """
    errors = []

    # Extract and validate required fields
    school_year_raw = row.get('SY')
    school_id = str(row.get('ORG_CODE', '')).strip()
    test_grade = str(row.get('TEST_GRADE', '')).strip()
    subject_code = str(row.get('SUBJECT_CODE', '')).strip()
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

    # Validate school_id (required, non-empty)
    if not school_id or school_id == 'nan':
        errors.append("Missing ORG_CODE (school_id)")

    # Validate test_grade (required, non-empty)
    if not test_grade or test_grade == 'nan':
        errors.append("Missing TEST_GRADE")

    # Validate subject_code (required, non-empty)
    if not subject_code or subject_code == 'nan':
        errors.append("Missing SUBJECT_CODE")

    # Validate student_group (required, non-empty)
    if not student_group or student_group == 'nan':
        errors.append("Missing STU_GRP (student_group)")

    # If critical validation errors, log and return None
    if errors:
        logger.warning(
            f"Invalid record: {', '.join(errors)} | "
            f"SY={row.get('SY')}, ORG_CODE={row.get('ORG_CODE')}, "
            f"TEST_GRADE={row.get('TEST_GRADE')}, SUBJECT_CODE={row.get('SUBJECT_CODE')}"
        )
        return None

    # Parse all metric fields (nulls are OK)
    try:
        record = McasRecord(
            school_year=school_year,
            school_id=school_id,
            test_grade=test_grade,
            subject_code=subject_code,
            student_group=student_group,

            # Performance levels
            meeting_exceeding_count=parse_int(row.get('M_PLUS_E_CNT')),
            meeting_exceeding_pct=parse_decimal(row.get('M_PLUS_E_PCT')),
            exceeding_count=parse_int(row.get('E_CNT')),
            exceeding_pct=parse_decimal(row.get('E_PCT')),
            meeting_count=parse_int(row.get('M_CNT')),
            meeting_pct=parse_decimal(row.get('M_PCT')),
            partially_meeting_count=parse_int(row.get('PM_CNT')),
            partially_meeting_pct=parse_decimal(row.get('PM_PCT')),
            not_meeting_count=parse_int(row.get('NM_CNT')),
            not_meeting_pct=parse_decimal(row.get('NM_PCT')),

            # Test participation and scores
            student_count=parse_int(row.get('STU_CNT')),
            student_participation_pct=parse_decimal(row.get('STU_PART_PCT')),
            avg_scaled_score=parse_decimal(row.get('AVG_SCALED_SCORE')),
            avg_student_growth_percentile=parse_decimal(row.get('AVG_SGP')),
            avg_sgp_included=parse_decimal(row.get('AVG_SGP_INCL')),
            achievement_percentile=parse_int(row.get('ACH_PERCENTILE')),
        )

        return record

    except Exception as e:
        logger.error(f"Error creating MCAS record: {str(e)} | Row: {row.to_dict()}")
        return None


# ============================================================================
# DATA EXTRACTION
# ============================================================================

def extract_mcas_records() -> List[McasRecord]:
    """
    Extract MCAS records from CSV file.

    Returns:
        List of validated McasRecord objects
    """
    logger.info("="*80)
    logger.info(f"Reading MCAS data from: {CSV_FILE.name}")
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
            record = validate_mcas_record(row)
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
    """Create and return Supabase client."""
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


def insert_mcas_records(supabase: Client, records: List[McasRecord],
                        batch_size: int = 100, dry_run: bool = False) -> bool:
    """
    Insert MCAS records into Supabase database.

    Args:
        supabase: Supabase client
        records: List of McasRecord objects
        batch_size: Number of records to insert per batch
        dry_run: If True, don't actually insert data

    Returns:
        True if successful, False otherwise
    """
    logger.info("="*80)
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Inserting {len(records)} MCAS records")
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
            response = supabase.table('mcas_results').upsert(
                batch,
                on_conflict='school_id,school_year,test_grade,subject_code,student_group'
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
                    supabase.table('mcas_results').upsert(record).execute()
                    total_inserted += 1
                except Exception as individual_error:
                    total_errors += 1
                    logger.error(
                        f"Failed to insert MCAS result for school {record['school_id']} "
                        f"year {record['school_year']} grade {record['test_grade']} "
                        f"subject {record['subject_code']} group {record['student_group']}: "
                        f"{str(individual_error)}"
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

    logger.info("BPS Enrollment Dashboard - MCAS Results Table Seeding Script")
    logger.info(f"Dry Run Mode: {dry_run}")
    logger.info("")

    # Step 1: Extract MCAS records from CSV
    records = extract_mcas_records()

    if not records:
        logger.error("No MCAS records extracted. Exiting.")
        return 1

    # Step 2: Get Supabase client
    supabase = get_supabase_client()

    if not supabase:
        logger.error("Failed to connect to Supabase. Exiting.")
        return 1

    # Step 3: Insert MCAS records
    success = insert_mcas_records(supabase, records, dry_run=dry_run)

    if success:
        logger.info("[SUCCESS] MCAS seeding completed successfully!")
        return 0
    else:
        logger.error("[FAILED] MCAS seeding completed with errors. Check logs for details.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
