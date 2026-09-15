CREATE DATABASE IF NOT EXISTS MOMO_Analytics;
USE MOMO_Analytics;

CREATE TABLE Transaction_Categories (
    category_id INT NOT NULL AUTO_INCREMENT,
    category_name VARCHAR(255) NOT NULL,
    PRIMARY KEY (category_id),

        CONSTRAINT uq_category_name UNIQUE (category_name),

    CONSTRAINT chk_category_name CHECK (CHAR_LENGTH(TRIM(category_name)) > 0)
) ENGINE = InnoDB;

CREATE TABLE Counterparties (
    counterparty_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    PRIMARY KEY (counterparty_id),
    CONSTRAINT uq_phone_number UNIQUE (phone_number),
    CONSTRAINT chk_counterparty_name CHECK (CHAR_LENGTH(TRIM(name)) > 0)
) ENGINE = InnoDB;

CREATE TABLE Transactions (
    transaction_id INT NOT NULL AUTO_INCREMENT,
    amount DECIMAL(18,2) NOT NULL,
    reference_number VARCHAR(255),
    balance_after DECIMAL(18,2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    fee DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    transaction_datetime DATETIME NOT NULL,
    category_id INT NOT NULL,
    raw_sms_body TEXT NOT NULL,
    PRIMARY KEY (transaction_id),
    CONSTRAINT uq_reference_number UNIQUE (reference_number),
    CONSTRAINT chk_positive_amount CHECK (amount > 0),
    CONSTRAINT chk_non_negative_fee CHECK (fee >= 0),
    CONSTRAINT chk_non_negative_balance CHECK (balance_after >= 0),
    CONSTRAINT chk_valid_status CHECK (status IN ('completed', 'pending', 'failed', 'reversed')),
    CONSTRAINT chk_datetime_not_future CHECK (transaction_datetime <= NOW()),
    CONSTRAINT fk_transactions_category
        FOREIGN KEY (category_id)
        REFERENCES Transaction_Categories(category_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB;

CREATE TABLE System_Logs (
    log_id INT NOT NULL AUTO_INCREMENT,
    transaction_id INT,
    log_type VARCHAR(100) NOT NULL,
    log_message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT NOW(),
    PRIMARY KEY (log_id),
    CONSTRAINT chk_valid_log_type CHECK (log_type IN ('info', 'warning', 'error', 'parse_success', 'parse_failure')),

    CONSTRAINT fk_logs_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES Transactions(transaction_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE = InnoDB;
CREATE TABLE Transaction_Counterparties (
    transaction_id INT NOT NULL,
    counterparty_id INT NOT NULL,
    role VARCHAR(50) NOT NULL,
    PRIMARY KEY (transaction_id, counterparty_id),
    CONSTRAINT chk_valid_role CHECK (role IN ('sender', 'receiver')),

    CONSTRAINT fk_tc_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES Transactions(transaction_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_tc_counterparty
        FOREIGN KEY (counterparty_id)
        REFERENCES Counterparties(counterparty_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE = InnoDB;
CREATE INDEX idx_txn_datetime ON Transactions(transaction_datetime);
CREATE INDEX idx_txn_status   ON Transactions(status);
CREATE INDEX idx_txn_category ON Transactions(category_id);
CREATE INDEX idx_txn_amount   ON Transactions(amount);
CREATE INDEX idx_log_type     ON System_Logs(log_type);
CREATE INDEX idx_log_created  ON System_Logs(created_at);
CREATE INDEX idx_cp_name      ON Counterparties(name);
DELIMITER //
CREATE TRIGGER trg_log_new_transaction
AFTER INSERT ON Transactions
FOR EACH ROW
BEGIN
    INSERT INTO System_Logs (transaction_id, log_type, log_message, created_at)
    VALUES (NEW.transaction_id, 'info',
            CONCAT('Transaction ', NEW.transaction_id, ' inserted. Amount: ', NEW.amount, ' RWF. Ref: ', IFNULL(NEW.reference_number, 'N/A')),
            NOW());
END //
DELIMITER ;
DELIMITER //
CREATE TRIGGER trg_prevent_category_delete
BEFORE DELETE ON Transaction_Categories
FOR EACH ROW
BEGIN
    DECLARE txn_count INT;
    SELECT COUNT(*) INTO txn_count
    FROM Transactions WHERE category_id = OLD.category_id;
    IF txn_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete category: transactions still reference it.';
    END IF;
END //
DELIMITER ;

INSERT INTO Transaction_Categories (category_name) VALUES
    ('Transfer'),
    ('Payment'),
    ('Deposit'),
    ('Withdrawal'),
    ('Airtime Purchase');

INSERT INTO Counterparties (name, phone_number) VALUES
    ('Jean Mugabo',    '+250788000001'),
    ('MTN MoMo Agent', '+250788000002'),
    ('Kigali Water',   '+250788000003'),
    ('Diane Uwase',    '+250788000004');

INSERT INTO Transactions (amount, reference_number, balance_after, status, fee, transaction_datetime, category_id, raw_sms_body) VALUES
    (5000.00,  'TXN20260901001', 45000.00, 'completed', 50.00,  '2026-09-01 10:30:00', 1,
     'You have sent 5,000 RWF to Jean Mugabo (250788000001). Fee: 50 RWF. Balance: 45,000 RWF. Ref: TXN20260901001'),
    (20000.00, 'TXN20260902001', 65000.00, 'completed', 0.00,   '2026-09-02 14:15:00', 3,
     'You have received 20,000 RWF from MTN MoMo Agent (250788000002). Balance: 65,000 RWF. Ref: TXN20260902001'),
    (3500.00,  'TXN20260903001', 61500.00, 'completed', 0.00,   '2026-09-03 09:00:00', 2,
     'Payment of 3,500 RWF to Kigali Water (250788000003) successful. Balance: 61,500 RWF. Ref: TXN20260903001'),
    (10000.00, 'TXN20260904001', 51500.00, 'completed', 100.00, '2026-09-04 16:45:00', 4,
     'Withdrawal of 10,000 RWF at agent. Fee: 100 RWF. Balance: 51,500 RWF. Ref: TXN20260904001'),
    (500.00,   'TXN20260905001', 51000.00, 'completed', 0.00,   '2026-09-05 08:20:00', 5,
     'Airtime purchase of 500 RWF successful. Balance: 51,000 RWF. Ref: TXN20260905001'),
    (15000.00, 'TXN20260906001', 36000.00, 'completed', 75.00,  '2026-09-06 11:00:00', 1,
     'You have sent 15,000 RWF to Diane Uwase (250788000004). Fee: 75 RWF. Balance: 36,000 RWF. Ref: TXN20260906001');

INSERT INTO Transaction_Counterparties (transaction_id, counterparty_id, role) VALUES
    (1, 1, 'receiver'),
    (2, 2, 'sender'),
    (3, 3, 'receiver'),
    (6, 4, 'receiver');

-- SAMPLE QUERIES

-- Q1: Total spending grouped by category
SELECT tc.category_name,
       COUNT(*) AS txn_count,
       SUM(t.amount) AS total_amount
FROM Transactions t
JOIN Transaction_Categories tc ON t.category_id = tc.category_id
GROUP BY tc.category_name
ORDER BY total_amount DESC;

-- Q2: All transactions with their counterparties
SELECT t.transaction_id, t.amount, t.status,
       t.transaction_datetime,
       c.name AS counterparty, tcp.role
FROM Transactions t
LEFT JOIN Transaction_Counterparties tcp ON t.transaction_id = tcp.transaction_id
LEFT JOIN Counterparties c ON tcp.counterparty_id = c.counterparty_id
ORDER BY t.transaction_datetime DESC;

-- Q3: Monthly summary
SELECT DATE_FORMAT(transaction_datetime, '%Y-%m') AS month,
       COUNT(*) AS total_transactions,
       SUM(amount) AS total_volume,
       SUM(fee) AS total_fees
FROM Transactions
GROUP BY month
ORDER BY month;

-- Q4: Failed or pending transactions
SELECT transaction_id, amount, status,
       reference_number, transaction_datetime
FROM Transactions
WHERE status IN ('failed', 'pending')
ORDER BY transaction_datetime DESC;

-- Q5: Recent system errors
SELECT log_id, transaction_id, log_type,
       log_message, created_at
FROM System_Logs
WHERE log_type IN ('error', 'parse_failure')
ORDER BY created_at DESC
LIMIT 20;

-- Q6: Top counterparties by transaction volume
SELECT c.name, c.phone_number,
       COUNT(*) AS txn_count,
       SUM(t.amount) AS total_volume
FROM Counterparties c
JOIN Transaction_Counterparties tcp ON c.counterparty_id = tcp.counterparty_id
JOIN Transactions t ON tcp.transaction_id = t.transaction_id
GROUP BY c.counterparty_id
ORDER BY total_volume DESC;