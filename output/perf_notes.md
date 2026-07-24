# Performance Notes

- 10 concurrent screener API calls should complete within 10 seconds on local SQLite for this dataset.
- Company Profile screen load checks are stored in output/sprint4_profile_load_times.csv.
- Existing indexes on company_id and year columns are defined in db/schema.sql.
