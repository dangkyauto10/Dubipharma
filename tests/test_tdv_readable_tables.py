"""UI-only TDV table QA: no actual NSX/E-HSMT material."""
import unittest
from contextlib import nullcontext

import pandas as pd

from tdv_readable_tables import build_table_html, render_readable_table


class FakeStreamlit:
    def __init__(self, picked=1, state=None):
        self.session_state = state if state is not None else {}
        self.picked = picked
        self.pages = []
        self.html = []
        self.captions = []
        self.raw = []
        self.info_messages = []
    def selectbox(self, label, options, **kwargs):
        self.pages.append((label, list(options), kwargs))
        self.session_state[kwargs["key"]] = self.picked
        return self.picked
    def markdown(self, html, **kwargs):
        assert kwargs.get("unsafe_allow_html")
        self.html.append(html)
    def caption(self, caption):
        self.captions.append(caption)
    def expander(self, label):
        return nullcontext()
    def dataframe(self, value, **kwargs):
        self.raw.append(value)
    def info(self, value):
        self.info_messages.append(value)


class ReadableTableQA(unittest.TestCase):
    def test_center_headers_all_numeric_cells_and_vertical_alignment(self):
        html=build_table_html(
            ["Mã G1 nhận diện", "Dòng kỹ thuật", "Loại"],
            [{"Mã G1 nhận diện":770, "Dòng kỹ thuật":770, "Loại":"E_HSMT"}],
        )
        self.assertEqual(html.count('scope="col"'),3)
        self.assertEqual(html.count('<td class="tdv-center"'),3)
        self.assertIn("text-align:center!important",html)
        self.assertIn("vertical-align:middle!important",html)
        self.assertIn('>770</td>',html)
        self.assertIn("position:sticky",html)

    def test_long_supplier_text_wraps_and_preserves_full_original(self):
        long_text="Đối chiếu bản gốc và lưu nguồn — "+"Giấy phép thử " * 30
        hash_value="abcde12345"*6+"abcd"
        h=build_table_html(["Tệp", "Hướng xử lý","SHA256"], [{
            "Tệp":"Hồ sơ mời thầu (G1-SYT).pdf",
            "Hướng xử lý":long_text, "SHA256":hash_value,
        }])
        self.assertIn("overflow-wrap:anywhere",h)
        self.assertIn("white-space:normal",h)
        self.assertIn(long_text,h)
        self.assertIn(hash_value,h)
        self.assertIn("Hồ sơ mời thầu",h)
        self.assertNotIn("text-overflow:ellipsis",h)
        self.assertEqual(h.count('class="tdv-wide"'),6)

    def test_user_filename_and_excerpt_are_escaped_not_executable(self):
        evil='<img src=x onerror="alert(1)">'
        rendered=build_table_html(["Tệp","TRICH_DAN"], [{
            "Tệp":evil,
            "TRICH_DAN":'<script>alert("XSS")</script> & báo cáo',
        }],label='Test "quoted"')
        self.assertNotIn('<img',rendered)
        self.assertNotIn('<script>',rendered)
        self.assertNotIn('onerror="alert',rendered)
        self.assertIn('&lt;img',rendered)
        self.assertIn('&lt;script',rendered)
        self.assertIn('&amp; báo cáo',rendered)
        self.assertIn("Test &quot;quoted&quot;",rendered)

    def test_page_2_770_rows_shows_only_25_with_complete_raw_fallback(self):
        original=pd.DataFrame([
            {"Mã thuốc":f"G1.{i:03d}","Hoạt chất":f"Drug {i}"}
            for i in range(1,771)
        ])
        st=FakeStreamlit(picked=2)
        render_readable_table(st,original,key="test_table",
                              label="Danh mục",page_size=25)
        self.assertEqual(st.pages[0][1],list(range(1,32)))
        self.assertIn("dòng 26–50 / 770",st.captions[0])
        self.assertIn("G1.026",st.html[0])
        self.assertIn("G1.050",st.html[0])
        self.assertNotIn("G1.001",st.html[0])
        self.assertNotIn("G1.051",st.html[0])
        self.assertEqual(len(st.raw[0]),770)
        self.assertEqual(original.iloc[25]["Mã thuốc"],"G1.026")

    def test_filtered_subset_resets_out_of_bounds_page(self):
        frame=pd.DataFrame([{"Mã":"G1.001"},{"Mã":"G1.002"}])
        state={"filter_table_page":30}
        st=FakeStreamlit(state=state)
        render_readable_table(st,frame,key="filter_table",label="Bảng lọc")
        self.assertEqual(state["filter_table_page"],1)
        self.assertEqual(len(st.pages),0)
        self.assertIn("dòng 1–2 / 2",st.captions[0])

    def test_empty_search_is_explained_and_source_is_not_mutated(self):
        st=FakeStreamlit()
        df=pd.DataFrame({"Mã":[]})
        render_readable_table(st,df,key="empty",label="Bảng trống")
        self.assertTrue(st.info_messages)
        self.assertFalse(st.html)
        self.assertEqual(len(df),0)

    def test_fallback_keep_full_value_and_html_without_truncation(self):
        long_code="a"*64
        df=pd.DataFrame([{"SHA256":long_code,"Mã G1 nhận diện":770}])
        st=FakeStreamlit()
        render_readable_table(st,df,key="source",label="Nguồn")
        self.assertIn(long_code,st.html[0])
        self.assertEqual(st.raw[0].iloc[0]["SHA256"],long_code)
        self.assertEqual(st.raw[0].iloc[0]["Mã G1 nhận diện"],770)


if __name__ == "__main__":
    unittest.main()
