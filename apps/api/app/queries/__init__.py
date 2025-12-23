"""
Query layer for STEP 5 API

SQL templates enforcing operational constitution:
- Compare axis: is_synthetic=false HARD-CODED in WHERE clause
- Amount Bridge axis: is_synthetic filter via option
- All queries are SELECT only (read-only)
"""
