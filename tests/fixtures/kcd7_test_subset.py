"""
KCD-7 Test Subset (TEST ONLY - NOT OFFICIAL DISTRIBUTION)

⚠️ WARNING: This is a minimal test fixture for STEP 7 Phase B MVP.
⚠️ DO NOT use this as official KCD-7 distribution.
⚠️ Official KCD-7 codes must come from disease_code_master loaded from external source.

Purpose: Validate FK constraints and evidence requirements in Policy Scope Pipeline.

Scope:
- Samsung 유사암 definition example (C73 갑상선암, C44 피부암)
- C00-C97 range markers for general cancer group
"""

KCD7_TEST_CODES = [
    {
        'code': 'C73',
        'name_kor': '갑상선의 악성신생물',
        'name_eng': 'Malignant neoplasm of thyroid gland',
        'category': 'C73-C75',
        'is_leaf': True
    },
    {
        'code': 'C44',
        'name_kor': '피부의 기타 악성신생물',
        'name_eng': 'Other malignant neoplasms of skin',
        'category': 'C43-C44',
        'is_leaf': True
    },
    {
        'code': 'C00',
        'name_kor': '입술의 악성신생물',
        'name_eng': 'Malignant neoplasm of lip',
        'category': 'C00-C14',
        'is_leaf': True
    },
    {
        'code': 'C97',
        'name_kor': '독립된 (원발성) 여러 부위의 악성신생물',
        'name_eng': 'Malignant neoplasms of independent (primary) multiple sites',
        'category': 'C97',
        'is_leaf': True
    }
]


def load_test_kcd7_codes(conn):
    """
    Load test KCD-7 codes into disease_code_master.

    ⚠️ TEST ONLY: This should ONLY be called from test fixtures.
    ⚠️ Production disease_code_master must be loaded from official KCD-7 distribution.

    Args:
        conn: Database connection (test database only)
    """
    sql = """
    INSERT INTO disease_code_master (code, name_kor, name_eng, category, is_leaf)
    VALUES (%(code)s, %(name_kor)s, %(name_eng)s, %(category)s, %(is_leaf)s)
    ON CONFLICT (code) DO NOTHING
    """

    with conn.cursor() as cursor:
        for code_data in KCD7_TEST_CODES:
            cursor.execute(sql, code_data)

    conn.commit()
