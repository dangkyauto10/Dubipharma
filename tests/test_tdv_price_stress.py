"""Bounded synthetic stress and integrity regression; never performs real tender actions."""
import unittest
import time
from decimal import Decimal
from tdv_price_controls import calculate_price, price_permission, append_draft, draft_in_scope

BASE={"project_id":"DA-TQ-01","package_id":"BP2600899572","ehsmt_revision_id":"R01"}
def result(price):
    return calculate_price(
        quote_before="9000",quote_after="9450",supplier_vat_percent="5",
        extra_cost="300",proposed_bid_gross=str(price),
        quantity="10000",ehsmt_reference="12000",reference_basis="vat_included",
    )

class BoundedPriceStressQA(unittest.TestCase):
    def test_3000_calculations_exact_and_no_mutation(self):
        for i in range(3000):
            r=result(9800+i)
            self.assertEqual(Decimal(r["estimated_total_bid_gross"]),
                             Decimal(9800+i)*10000)
            self.assertEqual(r["status"],"DU_THAO_TINH_TOAN_CHUA_PHE_DUYET")
        self.assertEqual(result(11500)["reference_minus_bid"],"500")
    def test_600_scoped_drafts_append_and_revisions(self):
        existing=[]
        for n in range(600):
            existing=append_draft(
                existing,permission="prepare",global_role="analyst",
                scope=BASE,lot_id=f"G1.{n+1:03d}",nsx_id=f"P{n+1:04d}",
                author_email="analyst@example.com",result=result(11500),
                quote_reference="mock-source.xlsx SheetQ!D10",
                tender_reference="test-E-HSMT.pdf page30")
        self.assertEqual(len(existing),600)
        self.assertEqual(len(draft_in_scope(existing,BASE)),600)
        self.assertEqual(draft_in_scope(existing,{**BASE,"project_id":"DA-TQ-02"}),[])
        self.assertTrue(all(x["status"]=="DRAFT_RAM_ONLY_NOT_APPROVED" for x in existing))
    def test_many_grants_match_only_one_exact_scope(self):
        grants=[{"email":f"employee{i}@example.com",**BASE,"permission":"prepare"}
                for i in range(1000)]
        config={"grants":grants}
        self.assertEqual(price_permission("employee777@example.com","analyst",BASE,config),"prepare")
        self.assertIsNone(price_permission("employee777@example.com","analyst",
                       {**BASE,"package_id":"OTHER-00001"},config))
    def test_alternate_tender_lot_code_supported(self):
        d=append_draft([],permission="prepare",global_role="analyst",
           scope=BASE,lot_id="PKG.123-A",nsx_id="P0001",
           author_email="analyst@example.com",result=result(11500),
           quote_reference="mock-source.xlsx",tender_reference="source.pdf")
        self.assertEqual(d[0]["lot_id"],"PKG.123-A")
    def test_zero_supplier_price_rejected(self):
        with self.assertRaises(ValueError):
            calculate_price(quote_before="0",quote_after="0",
               supplier_vat_percent="5",extra_cost="0",
               proposed_bid_gross="10",quantity="1")
if __name__=="__main__":unittest.main()
