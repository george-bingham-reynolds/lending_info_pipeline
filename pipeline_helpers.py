BQ_DS = "lending_doc_info"

gcs_bq_map = {"loan-pipeline-demo-financial-statements-bucket":"financial_statements", "loan-pipeline-demo-appraisals-bucket":"appraisals"}

# Each entry is (field_name, bq_dtype). Identifiers (loan_number, document_date)
# are no longer special-cased — they're just STRING fields alongside the
# FLOAT content fields, extracted and confidence-scored the same way.
req_fields_map = {
    "loan-pipeline-demo-financial-statements-bucket": [
        ("loan_number", "STRING"),
        ("statement_period", "STRING"),
        ("total_revenue", "FLOAT"),
        ("total_operating_expenses", "FLOAT"),
        ("net_operating_income", "FLOAT"),
        ("annual_debt_service", "FLOAT"),
        ("occupancy_rate", "FLOAT"),
    ],
    "loan-pipeline-demo-appraisals-bucket": [
        ("loan_number", "STRING"),
        ("valuation_date", "STRING"),
        ("appraised_value", "FLOAT"),
        ("capitalization_rate", "FLOAT"),
        ("appraiser_noi_estimate", "FLOAT"),
        ("gross_building_area_sf", "FLOAT"),
        ("value_per_sf", "FLOAT"),
    ],
}