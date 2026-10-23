"""Synthetic pricing access, VAT and RAM-draft regression tests."""
import unittest
from tdv_auth import may_open_section
from tdv_price_controls import (
    PRICE_PAGE, price_permission, may_price, calculate_price, append_draft,
    draft_in_scope)
S={"project_id":"DA-TQ-01","package_id":"BP2600899572","ehsmt_revision_id":"R01"}
V={"grants":[{"email":"buyer@example.com",**S,"permission":"prepare"},
             {"email":"chief@example.com",**S,"permission":"approve"},
             {"email":"observer@example.com",**S,"permission":"view"}]}

def calc(**kw):
    p=dict(quote_before="9000",quote_after="9450",
           supplier_vat_percent="5",extra_cost="300",
           proposed_bid_gross="11500",quantity="10000",
           ehsmt_reference="12000",reference_basis="vat_included")
    p.update(kw)
    return calculate_price(**p)

class PricePermissionQA(unittest.TestCase):
    def test_admin_without_grant_denied(self):
        self.assertIsNone(price_permission("admin@example.com","admin",S,V))
    def test_no_config_denies(self):
        self.assertIsNone(price_permission("chief@example.com","admin",S,None))
        self.assertIsNone(price_permission("chief@example.com","admin",S,{}))
    def test_approved_grants_exact(self):
        self.assertEqual(price_permission("buyer@example.com","analyst",S,V),"prepare")
        self.assertEqual(price_permission("chief@example.com","admin",S,V),"approve")
        self.assertEqual(price_permission("observer@example.com","viewer",S,V),"view")
    def test_project_mismatch_denied(self):
        self.assertIsNone(price_permission("buyer@example.com","analyst",
                          {**S,"project_id":"DA-TQ-02"},V))
    def test_package_mismatch_denied(self):
        self.assertIsNone(price_permission("buyer@example.com","analyst",
                          {**S,"package_id":"BP9999999999"},V))
    def test_revision_mismatch_denied(self):
        self.assertIsNone(price_permission("buyer@example.com","analyst",
                          {**S,"ehsmt_revision_id":"R02"},V))
    def test_viewer_cannot_elevate_with_prepare_grant(self):
        self.assertIsNone(price_permission("buyer@example.com","viewer",S,V))
    def test_uppercase_and_unknown_denied(self):
        self.assertIsNone(price_permission("Buyer@example.com","analyst",S,V))
        self.assertIsNone(price_permission("buyer@example.com","stranger",S,V))
    def test_duplicate_grant_denied(self):
        v={"grants":[V["grants"][0],V["grants"][0]]}
        self.assertIsNone(price_permission("buyer@example.com","analyst",S,v))
    def test_wildcard_grant_denied(self):
        self.assertIsNone(price_permission("buyer@example.com","analyst",S,
                          {"grants":[{"email":"buyer@example.com",
                          "project_id":"*","package_id":"*",
                          "ehsmt_revision_id":"*","permission":"approve"}]}))
    def test_unknown_grant_denied(self):
        self.assertIsNone(price_permission("buyer@example.com","analyst",S,
                          {"grants":[{**V["grants"][0],"permission":"superuser"}]}))
    def test_generic_access_always_denies_price(self):
        for role in ("admin","analyst","viewer","unknown"):
            self.assertFalse(may_open_section(role,PRICE_PAGE))
    def test_page_access_and_prepare_separate(self):
        self.assertTrue(may_price("view","view","viewer"))
        self.assertFalse(may_price("view","prepare","viewer"))
        self.assertTrue(may_price("prepare","prepare","analyst"))
    def test_no_fake_final_approval(self):
        for role in ("admin","analyst","viewer"):
            for p in ("view","prepare","approve",None):
                self.assertFalse(may_price(p,"final_approve",role))

class PriceMathQA(unittest.TestCase):
    def test_vat_5_percent_correct(self):
        r=calc()
        self.assertEqual(r["quote_before_vat"],"9000")
        self.assertEqual(r["quote_after_vat"],"9450")
        self.assertEqual(r["cost_estimate_gross"],"9750")
        self.assertEqual(r["estimated_total_bid_gross"],"115000000")
        self.assertEqual(r["reference_minus_bid"],"500")
    def test_after_only_derives_before(self):
        r=calc(quote_before="")
        self.assertEqual(r["quote_before_vat"],"9000")
    def test_before_only_derives_after(self):
        r=calc(quote_after="")
        self.assertEqual(r["quote_after_vat"],"9450")
    def test_price_conflict_is_hard_error(self):
        with self.assertRaises(ValueError):calc(quote_after="9550")
    def test_zero_vat_is_valid_if_explicit(self):
        r=calc(quote_before="5000",quote_after="5000",supplier_vat_percent="0")
        self.assertEqual(r["quote_after_vat"],"5000")
    def test_vat_oversize_rejected(self):
        with self.assertRaises(ValueError):calc(supplier_vat_percent="101")
    def test_missing_vat_rejected(self):
        with self.assertRaises(ValueError):calc(supplier_vat_percent="")
    def test_missing_both_prices_rejected(self):
        with self.assertRaises(ValueError):calc(quote_before="",quote_after="")
    def test_negative_and_formula_strings_rejected(self):
        for v in ("-1","=SUM(A1:A2)","nan","inf","10e9"):
            with self.subTest(value=v):
                with self.assertRaises(ValueError):calc(proposed_bid_gross=v)
    def test_zero_or_fractional_quantity_rejected(self):
        for v in ("0","1.5"):
            with self.assertRaises(ValueError):calc(quantity=v)
    def test_vat_incompatible_reference_not_compared(self):
        r=calc(reference_basis="unknown")
        self.assertEqual(r["comparison_status"],"CHUA_CO_CO_SO_SO_SANH")
        self.assertEqual(r["reference_minus_bid"],"")
    def test_without_vat_ref_requires_bid_vat(self):
        r=calc(reference_basis="vat_excluded",bid_vat_percent="")
        self.assertEqual(r["comparison_status"],"CHUA_CO_CO_SO_SO_SANH")
    def test_without_vat_ref_with_explicit_bid_vat(self):
        r=calc(reference_basis="vat_excluded",bid_vat_percent="5",
               ehsmt_reference="10952")
        self.assertEqual(r["offer_comparison_basis"],"10952")
        self.assertEqual(r["reference_minus_bid"],"0")
    def test_above_reference_is_warning_not_legal_disqualifier(self):
        r=calc(proposed_bid_gross="13000")
        self.assertEqual(r["comparison_status"],"VUOT_MUC_THAM_CHIEU_SO_BO")
        self.assertEqual(r["status"],"DU_THAO_TINH_TOAN_CHUA_PHE_DUYET")
        self.assertTrue(r["warnings"])
    def test_below_cost_warning(self):
        r=calc(proposed_bid_gross="9000")
        self.assertTrue(any("thấp hơn" in w for w in r["warnings"]))
    def test_without_reference_no_fake_limit(self):
        self.assertEqual(calc(ehsmt_reference="")["comparison_status"],
                         "CHUA_CO_CO_SO_SO_SANH")

class PriceDraftQA(unittest.TestCase):
    def make(self,**kw):
        opts=dict(permission="prepare",global_role="analyst",scope=S,
                  lot_id="G1.001",nsx_id="P0001",author_email="buyer@example.com",
                  result=calc(),quote_reference="Bao_gia.xlsx Sheet Q D10",
                  tender_reference="E-HSMT G1 page 330")
        opts.update(kw)
        return opts
    def test_unauthorized_draft_fails(self):
        with self.assertRaises(PermissionError):
            append_draft([],**self.make(permission=None))
    def test_global_viewer_cannot_write(self):
        with self.assertRaises(PermissionError):
            append_draft([],**self.make(global_role="viewer"))
    def test_unlinked_nsx_rejected(self):
        with self.assertRaises(ValueError):
            append_draft([],**self.make(nsx_id=""))
    def test_missing_price_reference_rejected(self):
        with self.assertRaises(ValueError):
            append_draft([],**self.make(quote_reference=""))
    def test_missing_tender_reference_rejected(self):
        with self.assertRaises(ValueError):
            append_draft([],**self.make(tender_reference=""))
    def test_no_scope_draft_rejected(self):
        with self.assertRaises(ValueError):
            append_draft([],**self.make(scope={}))
    def test_two_drafts_keep_history(self):
        rows=append_draft([],**self.make())
        rows2=append_draft(rows,**self.make())
        self.assertEqual([x["revision"] for x in rows2],[1,2])
        self.assertEqual(len(rows),1)
        self.assertTrue(all(x["status"]=="DRAFT_RAM_ONLY_NOT_APPROVED" for x in rows2))
    def test_different_scope_not_visible(self):
        rows=append_draft([],**self.make())
        self.assertEqual(len(draft_in_scope(rows,{**S,"project_id":"DA-TQ-02"})),0)
    def test_product_revision_is_distinct(self):
        rows=append_draft([],**self.make())
        rows=append_draft(rows,**self.make(lot_id="G1.002"))
        self.assertEqual(rows[-1]["revision"],1)

if __name__=="__main__": unittest.main()
