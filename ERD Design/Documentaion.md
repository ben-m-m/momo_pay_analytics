# MoMo SMS Data Processing System — Database Design

The editable ERD is available in [Lucidchart](https://lucid.app/lucidchart/34908f11-d5b6-4716-b5be-23a0328c8ced/edit?viewport_loc=-19%2C0%2C2570%2C1094%2C0_0&invitationId=inv_1da15af1-75b6-4b3a-aa60-be9354d449e4). A local image is available at [ERD Image](ERD%20Image.png).

## ERD Design Decisions

Our schema was designed by working backwards from the actual MoMo SMS data rather than forward from assumptions about what a mobile money system should look like. The XML file contains 1,693 messages, and every structural decision we made came from patterns we found in those messages.

### Why Counterparties instead of Users

We named the entity Counterparties instead of Users or Customers because the SMS data does not give us real user accounts. It gives us names and phone numbers extracted from message text, and those names include non-person entities like Airtime, Bundles and Packs, MTN Cash Power, and DIRECT PAYMENT LTD. A single Counterparties table with a name and nullable phone_number field handles all of them without special casing.

### Why credit and debit is not its own field

Credit and debit is not stored as its own column because it is fully determined by the transaction category. A deposit is always a credit. A transfer out, an airtime purchase, a withdrawal, and a bill payment are always debits. Storing it separately would create a redundancy that could fall out of sync.

### Why withdrawal, failed, and reversed are not separate tables

A withdrawal is just another category value in Transaction_Categories. Failed and reversed are outcomes captured by the status field on Transactions. Giving any of these their own table would duplicate every column that Transactions already has.

### Why the many to many relationship exists

A single transaction can involve multiple parties. A withdrawal in our data involves the account holder, the agent, and the system. A transfer involves a sender and a receiver. The Transaction_Counterparties junction table resolves this with a composite primary key and a role field that records each party's function in the transaction.

### Why System_Logs uses a nullable foreign key

System_Logs links to transaction_id with a nullable foreign key so it can record events that never produced a valid transaction, such as OTP messages or malformed records that failed during parsing.