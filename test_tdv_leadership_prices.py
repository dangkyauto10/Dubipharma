import unittest
from tdv_leadership_prices import parse_vnd, compare_prices

class PriceReportTests(unittest.TestCase):
    def test_prices_adjacent_and_bid_is_manual(self):
        r=compare_prices([{"Mã lô E-HSMT":"G1.001","Giá định mức E-HSMT":1650,
            "Giá báo NSX":1200,"Giá chào thầu (LĐ nhập)":1500,
            "Xác minh giá":"ĐÃ XÁC MINH"}])[0]
        self.assertEqual(r["Giá định mức E-HSMT"],1650)
        self.assertEqual(r["Giá báo NSX"],1200)
        self.assertEqual(r["Giá chào thầu (LĐ nhập)"],1500)
        self.assertEqual(r["Chênh lệch chào - định mức"],-150)
    def test_no_invented_price(self):
        r=compare_prices([{"Mã lô E-HSMT":"G1.002"}])[0]
        self.assertIsNone(r["Giá định mức E-HSMT"])
        self.assertIsNone(r["Giá báo NSX"])
        self.assertIsNone(r["Giá chào thầu (LĐ nhập)"])
        self.assertEqual(r["Cảnh báo"],"CHƯA XÁC MINH NGUỒN GIÁ")
    def test_over_plan_warning(self):
        r=compare_prices([{"Giá định mức E-HSMT":"1.650","Giá báo NSX":"1,200",
           "Giá chào thầu (LĐ nhập)":"1800","Xác minh giá":"ĐÃ XÁC MINH"}])[0]
        self.assertEqual(r["Cảnh báo"],"CHÀO VƯỢT ĐỊNH MỨC")
    def test_reject_ambiguous_decimal(self):
        self.assertIsNone(parse_vnd("1.65"))
if __name__=="__main__":
    unittest.main()
