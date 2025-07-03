# GCS Tools

This directory contains tools that utilize the GCS (Game Content System) database.

## Structure

- `__init__.py` - Package initialization file
- Individual tool files for specific GCS database operations

## Database

The GCS database is loaded from `gcs_data.db.sqlite` located in the path specified by `WORKLOAD_DB_PATH` environment variable.

## Usage

Tools in this directory should import database functions from `db_gcs.py`:

```python
from db_gcs import get_gcs_data, query_gcs_table
```

## Creating New Tools

When creating new GCS tools:
1. Place them in this directory
2. Follow the naming convention: `gcs_[tool_name].py`
3. Import necessary functions from `db_gcs.py`
4. Add appropriate logging using the standard logger
5. Return results in JSON format for consistency