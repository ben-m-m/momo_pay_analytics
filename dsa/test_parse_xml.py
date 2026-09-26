"""
dsa/test_parse_xml.py — Unit tests for the SMS parser.

Run:
    cd dsa
    python -m unittest test_parse_xml -v
"""

import unittest
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from parse_xml import (
    is_otp,
    _to_float,
    _epoch_millisec_to_iso,
    _status_for,
    _extract_from_body,
    parse_sms_xml,
)


EPOCH_MS = "1715351458724"   # 2024-05-10 16:30:58 Kigali time


class TestIsOtp(unittest.TestCase):

    def test_otp_uppercase(self):
        self.assertTrue(is_otp("Your OTP is 123456"))

    def test_otp_lowercase(self):
        self.assertTrue(is_otp("your otp: 123456"))

    def test_verification_code(self):
        self.assertTrue(is_otp("Your verification code is 987654"))

    def test_your_code_is(self):
        self.assertTrue(is_otp("Your code is 987654. Do not share."))

    def test_normal_transaction_is_not_otp(self):
        self.assertFalse(is_otp("You have received 2000 RWF from Jane Smith"))

    def test_empty_body(self):
        self.assertFalse(is_otp(""))
        self.assertFalse(is_otp(None))


class TestToFloat(unittest.TestCase):

    def test_plain_number(self):
        self.assertEqual(_to_float("2000"), 2000.0)

    def test_comma_amount(self):
        self.assertEqual(_to_float("2,000"), 2000.0)

    def test_comma_with_decimal(self):
        self.assertEqual(_to_float("1,000.50"), 1000.5)

    def test_whitespace(self):
        self.assertEqual(_to_float("  500  "), 500.0)

    def test_none(self):
        self.assertIsNone(_to_float(None))

    def test_empty(self):
        self.assertIsNone(_to_float(""))

    def test_garbage(self):
        self.assertIsNone(_to_float("abc"))


class TestEpochMillisecToIso(unittest.TestCase):

    def test_real_value_kigali_time(self):
        # 1715351458724 ms = 2024-05-10 16:30:58 Kigali time (UTC+2)
        self.assertEqual(_epoch_millisec_to_iso(EPOCH_MS), "2024-05-10 16:30:58")

    def test_epoch_zero(self):
        self.assertEqual(_epoch_millisec_to_iso("0"), "1970-01-01 02:00:00")

    def test_none(self):
        self.assertIsNone(_epoch_millisec_to_iso(None))

    def test_garbage(self):
        self.assertIsNone(_epoch_millisec_to_iso("not-a-number"))


class TestStatusFor(unittest.TestCase):

    def test_normal_is_ok(self):
        self.assertEqual(_status_for("payment"), "ok")
        self.assertEqual(_status_for("received"), "ok")
        self.assertEqual(_status_for("transfer"), "ok")

    def test_failed(self):
        self.assertEqual(_status_for("failed_transaction"), "failed")

    def test_pending_reversal(self):
        self.assertEqual(_status_for("reversal_initiated"), "pending_reversal")

    def test_reversed(self):
        self.assertEqual(_status_for("reversal_confirmed"), "reversed")

    def test_statement(self):
        self.assertEqual(_status_for("statement_line"), "statement")

    def test_unknown_type_defaults_to_ok(self):
        self.assertEqual(_status_for("nonexistent_type"), "ok")


class TestExtractFromBody(unittest.TestCase):
    """One test per template, using real bodies from the XML file."""

    def test_received(self):
        body = ("You have received 2000 RWF from Jane Smith (*********013) "
                "at 2024-05-10 16:30:51.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("received", 2000.0, "Jane Smith", "self", "2024-05-10 16:30:51"),
        )

    def test_payment(self):
        body = ("TxId: 1. Your payment of 1,000 RWF to Jane Smith 12845 "
                "has been completed at 2024-05-10 16:31:39.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("payment", 1000.0, "self", "Jane Smith", "2024-05-10 16:31:39"),
        )

    def test_airtime(self):
        body = ("*162*TxId:1*S*Your payment of 2000 RWF to Airtime with token "
                "has been completed at 2024-05-12 11:41:28.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("airtime", 2000.0, "self", "Airtime", "2024-05-12 11:41:28"),
        )

    def test_bundle_purchase_uses_epoch_fallback(self):
        # Body has no human timestamp — fallback fires
        body = "Yello!Umaze kugura 2000Rwf(1GB)/30days igura 2,000 RWF"
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("bundle_purchase", 2000.0, "self", "MTN", "2024-05-10 16:30:58"),
        )

    def test_bank_transfer(self):
        body = ("You have transferred 50000 RWF to Linda Green (250795963036) "
                "from your mobile money account 20077201001 imbank.bank "
                "at 2024-10-23 09:59:01.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("bank_transfer", 50000.0, "self", "Linda Green", "2024-10-23 09:59:01"),
        )

    def test_direct_payment_receiver_is_self(self):
        body = ("*164*S*Y'ello,A transaction of 25000 RWF by DIRECT PAYMENT LTD  "
                "on your MOMO account was successfully completed at 2024-05-14 21:01:00.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("direct_payment", 25000.0, "DIRECT PAYMENT LTD", "self", "2024-05-14 21:01:00"),
        )

    def test_agent_withdrawal(self):
        body = ("You Abebe Chala CHEBUDIE (*********036) have via agent: "
                "Agent Sophia (250790777777), withdrawn 20000 RWF from your "
                "mobile money account: 36521838 at 2024-05-26 02:10:27 and you can")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("agent_withdrawal", 20000.0, "self", "Agent Sophia", "2024-05-26 02:10:27"),
        )

    def test_transfer_165(self):
        body = ("*165*S*10000 RWF transferred to Samuel Carter (250791666666) "
                "from 36521838 at 2024-05-11 20:34:47 .")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("transfer", 10000.0, "self", "Samuel Carter", "2024-05-11 20:34:47"),
        )

    def test_deposit(self):
        body = ("*113*R*A bank deposit of 40000 RWF has been added at "
                "2024-05-11 18:43:49. Your NEW BALANCE :40400 RWF.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("deposit", 40000.0, "bank", "self", "2024-05-11 18:43:49"),
        )

    def test_failed_transaction_variant_a(self):
        body = ("*143*TxId:16803066185*S*Your payment of 5000 RWF to Bundlesand "
                "Packs with token  has failed at 2024-11-12 23:47:47.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("failed_transaction", 5000.0, "self", "Bundlesand Packs", "2024-11-12 23:47:47"),
        )

    def test_failed_transaction_variant_b(self):
        body = ("*143*R*Y'ello, the transaction with amount 14200 RWF for ESICIA "
                "LTD with message: 1734874172692585358074144 failed at 2024-09-21 15:49:01 .")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("failed_transaction", 14200.0, "self", "ESICIA LTD", "2024-09-21 15:49:01"),
        )

    def test_reversal_confirmed(self):
        body = ("*143*S*Your transaction to Mediatrice UWAYISENGA (250788658286) "
                "with 3000 RWF has been reversed at 2024-10-07 14:37:00.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("reversal_confirmed", 3000.0, "self", "Mediatrice UWAYISENGA", "2024-10-07 14:37:00"),
        )

    def test_reversal_initiated_uses_epoch(self):
        body = ("A reversal has been initiated for your transaction to "
                "Mediatrice UWAYISENGA (250788658286) with 3000 RWF.")
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("reversal_initiated", 3000.0, "self", "Mediatrice UWAYISENGA", "2024-05-10 16:30:58"),
        )

    def test_statement_line(self):
        body = "1) 2024-08-23 DEPOSIT RWF 25000 Receiver: 250795963036 Sender:  Fee: RWF"
        self.assertEqual(
            _extract_from_body(body, EPOCH_MS),
            ("statement_line", 25000.0, "bank", "self", "2024-08-23 00:00:00"),
        )

    def test_unmatched_returns_none(self):
        self.assertIsNone(_extract_from_body("Random text", EPOCH_MS))

    def test_empty_body_returns_none(self):
        self.assertIsNone(_extract_from_body("", EPOCH_MS))


class TestParseSmsXmlEndToEnd(unittest.TestCase):
    """Tests against the real XML file — full-file integrity checks."""

    @classmethod
    def setUpClass(cls):
        cls.txs, cls.otp, cls.unknown = parse_sms_xml()

    def test_total_records(self):
        self.assertEqual(len(self.txs), 1683)

    def test_otp_skipped(self):
        self.assertEqual(self.otp, 8)

    def test_no_unrecognized(self):
        self.assertEqual(self.unknown, 0)

    def test_full_accounting(self):
        # 1683 parsed + 8 skipped OTP + 0 unknown = 1691 total
        self.assertEqual(len(self.txs) + self.otp + self.unknown, 1691)

    def test_ids_are_contiguous_from_1(self):
        ids = [t["id"] for t in self.txs]
        self.assertEqual(ids, list(range(1, len(self.txs) + 1)))

    def test_all_records_have_required_keys(self):
        required = {"id", "transaction_type", "amount", "sender",
                    "receiver", "timestamp", "status", "txid", "body"}
        for tx in self.txs:
            self.assertTrue(required.issubset(tx.keys()),
                            f"missing keys in {tx}")

    def test_no_none_amounts(self):
        for tx in self.txs:
            self.assertIsNotNone(tx["amount"],
                                 f"amount is None in {tx['transaction_type']}")

    def test_no_none_timestamps(self):
        for tx in self.txs:
            self.assertIsNotNone(tx["timestamp"],
                                 f"timestamp is None in {tx['transaction_type']}")

    def test_status_values_are_valid(self):
        valid = {"ok", "failed", "pending_reversal", "reversed", "statement"}
        for tx in self.txs:
            self.assertIn(tx["status"], valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)