"""Regression for 87 source-anchored catalog rows but no registration/GMP ties.

Synthetic QA only: never private company data or original manufacturer files.
"""
import unittest

from tdv_nsx_workbench import summarize_product_field_coverage
from tdv_leadership_report import compare_sources, GREEN, YELLOW, RED

def product(i, *, ingredient="", drug_name="Paracetamol Brand",
            drug_strength="500 mg"):
    f={"PRODUCT_NAME":drug_name, "STRENGTH":drug_strength,
       "FACTORY":"Factory One"}
    if ingredient:
        f["INGREDIENT"]=ingredient
    return {
        "uid":"P%04d"%i, "fields":f,
        "file":"catalogue.xlsx","sha256":"0"*64,
        "origin":f"Sheet 1, row {i+1}", "conflicts":{},
        "evidence":{k:{"file":"catalogue.xlsx","source":f"Sheet 1, row {i+1}",
                       "sha256":"0"*64,"raw":v} for k,v in f.items()},
        "verified":False,
    }

def lot(ingredient="Paracetamol",strength="500 mg"):
    e={"HOAT_CHAT_HSMT":ingredient,"NONG_DO_HAM_LUONG":strength}
    return {"MA_THUOC":"G1.001","FILE_NGUON":"ehsmt.pdf",
        "HOAT_CHAT_HSMT":ingredient,"NONG_DO_HAM_LUONG":strength,
        "DANG_BAO_CHE":"Viên","DUONG_DUNG":"Uống",
        "EVIDENCE":{key:{"source":"ehsmt.pdf","raw":v} for key,v in e.items()}}

def report(products):
    return {"products":products,"links":[],"sources":[],"files":[{"filename":"catalogue.xlsx"}],
            "warnings":[],"review_queue":[],"traceability":{"products":[]}}

class MappingQA(unittest.TestCase):
    def test_87_catalogue_rows_are_not_87_verified_medicines(self):
        batch=report([product(i+1,drug_name="Medicine C %d"%i) for i in range(87)])
        coverage=summarize_product_field_coverage(batch)
        self.assertEqual(coverage["total"],87)
        self.assertEqual(coverage["fields"]["PRODUCT_NAME"],87)
        self.assertEqual(coverage["fields"]["INGREDIENT"],0)
        self.assertEqual(coverage["fields"]["REGISTRATION_NO"],0)
        self.assertEqual(coverage["linked_evidence"],0)
        self.assertFalse(coverage["verified"])
        result=compare_sources({"rows":[lot()]},batch)
        self.assertEqual(result["summary"]["nsx_products"],87)
        self.assertIsNone(result["summary"]["matching_percent_preliminary"])
        self.assertEqual(result["summary"]["green_criteria_preliminary"],0)
        self.assertEqual(result["summary"]["red_mismatch_preliminary"],0)
        self.assertEqual(result["summary"]["yellow_criteria"],4)

    def test_name_hint_is_readonly_not_green_or_lawful_proof(self):
        batch=report([product(1)])
        r=compare_sources({"rows":[lot()]},batch)
        row=r["comparison"][0]
        self.assertEqual(row["SO_UNG_VIEN_NSX"],0)
        self.assertEqual(row["SO_GOI_Y_TEN_NSX"],1)
        self.assertEqual(row["GOI_Y_TEN_NSX"][0]["product_id"],"P0001")
        self.assertEqual(row["GOI_Y_TEN_NSX"][0]["source_file"],"catalogue.xlsx")
        self.assertIsNone(row["TY_LE_KHOP_SO_BO"])
        self.assertEqual(row["SO_TIEU_CHI_DAT"],0)
        self.assertEqual(row["SO_TIEU_CHI_CHUA_DAT"],4)
        self.assertEqual(row["SO_TIEU_CHI_KHONG_KHOP"],0)
        self.assertFalse(r["bid_eligible"])

    def test_name_partial_does_not_guess(self):
        batch=report([product(1,drug_name="Paracetamolum")])
        r=compare_sources({"rows":[lot()]},batch)
        self.assertEqual(r["comparison"][0]["SO_GOI_Y_TEN_NSX"],0)

    def test_known_conflicting_ingredient_does_not_create_false_name_hint(self):
        batch=report([product(1,drug_name="Paracetamol Brand",ingredient="Amoxicillin")])
        r=compare_sources({"rows":[lot()]},batch)
        self.assertEqual(r["comparison"][0]["SO_GOI_Y_TEN_NSX"],0)
        self.assertEqual(r["comparison"][0]["SO_TIEU_CHI_KHONG_KHOP"],0)
        self.assertFalse(r["verified"])

    def test_ratio_denominator_only_ehsmt_requirements_of_uniquely_linked_pair(self):
        batch=report([product(1,ingredient="Paracetamol")])
        r=compare_sources({"rows":[lot()]},batch)
        self.assertEqual(r["summary"]["lots_uniquely_linked"],1)
        self.assertEqual(r["summary"]["linked_requirements"],4)
        self.assertEqual(r["summary"]["green_criteria_preliminary"],2)
        self.assertEqual(r["summary"]["matching_percent_preliminary"],50.0)
        self.assertEqual(r["comparison"][0]["TY_LE_KHOP_SO_BO"],50.0)
        self.assertEqual(r["summary"]["fully_verified"],0)

    def test_missing_ehsmt_criteria_not_counted_as_failure(self):
        batch=report([product(1,ingredient="Paracetamol")])
        t=lot()
        t.pop("DANG_BAO_CHE")
        t.pop("DUONG_DUNG")
        r=compare_sources({"rows":[t]},batch)
        self.assertEqual(r["summary"]["linked_requirements"],2)
        self.assertEqual(r["summary"]["matching_percent_preliminary"],100.0)
        self.assertEqual(r["summary"]["yellow_criteria"],2)
        self.assertEqual(r["summary"]["fully_verified"],0)

if __name__=="__main__":
    unittest.main()
