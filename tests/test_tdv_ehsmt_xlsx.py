"""Structural regression for e-GP bid-guarantee tables.

Fixtures represent layout cases, NOT a copy of the private E-HSMT or a
substitute for full-workbook validation against the authentic Drive source.
"""
from io import BytesIO
import unittest
from openpyxl import Workbook
from tdv_ehsmt_xlsx import inspect_ehsmt_xlsx


def book(rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "HỒ SƠ MỜI THẦU"
    for values in rows:
        ws.append(values)
    output = BytesIO()
    wb.save(output)
    wb.close()
    return output.getvalue()


class EhsmtWorkbookTests(unittest.TestCase):
    def test_mixed_separate_cells_and_flattened_summary(self):
        data = book([
            ["STT", "Mã phần (lô)", "Mã thuốc", "Tên hoạt chất", "Giá ước tính", "BĐDT"],
            [1, "PP1111111111", "G1.001", "Hoat chat A", "12.345.000", "123.450"],
            ["2 PP2222222222 G1.002 Hoat chat B 45.678.000", "456.780"],
            [1, "PP1111111111", "G1.001", "Hoat chat", "50mg", "Uống", "Viên", 42000, 1650, 2],
        ])
        report = inspect_ehsmt_xlsx(data)
        self.assertEqual(report["lot_count"], 2)
        self.assertEqual(report["summary_rows"], 2)
        self.assertEqual(report["missing_summary"], [])
        self.assertEqual(report["lots"][0]["GIA_TRI_UOC_TINH"], 12345000)
        self.assertEqual(report["lots"][1]["BAO_DAM_DU_THAU"], 456780)
        self.assertEqual(report["lots"][0]["EVIDENCE"]["row"], 2)
        self.assertFalse(report["verified"])

    def test_unresolved_technical_only_row_never_becomes_summary(self):
        report = inspect_ehsmt_xlsx(book([
            [9, "PP3333333333", "G1.009", "Aca...", "500mg", "Uống", "Viên", 1200, 1000, 2],
        ]))
        self.assertEqual(report["summary_rows"], 0)
        self.assertEqual(report["missing_summary"], ["G1.009"])
        self.assertEqual(report["lots"][0]["TRANG_THAI"], "CAN_KIEM_TRA_DONG_GOC")

    def test_conflicting_summary_must_not_be_selected(self):
        report = inspect_ehsmt_xlsx(book([
            [1, "PP1111111111", "G1.001", "Hoat chat A", "12.345.000", "123.450"],
            [1, "PP1111111111", "G1.001", "Hoat chat A", "99.345.000", "123.450"],
        ]))
        self.assertEqual(report["summary_rows"], 0)
        self.assertEqual(report["missing_summary"], ["G1.001"])
        self.assertFalse(report["lots"][0].get("GIA_TRI_UOC_TINH"))

    def test_row_limit_means_not_complete(self):
        report = inspect_ehsmt_xlsx(book([
            [1, "PP1111111111", "G1.001", "Hoat chat A", "12.345.000", "123.450"],
            [2, "PP2222222222", "G1.002", "Hoat chat B", "50.000.000", "500.000"],
        ]), max_rows=1)
        self.assertFalse(report["complete_read"])
        self.assertEqual(report["lot_count"], 1)
        self.assertTrue(report["warnings"])


if __name__ == "__main__":
    unittest.main()
