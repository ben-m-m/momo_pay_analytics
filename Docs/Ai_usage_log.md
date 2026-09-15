# AI Usage Log

**Project:** MoMo SMS Data Processing System — Database Design (Week 2)
**Team:** [Web 404]
**Log Maintained By:** [Gahima Nziza]
**Last Updated:** [2026-9-15]

---

## Purpose of This Log

This log documents every interaction between team members and AI-assisted tools
during the design and implementation of the MoMo SMS database. It is maintained
in accordance with the assignment's AI Usage Policy, which permits:

- Grammar and syntax checking in documentation
- Code syntax verification (not logic generation)
- Research on MySQL best practices (with proper citation)

And prohibits:

- Generating ERD designs or SQL schemas
- Creating business logic or database relationships
- Writing reflection content or technical explanations

Each entry below records the date, the responsible team member, the tool used,
the specific purpose, a summary of the prompt, what was taken from the output,
and what was modified or rejected.

---

## Summary of Usage

| Category | Count | Notes |
|---|---|---|
| Grammar / syntax checking | [N] | Documentation only |
| Code syntax verification | [N] | Confirm MySQL 8.0 syntax, not logic |
| Best-practice research (cited) | [N] | With sources in the design doc |
| Logic generation (prohibited) | 0 | Not used |
| ERD generation (prohibited) | 0 | Drawn by team in Lucidchart |
| Explanation writing (prohibited) | 0 | Written by team from source XML |

---

## Detailed Log

### Entry 001 — [2026-9-13]

- **Team Member:** [Tobi]
- **Tool:** [Claude]
- **Category:** syntax checking
- **Purpose:** Verify MySQL 8.0 CHECK constraint syntax for decimal comparisons.
- **Prompt Summary:** "Is `CHECK (amount > 0)` valid on a `DECIMAL(15,2)` column
  in MySQL 8.0? Any caveats?"
- **Output Used:** Confirmed syntax; noted that MySQL 8.0.16+ enforces CHECK
  constraints, earlier versions parse but ignore them.

### Entry 002 — [2026-9-13]

- **Team Member:** [Tobi]
- **Tool:** [Claude]
- **Category:** Best-practice research (with a cite to confirm)
- **Purpose:** Confirm recommended data type for storing monetary amounts.
- **Prompt Summary:** "What is the recommended MySQL data type for financial
  amounts, and why?"
- **Output Used:** Confirmed `DECIMAL(15,2)` over `FLOAT`/`DOUBLE` to avoid
  rounding errors. Team independently decided on precision (15,2) based on
  maximum observed RWF amount in the XML.
- **Citation:** MySQL 8.0 Reference Manual, "Numeric Type Attributes".

### Entry 003 — [2026-9-13]

- **Team Member:** [Benson]
- **Tool:** [ChatGpt]
- **Category:** Grammar / syntax checking
- **Purpose:** Grammar-check the design rationale paragraph for tense
  consistency and article usage.
- **Prompt Summary:** "Please check the grammar of this paragraph: [paste
  paragraph written by the team]."
- **Output Used:** Two minor fixes — "was" → "were" in one clause, and a
  missing comma.

### Entry 004 — [2026-9-14]

- **Team Member:** [Nziza]
- **Tool:** [ChatGpt]
- **Category:** Code syntax verification
- **Purpose:** Confirm syntax for a composite primary key with a foreign key
  constraint in the same table.
- **Prompt Summary:** "Is this valid? `PRIMARY KEY (transaction_id,
  counterparty_id, role)` alongside two separate FOREIGN KEY constraints?"
- **Output Used:** Confirmed valid; suggested explicitly naming the FK
  constraints for easier debugging.
- **Where It Appears:** `database/database_setup.sql`, `transaction_counterparties`.

### Entry 005 — [2026-9-14]

- **Team Member:** [Benson]
- **Tool:** [ChatGpt]
- **Category:** Grammar checking
- **Purpose:** Proofread the README.md for typos.
- **Prompt Summary:** "Proofread this README for typos and awkward phrasing:
  [Readme paste]."
- **Output Used:** Corrected two typos and one sentence fragment.
- **Where It Appears:** `README.md`.

---

## Interaction We Deliberately Did NOT Use AI For

The following tasks were completed entirely by the team, with no AI input
at any stage. This is recorded here to demonstrate policy compliance:

1. **ERD design** — All entities, attributes, keys, and relationships were
   identified by the team by reading the XML file directly. The diagram was
   drawn by hand in Lucidchart.
2. **SQL schema** — Every `CREATE TABLE` statement, column choice, data type,
   and constraint was written by the team. No table structure was generated
   by AI.
3. **Business logic** — The decision to model the account owner as a single
   `counterparties` row (`party_type = 'account_owner'`) was made by the team
   after reviewing the XML and noticing that only one account number
   (`36521838`) appears in the source data.
4. **Category enumeration** — The eight `category_type` values
   (`incoming_transfer`, `outgoing_payment`, `peer_transfer`, `bank_deposit`,
   `withdrawal`, `airtime`, `cash_power`, `merchant_debit`) were derived by the
   team by scanning the SMS templates in the XML.
5. **JSON modeling** — The structure, nesting, and field names for all JSON
   examples were designed by the team.
6. **Technical explanations** — The design rationale, data dictionary, and
   README explanations were written by the team from their own understanding
   of the schema.
7. **Sample data** — All 19 transactions, 11 counterparties, and 8 categories
   were transcribed from the XML by the team.

---

## Attribution in Artifacts

Where any small phrasing or syntax was improved with AI assistance, it is
marked in the artifact:


---

