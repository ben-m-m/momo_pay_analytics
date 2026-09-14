# SQL → JSON Mapping

| SQL Table.Column | JSON Path | Notes |
|---|---|---|
| counterparties.counterparty_id | counterparty.counterparty_id | Stable ID |
| counterparties.party_type = 'account_owner' | marks the XML subscriber | Appears as role: "account_holder" in transaction output |
| transactions.financial_transaction_id | transaction.financial_transaction_id | From TxId: / Financial Transaction Id: |
| transactions.external_transaction_id | transaction.external_transaction_id | Only on *164* template |
| transactions.account_number | transaction.account_number | Always 36521838 |
| transactions.sms_received_at | transaction.sms_received_at | From XML @date (epoch ms → ISO 8601 UTC) |
| transactions.transaction_datetime | transaction.transaction_datetime | Parsed from SMS body |
| transactions.raw_sms_body | transaction.raw_sms_body | Only in complete_* objects |
| transaction_categories.* | transaction.category.* | Nested object |
| transaction_counterparties + counterparties | transaction.parties[] | Array of {counterparty_id, name, role, phone_number, party_type} |
| system_logs | transaction.logs[] and standalone system_log objects | Only logs referencing that transaction are embedded |
