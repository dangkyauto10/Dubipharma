"""NSX data audit front-end, synthetic only; never publish NSX source docs."""
from contextlib import nullcontext
import unittest

from tdv_nsx_workbench import render_nsx_conflict_review, render_nsx_workbench


class FakeStreamlit:
    def __init__(self):
        self.titles=[]
        self.expanders=[]
        self.frames=[]
        self.warnings=[]
        self.errors=[]
        self.captions=[]
        self.info_items=[]
    def warning(self,text): self.warnings.append(text)
    def caption(self,text): self.captions.append(text)
    def info(self,text): self.info_items.append(text)
    def error(self,text): self.errors.append(text)
    def markdown(self,text): self.titles.append(text)
    def dataframe(self,frame,**kwargs): self.frames.append(frame)
    def expander(self,label,**kwargs):
        self.expanders.append((label,kwargs))
        return nullcontext()
    def container(self,**kwargs): return nullcontext()


def conflict_product():
    a,b={
      "PRODUCT_NAME":"Drug A","STRENGTH":"50 mg","FACTORY":"Factory A"
    },{
      "PRODUCT_NAME":"Drug A","STRENGTH":"100 mg","FACTORY":"Factory A"
    }
    def row(sheet,fields):
        return {"file":"source.xlsx","sha256":"f"*64,
                "origin":f"Sheet {sheet}, dòng 2",
                "fields":fields,"evidence":{
                    key:{"file":"source.xlsx","sha256":"f"*64,
                         "source":f"Sheet {sheet}, hàng 2, cột {i+1}",
                         "raw":value,"value":value}
                    for i,(key,value) in enumerate(fields.items())
                }}
    first,second=row("Biểu 05",a),row("ÁP",b)
    return {"uid":"P0004","fields":a,"conflicts":{"STRENGTH":[{
        "raw":"100 mg","source":"Sheet ÁP, hàng 2, cột 2"}]},
        "source_rows":[first,second],"file":"source.xlsx",
        "sha256":"f"*64}


class NsXVisibilityQA(unittest.TestCase):
    def test_real_values_render_first_and_version_mark_shown(self):
        ui=FakeStreamlit()
        render_nsx_conflict_review([conflict_product()],st_module=ui)
        self.assertEqual(len(ui.frames),3)
        self.assertEqual(ui.frames[0].iloc[0]["Giá trị nguồn 1"],"50 mg")
        self.assertEqual(ui.frames[0].iloc[0]["Giá trị nguồn 2"],"100 mg")
        self.assertIn("Biểu 05",ui.frames[0].iloc[0]["Ô nguồn 1"])
        self.assertIn("Sheet ÁP",ui.frames[0].iloc[0]["Ô nguồn 2"])
        self.assertEqual(len(ui.frames[1].iloc[0]["SHA256 nguồn 1"]),64)
        self.assertIn("2026-10-22B",ui.captions[0])
        self.assertIn("ĐỐI CHIẾU 2 NGUỒN",ui.expanders[0][0])
        self.assertTrue(ui.expanders[0][1].get("expanded"))
        self.assertIn("Danh sách tổng hợp",ui.expanders[1][0])
        self.assertFalse(ui.errors)
        self.assertEqual(ui.frames[2][0]["Trạng thái"],"CHƯA XÁC MINH")

    def test_build_marker_at_page_top_even_without_uploaded_files(self):
        ui=FakeStreamlit()
        ui.session_state={}
        ui.checkbox=lambda *args,**kwargs: False
        from unittest.mock import patch
        with patch("tdv_nsx_workbench.st",ui):
            render_nsx_workbench()
        self.assertTrue(any("2026-10-22B" in value for value in ui.captions))
        self.assertTrue(any("SEE PRO" in value for value in ui.titles))
        self.assertTrue(ui.warnings)

    def test_failure_is_visible_never_silently_missing(self):
        ui=FakeStreamlit()
        p=conflict_product()
        p["source_rows"]=[]
        # If original citations aren't supplied, a failed comparison must be
        # explicit to the human reviewer; never render an implicit pass.
        from unittest.mock import patch
        with patch("tdv_nsx_workbench.compare_conflict_sources",return_value=[]):
            render_nsx_conflict_review([p],st_module=ui)
        self.assertTrue(ui.errors)
        self.assertEqual(len(ui.frames),1)
        self.assertTrue(any("KHÔNG TẠO ĐƯỢC" in x for x in ui.errors))


if __name__=="__main__":
    unittest.main()
