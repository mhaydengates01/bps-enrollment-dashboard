"""
Seed script for the 'schools' dimension table.

This script:
- Reads school data from multiple CSV sources
- Deduplicates and validates school records
- Inserts data into the Supabase 'schools' table
- Provides detailed error handling and logging

Usage:
    python scripts/seed_schools.py [--dry-run]

Environment Variables Required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_SERVICE_KEY - Service role key (not anon key!)
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
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
        logging.FileHandler('scripts/seed_schools.log')
    ]
)
logger = logging.getLogger(__name__)

# Valid org_type values per schema constraint
VALID_ORG_TYPES = {'School', 'District', 'State'}

# CSV files to extract schools from
DATA_DIR = Path('data/data/raw')
CSV_SOURCES = [
    'enrollment/Enrollment__Grade,_Race_Ethnicity,_Gender,_and_Selected_Populations_20251204.csv',
    'mcas_achievement_results/MCAS_Achievement_Results_20251204.csv',
    'student_attendance/Student_Attendance_20251204.csv',
    'class_size/Class_Size_by_Gender,_Race_Ethnicity,_and_Selected_Populations_20251204.csv',
    'student_attrition/Student_Attrition_20251204.csv',
    'student_discipline/Student_Discipline_20251204.csv',
    'student_mobility_rate/Student_Mobility_Rate_20251204.csv',
    'graduation_rates/High_School_Graduation_Rates_20251204.csv',
]


# ============================================================================
# DATA VALIDATION
# ============================================================================

def normalize_org_type(org_type: str) -> str:
    """
    Normalize org_type values from different CSV sources to match schema constraints.

    Schema allows: 'School', 'District', 'State'
    But CSVs may contain: 'Public School', 'Charter School', 'Public School District', etc.

    Args:
        org_type: Raw org_type value from CSV

    Returns:
        Normalized org_type value
    """
    org_type_lower = org_type.lower().strip()

    # State - no normalization needed
    if org_type_lower == 'state':
        return 'State'

    # District variations
    if 'district' in org_type_lower:
        return 'District'

    # School variations (Public School, Charter School, School, etc.)
    if 'school' in org_type_lower:
        return 'School'

    # If no match, return original (will fail validation)
    return org_type


class SchoolRecord:
    """Represents a validated school record."""

    def __init__(self, school_id: str, school_name: str, district_code: str,
                 district_name: str, org_type: str, source_file: str):
        self.school_id = school_id
        self.school_name = school_name
        self.district_code = district_code
        self.district_name = district_name
        self.org_type = org_type
        self.source_file = source_file

    def to_dict(self) -> Dict:
        """Convert to dictionary for Supabase insert."""
        return {
            'school_id': self.school_id,
            'school_name': self.school_name,
            'district_code': self.district_code,
            'district_name': self.district_name,
            'org_type': self.org_type
        }

    def __repr__(self):
        return f"SchoolRecord({self.school_id}, {self.school_name}, {self.org_type})"


def validate_school_record(row: pd.Series, source_file: str) -> Optional[SchoolRecord]:
    """
    Validate a single school record from CSV.

    Args:
        row: Pandas Series representing a CSV row
        source_file: Name of source file for logging

    Returns:
        SchoolRecord if valid, None if invalid
    """
    errors = []

    # Extract and validate required fields
    school_id = str(row.get('ORG_CODE', '')).strip()
    school_name = str(row.get('ORG_NAME', '')).strip()
    district_code = str(row.get('DIST_CODE', '')).strip()
    district_name = str(row.get('DIST_NAME', '')).strip()
    org_type_raw = str(row.get('ORG_TYPE', '')).strip()

    # Normalize org_type to match schema constraints
    org_type = normalize_org_type(org_type_raw) if org_type_raw and org_type_raw != 'nan' else ''

    # Validate school_id (required, non-empty)
    if not school_id or school_id == 'nan':
        errors.append("Missing ORG_CODE (school_id)")

    # Validate school_name (required, non-empty)
    if not school_name or school_name == 'nan':
        errors.append("Missing ORG_NAME (school_name)")

    # Validate district_code (required, non-empty)
    if not district_code or district_code == 'nan':
        errors.append("Missing DIST_CODE (district_code)")

    # Validate district_name (required, non-empty)
    if not district_name or district_name == 'nan':
        errors.append("Missing DIST_NAME (district_name)")

    # Validate org_type (must be in VALID_ORG_TYPES)
    if not org_type or org_type == 'nan':
        errors.append("Missing ORG_TYPE (org_type)")
    elif org_type not in VALID_ORG_TYPES:
        errors.append(f"Invalid ORG_TYPE '{org_type}'. Must be one of: {VALID_ORG_TYPES}")

    # If any validation errors, log and return None
    if errors:
        logger.warning(
            f"Invalid record in {source_file}: {', '.join(errors)} | "
            f"Row data: ORG_CODE={school_id}, ORG_NAME={school_name}"
        )
        return None

    return SchoolRecord(
        school_id=school_id,
        school_name=school_name,
        district_code=district_code,
        district_name=district_name,
        org_type=org_type,
        source_file=source_file
    )


# ============================================================================
# DATA EXTRACTION
# ============================================================================

def extract_schools_from_csv(csv_path: Path) -> List[SchoolRecord]:
    """
    Extract school records from a single CSV file.

    Args:
        csv_path: Path to CSV file

    Returns:
        List of validated SchoolRecord objects
    """
    logger.info(f"Reading CSV: {csv_path.name}")

    try:
        # Read CSV with error handling
        df = pd.read_csv(csv_path, low_memory=False)

        # Check if required columns exist
        required_cols = ['ORG_CODE', 'ORG_NAME', 'DIST_CODE', 'DIST_NAME', 'ORG_TYPE']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            logger.error(f"Missing required columns in {csv_path.name}: {missing_cols}")
            return []

        # Extract unique school combinations
        school_cols = ['ORG_CODE', 'ORG_NAME', 'DIST_CODE', 'DIST_NAME', 'ORG_TYPE']
        unique_schools = df[school_cols].drop_duplicates()

        logger.info(f"Found {len(unique_schools)} unique school records in {csv_path.name}")

        # Validate each record
        valid_records = []
        invalid_count = 0

        for _, row in unique_schools.iterrows():
            record = validate_school_record(row, csv_path.name)
            if record:
                valid_records.append(record)
            else:
                invalid_count += 1

        logger.info(f"Validated {len(valid_records)} records, skipped {invalid_count} invalid records")
        return valid_records

    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        return []
    except pd.errors.EmptyDataError:
        logger.error(f"Empty CSV file: {csv_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading {csv_path.name}: {str(e)}")
        return []


def collect_all_schools() -> Dict[str, SchoolRecord]:
    """
    Collect schools from all CSV sources and deduplicate.

    Returns:
        Dictionary mapping school_id to SchoolRecord
    """
    logger.info("="*80)
    logger.info("Starting school data collection from all CSV sources")
    logger.info("="*80)

    all_schools: Dict[str, SchoolRecord] = {}
    duplicate_count = 0

    for csv_relative_path in CSV_SOURCES:
        csv_path = DATA_DIR / csv_relative_path

        if not csv_path.exists():
            logger.warning(f"Skipping missing file: {csv_relative_path}")
            continue

        # Extract schools from this CSV
        schools = extract_schools_from_csv(csv_path)

        # Add to master dictionary (later entries overwrite earlier ones)
        for school in schools:
            if school.school_id in all_schools:
                duplicate_count += 1
                # Keep the record (could add logic to compare and choose "best" record)
            all_schools[school.school_id] = school

    logger.info("="*80)
    logger.info(f"Collection complete: {len(all_schools)} unique schools")
    logger.info(f"Duplicate records found (deduplicated): {duplicate_count}")
    logger.info("="*80)

    return all_schools


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


def insert_schools(supabase: Client, schools: Dict[str, SchoolRecord],
                   batch_size: int = 100, dry_run: bool = False) -> bool:
    """
    Insert schools into Supabase database.

    Args:
        supabase: Supabase client
        schools: Dictionary of SchoolRecord objects
        batch_size: Number of records to insert per batch
        dry_run: If True, don't actually insert data

    Returns:
        True if successful, False otherwise
    """
    logger.info("="*80)
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Inserting {len(schools)} schools into database")
    logger.info("="*80)

    if dry_run:
        logger.info("DRY RUN MODE - No data will be inserted")
        for i, school in enumerate(list(schools.values())[:5], 1):
            logger.info(f"Sample {i}: {school}")
        logger.info("...")
        return True

    # Convert to list of dicts
    school_dicts = [school.to_dict() for school in schools.values()]

    # Insert in batches
    total_inserted = 0
    total_errors = 0

    for i in range(0, len(school_dicts), batch_size):
        batch = school_dicts[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(school_dicts) + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")

        try:
            # Use upsert to handle duplicates gracefully
            response = supabase.table('schools').upsert(
                batch,
                on_conflict='school_id'
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
                    supabase.table('schools').upsert(record).execute()
                    total_inserted += 1
                except Exception as individual_error:
                    total_errors += 1
                    logger.error(
                        f"Failed to insert school {record['school_id']} "
                        f"({record['school_name']}): {str(individual_error)}"
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

    logger.info("BPS Enrollment Dashboard - Schools Table Seeding Script")
    logger.info(f"Dry Run Mode: {dry_run}")
    logger.info("")

    # Step 1: Collect schools from all CSV sources
    schools = collect_all_schools()

    if not schools:
        logger.error("No schools collected. Exiting.")
        return 1

    # Step 2: Get Supabase client
    supabase = get_supabase_client()

    if not supabase:
        logger.error("Failed to connect to Supabase. Exiting.")
        return 1

    # Step 3: Insert schools
    success = insert_schools(supabase, schools, dry_run=dry_run)

    if success:
        logger.info("[SUCCESS] Schools seeding completed successfully!")
        return 0
    else:
        logger.error("[FAILED] Schools seeding completed with errors. Check logs for details.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
