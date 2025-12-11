"""
Seed script for the 'enrollment' fact table.

This script:
- Reads enrollment data from CSV
- Validates and transforms data (handles commas, percentages, nulls)
- Inserts data into the Supabase 'enrollment' table
- Provides detailed error handling and logging

Usage:
    python scripts/seed_enrollment.py [--dry-run]

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
        logging.FileHandler('scripts/seed_enrollment.log')
    ]
)
logger = logging.getLogger(__name__)

# CSV file path
DATA_DIR = Path('data/data/raw')
CSV_FILE = DATA_DIR / 'enrollment' / 'Enrollment__Grade,_Race_Ethnicity,_Gender,_and_Selected_Populations_20251204.csv'


# ============================================================================
# DATA TRANSFORMATION HELPERS
# ============================================================================

def parse_int(value) -> Optional[int]:
    """
    Parse integer from string, handling commas and empty values.

    Examples:
        '915,932' -> 915932
        '' -> None
        'N' -> None

    Args:
        value: Raw value from CSV

    Returns:
        Integer or None
    """
    if pd.isna(value) or value == '' or value == 'N':
        return None

    try:
        # Remove commas and convert to int
        return int(str(value).replace(',', ''))
    except (ValueError, AttributeError):
        return None


def parse_pct(value) -> Optional[float]:
    """
    Parse percentage from string to decimal.

    Examples:
        '13.9%' -> 13.90
        '0%' -> 0.00
        '' -> None
        'N' -> None

    Args:
        value: Raw percentage value from CSV

    Returns:
        Decimal or None
    """
    if pd.isna(value) or value == '' or value == 'N':
        return None

    try:
        # Remove % sign and convert to float
        return float(str(value).replace('%', ''))
    except (ValueError, AttributeError):
        return None


# ============================================================================
# DATA VALIDATION
# ============================================================================

class EnrollmentRecord:
    """Represents a validated enrollment record."""

    def __init__(self, **kwargs):
        self.school_year = kwargs.get('school_year')
        self.school_id = kwargs.get('school_id')

        # Grade-level counts
        self.total_enrollment = kwargs.get('total_enrollment')
        self.pk_count = kwargs.get('pk_count')
        self.k_count = kwargs.get('k_count')
        self.grade_1_count = kwargs.get('grade_1_count')
        self.grade_2_count = kwargs.get('grade_2_count')
        self.grade_3_count = kwargs.get('grade_3_count')
        self.grade_4_count = kwargs.get('grade_4_count')
        self.grade_5_count = kwargs.get('grade_5_count')
        self.grade_6_count = kwargs.get('grade_6_count')
        self.grade_7_count = kwargs.get('grade_7_count')
        self.grade_8_count = kwargs.get('grade_8_count')
        self.grade_9_count = kwargs.get('grade_9_count')
        self.grade_10_count = kwargs.get('grade_10_count')
        self.grade_11_count = kwargs.get('grade_11_count')
        self.grade_12_count = kwargs.get('grade_12_count')
        self.sp_count = kwargs.get('sp_count')

        # Race/Ethnicity percentages
        self.american_indian_pct = kwargs.get('american_indian_pct')
        self.asian_pct = kwargs.get('asian_pct')
        self.black_african_american_pct = kwargs.get('black_african_american_pct')
        self.hispanic_latino_pct = kwargs.get('hispanic_latino_pct')
        self.multi_race_non_hisp_pct = kwargs.get('multi_race_non_hisp_pct')
        self.native_hawaiian_pacific_pct = kwargs.get('native_hawaiian_pacific_pct')
        self.white_pct = kwargs.get('white_pct')

        # Gender
        self.female_pct = kwargs.get('female_pct')
        self.male_pct = kwargs.get('male_pct')
        self.non_binary_pct = kwargs.get('non_binary_pct')

        # Selected Populations
        self.english_learner_count = kwargs.get('english_learner_count')
        self.english_learner_pct = kwargs.get('english_learner_pct')
        self.former_english_learner_count = kwargs.get('former_english_learner_count')
        self.former_english_learner_pct = kwargs.get('former_english_learner_pct')
        self.high_needs_count = kwargs.get('high_needs_count')
        self.high_needs_pct = kwargs.get('high_needs_pct')
        self.low_income_count = kwargs.get('low_income_count')
        self.low_income_pct = kwargs.get('low_income_pct')
        self.economically_disadvantaged_count = kwargs.get('economically_disadvantaged_count')
        self.economically_disadvantaged_pct = kwargs.get('economically_disadvantaged_pct')
        self.students_with_disabilities_count = kwargs.get('students_with_disabilities_count')
        self.students_with_disabilities_pct = kwargs.get('students_with_disabilities_pct')

    def to_dict(self) -> Dict:
        """Convert to dictionary for Supabase insert."""
        return {
            'school_year': self.school_year,
            'school_id': self.school_id,
            'total_enrollment': self.total_enrollment,
            'pk_count': self.pk_count,
            'k_count': self.k_count,
            'grade_1_count': self.grade_1_count,
            'grade_2_count': self.grade_2_count,
            'grade_3_count': self.grade_3_count,
            'grade_4_count': self.grade_4_count,
            'grade_5_count': self.grade_5_count,
            'grade_6_count': self.grade_6_count,
            'grade_7_count': self.grade_7_count,
            'grade_8_count': self.grade_8_count,
            'grade_9_count': self.grade_9_count,
            'grade_10_count': self.grade_10_count,
            'grade_11_count': self.grade_11_count,
            'grade_12_count': self.grade_12_count,
            'sp_count': self.sp_count,
            'american_indian_pct': self.american_indian_pct,
            'asian_pct': self.asian_pct,
            'black_african_american_pct': self.black_african_american_pct,
            'hispanic_latino_pct': self.hispanic_latino_pct,
            'multi_race_non_hisp_pct': self.multi_race_non_hisp_pct,
            'native_hawaiian_pacific_pct': self.native_hawaiian_pacific_pct,
            'white_pct': self.white_pct,
            'female_pct': self.female_pct,
            'male_pct': self.male_pct,
            'non_binary_pct': self.non_binary_pct,
            'english_learner_count': self.english_learner_count,
            'english_learner_pct': self.english_learner_pct,
            'former_english_learner_count': self.former_english_learner_count,
            'former_english_learner_pct': self.former_english_learner_pct,
            'high_needs_count': self.high_needs_count,
            'high_needs_pct': self.high_needs_pct,
            'low_income_count': self.low_income_count,
            'low_income_pct': self.low_income_pct,
            'economically_disadvantaged_count': self.economically_disadvantaged_count,
            'economically_disadvantaged_pct': self.economically_disadvantaged_pct,
            'students_with_disabilities_count': self.students_with_disabilities_count,
            'students_with_disabilities_pct': self.students_with_disabilities_pct,
        }

    def __repr__(self):
        return f"EnrollmentRecord(year={self.school_year}, school_id={self.school_id}, total={self.total_enrollment})"


def validate_enrollment_record(row: pd.Series) -> Optional[EnrollmentRecord]:
    """
    Validate and transform a single enrollment record from CSV.

    Args:
        row: Pandas Series representing a CSV row

    Returns:
        EnrollmentRecord if valid, None if invalid
    """
    errors = []

    # Extract and validate required fields
    school_year = parse_int(row.get('SY'))
    school_id = str(row.get('ORG_CODE', '')).strip()

    # Validate school_year (required)
    if school_year is None:
        errors.append("Missing SY (school_year)")
    elif school_year < 2000 or school_year > 2100:
        errors.append(f"Invalid school_year {school_year} (must be 2000-2100)")

    # Validate school_id (required, non-empty)
    if not school_id or school_id == 'nan':
        errors.append("Missing ORG_CODE (school_id)")

    # If critical validation errors, log and return None
    if errors:
        logger.warning(
            f"Invalid record: {', '.join(errors)} | "
            f"SY={row.get('SY')}, ORG_CODE={row.get('ORG_CODE')}, ORG_NAME={row.get('ORG_NAME')}"
        )
        return None

    # Parse all other fields (nulls are OK for non-required fields)
    try:
        record = EnrollmentRecord(
            school_year=school_year,
            school_id=school_id,

            # Grade counts
            total_enrollment=parse_int(row.get('TOTAL_CNT')),
            pk_count=parse_int(row.get('PK_CNT')),
            k_count=parse_int(row.get('K_CNT')),
            grade_1_count=parse_int(row.get('G1_CNT')),
            grade_2_count=parse_int(row.get('G2_CNT')),
            grade_3_count=parse_int(row.get('G3_CNT')),
            grade_4_count=parse_int(row.get('G4_CNT')),
            grade_5_count=parse_int(row.get('G5_CNT')),
            grade_6_count=parse_int(row.get('G6_CNT')),
            grade_7_count=parse_int(row.get('G7_CNT')),
            grade_8_count=parse_int(row.get('G8_CNT')),
            grade_9_count=parse_int(row.get('G9_CNT')),
            grade_10_count=parse_int(row.get('G10_CNT')),
            grade_11_count=parse_int(row.get('G11_CNT')),
            grade_12_count=parse_int(row.get('G12_CNT')),
            sp_count=parse_int(row.get('SP_CNT')),

            # Race/Ethnicity percentages
            american_indian_pct=parse_pct(row.get('AIAN_PCT')),
            asian_pct=parse_pct(row.get('AS_PCT')),
            black_african_american_pct=parse_pct(row.get('BAA_PCT')),
            hispanic_latino_pct=parse_pct(row.get('HL_PCT')),
            multi_race_non_hisp_pct=parse_pct(row.get('MNHL_PCT')),
            native_hawaiian_pacific_pct=parse_pct(row.get('NHPI_PCT')),
            white_pct=parse_pct(row.get('WH_PCT')),

            # Gender
            female_pct=parse_pct(row.get('FE_PCT')),
            male_pct=parse_pct(row.get('MA_PCT')),
            non_binary_pct=parse_pct(row.get('NB_PCT')),

            # Selected Populations
            english_learner_count=parse_int(row.get('EL_CNT')),
            english_learner_pct=parse_pct(row.get('EL_PCT')),
            former_english_learner_count=parse_int(row.get('FLNE_CNT')),
            former_english_learner_pct=parse_pct(row.get('FLNE_PCT')),
            high_needs_count=parse_int(row.get('HN_CNT')),
            high_needs_pct=parse_pct(row.get('HN_PCT')),
            low_income_count=parse_int(row.get('LI_CNT')),
            low_income_pct=parse_pct(row.get('LI_PCT')),
            economically_disadvantaged_count=parse_int(row.get('ECD_CNT')),
            economically_disadvantaged_pct=parse_pct(row.get('ECD_PCT')),
            students_with_disabilities_count=parse_int(row.get('SWD_CNT')),
            students_with_disabilities_pct=parse_pct(row.get('SWD_PCT')),
        )

        return record

    except Exception as e:
        logger.error(f"Error creating enrollment record: {str(e)} | Row: {row.to_dict()}")
        return None


# ============================================================================
# DATA EXTRACTION
# ============================================================================

def extract_enrollment_records() -> List[EnrollmentRecord]:
    """
    Extract enrollment records from CSV file.

    Returns:
        List of validated EnrollmentRecord objects
    """
    logger.info("="*80)
    logger.info(f"Reading enrollment data from: {CSV_FILE.name}")
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
            record = validate_enrollment_record(row)
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


def insert_enrollment_records(supabase: Client, records: List[EnrollmentRecord],
                               batch_size: int = 100, dry_run: bool = False) -> bool:
    """
    Insert enrollment records into Supabase database.

    Args:
        supabase: Supabase client
        records: List of EnrollmentRecord objects
        batch_size: Number of records to insert per batch
        dry_run: If True, don't actually insert data

    Returns:
        True if successful, False otherwise
    """
    logger.info("="*80)
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Inserting {len(records)} enrollment records")
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
            response = supabase.table('enrollment').upsert(
                batch,
                on_conflict='school_id,school_year'
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
                    supabase.table('enrollment').upsert(record).execute()
                    total_inserted += 1
                except Exception as individual_error:
                    total_errors += 1
                    logger.error(
                        f"Failed to insert enrollment for school {record['school_id']} "
                        f"year {record['school_year']}: {str(individual_error)}"
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

    logger.info("BPS Enrollment Dashboard - Enrollment Table Seeding Script")
    logger.info(f"Dry Run Mode: {dry_run}")
    logger.info("")

    # Step 1: Extract enrollment records from CSV
    records = extract_enrollment_records()

    if not records:
        logger.error("No enrollment records extracted. Exiting.")
        return 1

    # Step 2: Get Supabase client
    supabase = get_supabase_client()

    if not supabase:
        logger.error("Failed to connect to Supabase. Exiting.")
        return 1

    # Step 3: Insert enrollment records
    success = insert_enrollment_records(supabase, records, dry_run=dry_run)

    if success:
        logger.info("[SUCCESS] Enrollment seeding completed successfully!")
        return 0
    else:
        logger.error("[FAILED] Enrollment seeding completed with errors. Check logs for details.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
