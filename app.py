"""TDV QC7 Online — giao diện lãnh đạo, bản thử KHÔNG CHỨA DỮ LIỆU THẬT."""
from __future__ import annotations
import re
import unicodedata
import base64
import io
from collections import deque
from decimal import Decimal, InvalidOperation
from pathlib import Path
import streamlit as st

try:
    from PIL import Image
except ImportError:
    Image = None  # Fall back to original brand asset if Pillow is not installed.


st.set_page_config(
    page_title="TDV QC7 ONLINE | DUBIPHARMA DŨNG BÍCH",
    page_icon="💊", layout="wide", initial_sidebar_state="expanded"
)

ROOT = Path(__file__).resolve().parent

def asset_base64(filename: str) -> str:
    """Local public-safe branding only; never load remote files or secret keys."""
    path = ROOT / "assets" / filename
    try:
        data = path.read_text(encoding="ascii").strip()
        if len(data) > 256 and re.fullmatch(r"[A-Za-z0-9+/=\s]+", data):
            return data
    except OSError:
        pass
    return ""

LOGO_DATA = asset_base64("tdv_logo.webp.b64")
ART_DATA = asset_base64("tdv_art.webp.b64")


@st.cache_data(show_spinner=False)
def transparent_brand_logo(encoded: str) -> tuple[str, str]:
    """Remove edge-connected pale-blue paper from the genuine DUBI logo.

    Do not recolor white lettering inside the logo. Pillow is a Streamlit
    dependency; if unavailable, fall back to the original asset.
    """
    if not encoded or Image is None:
        return encoded, "webp"
    try:
        original = Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGBA")
        width, height = original.size
        if width * height > 2_000_000:
            return encoded, "webp"
        pixels = original.load()
        samples = [
            pixels[0, 0], pixels[width - 1, 0],
            pixels[0, height - 1], pixels[width - 1, height - 1],
        ]
        paper = tuple(round(sum(pixel[channel] for pixel in samples) / 4) for channel in range(3))
        seen = bytearray(width * height)
        frontier = deque()

        def delta(x: int, y: int) -> int:
            rgb = pixels[x, y]
            return max(abs(rgb[channel] - paper[channel]) for channel in range(3))

        for x in range(width):
            frontier.append((x, 0))
            frontier.append((x, height - 1))
        for y in range(height):
            frontier.append((0, y))
            frontier.append((width - 1, y))

        while frontier:
            x, y = frontier.popleft()
            idx = y * width + x
            if seen[idx]:
                continue
            seen[idx] = 1
            distance = delta(x, y)
            if distance > 29:
                continue
            r, g, b, _ = pixels[x, y]
            # Preserve anti-aliased edges as partially transparent pixels.
            opacity = 0 if distance <= 10 else min(255, round((distance - 10) / 19 * 255))
            pixels[x, y] = (r, g, b, opacity)
            if x > 0:
                frontier.append((x - 1, y))
            if x + 1 < width:
                frontier.append((x + 1, y))
            if y > 0:
                frontier.append((x, y - 1))
            if y + 1 < height:
                frontier.append((x, y + 1))

        output = io.BytesIO()
        original.save(output, format="PNG", optimize=True)
        return base64.b64encode(output.getvalue()).decode("ascii"), "png"
    except Exception:
        return encoded, "webp"


LOGO_DISPLAY_DATA, LOGO_MIME = transparent_brand_logo(LOGO_DATA)


STYLE = """
<style>
:root {--navy:#0c3167;--blue:#1966b5;--border:#dce8f4;--soft:#f3f8fe;}
html,body,[data-testid="stAppViewContainer"] {background:#f3f7fc;color:#193b63;}
[data-testid="stHeader"] {background:#f3f7fc; z-index:1000;}
[data-testid="stSidebar"] {background:linear-gradient(160deg,#f5faff,#eaf3fe);border-right:1px solid #d9e7f5;}
.block-container {max-width:1650px;padding-top:0.6rem;padding-bottom:.4rem;padding-left:1.3rem;padding-right:1.3rem;}
h1,h2,h3 {color:#0b316b;}
[data-testid="stMetric"] {padding:12px 14px;background:#fff;border:1px solid var(--border);border-radius:15px;}
.tdv-left-head {padding:12px 9px 16px;border-bottom:1px solid #cfdfed;background:#eff7ff;}
.tdv-left-brand {display:flex;align-items:center;justify-content:center;gap:9px;}
.tdv-logo-word {font-size:1.62rem;line-height:1.05;letter-spacing:-.06em;font-weight:900;
 background:linear-gradient(135deg,#f5c829 0%,#e42f4a 48%,#1c9857 88%);
 color:transparent;background-clip:text;-webkit-background-clip:text;}
.tdv-sidebar-name {font-size:.97rem;color:#103b75;font-weight:850;text-align:center;margin-top:9px;}
.tdv-sidebar-sub {font-size:.76rem;color:#607b98;text-align:center;}
.tdv-left-note {background:#fff8df;border:1px solid #e4d9ab;color:#805b16;
 border-radius:10px;padding:9px 11px;font-size:.79rem;margin-top:12px;}
.tdv-heading-section {font-size:.74rem;color:#647b94;letter-spacing:.08em;font-weight:800;padding:14px 4px 2px;}
.tdv-main-hero {background:linear-gradient(105deg,#fff 0%,#f0f8ff 57%,#d3eaf9 100%);
 border:1px solid #d5e7f6;box-shadow:0 4px 18px #173b710c;border-radius:18px;
 position:relative;overflow:hidden;min-height:148px;display:flex;align-items:center;gap:18px;
 padding:18px 22px;margin:0 0 6px;}
.tdv-main-logo {width:128px;min-width:128px;display:flex;justify-content:center;align-items:center;
 border-right:1px solid #c8dced;padding-right:16px;min-height:99px;}
.tdv-main-body {min-width:0;max-width:900px;position:relative;z-index:2;}
.tdv-pill {display:inline-block;background:#d7f2e2;color:#09623d;border-radius:24px;
 padding:4px 11px;font-weight:780;font-size:.7rem;}
.tdv-main-title {font-size:clamp(1.18rem,2vw,2rem);line-height:1.16;font-weight:900;color:#102f65;
 margin:8px 0 6px;letter-spacing:.01em;}
.tdv-main-subtitle {color:#4b6b87;font-size:.85rem;}
.tdv-main-art {position:absolute;right:0;top:0;bottom:0;width:24%;
 background:radial-gradient(circle at 78% 29%,#d6fbff 0 10%,transparent 11%),
 radial-gradient(circle at 65% 76%,#61a9d066 0 17%,transparent 18%);
 opacity:.75;}
.tdv-main-art:before{content:"✚";position:absolute;right:21%;top:17%;color:#fff;
 font-size:4.8rem;text-shadow:0 1px 19px #0d74a4;font-weight:800;}
.tdv-tags {display:flex;flex-wrap:wrap;gap:7px;margin-top:8px;}
.tdv-tags span {background:#ffffffdb;border:1px solid #e0eaf3;border-radius:10px;
 padding:4px 8px;font-size:.7rem;color:#28547d;font-weight:700;}
.tdv-notice {background:#fff9e8;border:1px solid #efdfb1;border-radius:11px;
 color:#795714;padding:10px 13px;font-size:.83rem;margin:6px 0 10px;}
.tdv-crumb{color:#647d99;font-size:.78rem;padding:2px 1px 9px;}
.tdv-panel {background:#fff;border:1px solid #dce8f4;border-radius:16px;
 padding:17px 19px;min-height:118px;margin-bottom:9px;box-shadow:0 3px 14px #23456a09;}
.tdv-panel h3{font-size:1.06rem;margin:0 0 10px;color:#174474;}
.tdv-panel p{font-size:.89rem;color:#5f7692;margin:0;}
.tdv-empty {border:1px dashed #c7d9e9;background:#fff;border-radius:12px;
 padding:17px;color:#52718c;}
.tdv-page-title{font-size:1.4rem;font-weight:790;color:#123d76;margin:7px 0 10px;}
.st-key-tdv_sidebar_scroll [data-testid="stRadio"] label {font-size:.91rem;}
.st-key-tdv_sidebar_scroll [data-testid="stRadio"] div[role="radiogroup"] {gap:.15rem;}
/* DESKTOP: two separately scrolling business areas with stationary brand/header.
   Keep Streamlit's own sidebar collapse/expand control clickable. */
@media (min-width: 900px) and (min-height: 570px) {
 [data-testid="stSidebar"] [data-testid="stSidebarContent"]{overflow:hidden!important;}
 [data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{
    height:100%!important;min-height:0!important;overflow:hidden!important;}
 [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {
    display:flex!important;flex-direction:column!important;height:100%!important;min-height:0!important;
    overflow:hidden!important;gap:0!important;}
 .st-key-tdv_sidebar_brand{flex:0 0 auto!important;min-height:0;position:relative;z-index:3;}
 .st-key-tdv_sidebar_scroll {flex:1 1 auto!important;min-height:0!important;
    overflow-y:auto!important;overscroll-behavior-y:contain;padding:0 8px 16px 2px;}
 [data-testid="stMain"]{overflow:hidden!important;}
 [data-testid="stMainBlockContainer"]{
    height:calc(100dvh - 3.25rem)!important;max-height:calc(100dvh - 3.25rem)!important;
    display:flex!important;flex-direction:column!important;min-height:0!important;overflow:hidden!important;}
 [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]{
    height:100%!important;min-height:0!important;display:flex!important;
    flex-direction:column!important;overflow:hidden!important;gap:0!important;}
 .st-key-tdv_main_fixed{flex:0 0 auto!important;min-height:0!important;position:relative;z-index:5;}
 .st-key-tdv_main_scroll {flex:1 1 auto!important;min-height:0!important;
    overflow-y:auto!important;overscroll-behavior:contain;padding:0 7px 20px 1px;}
 .st-key-tdv_sidebar_scroll::-webkit-scrollbar,
 .st-key-tdv_main_scroll::-webkit-scrollbar{width:7px;}
 .st-key-tdv_sidebar_scroll::-webkit-scrollbar-thumb,
 .st-key-tdv_main_scroll::-webkit-scrollbar-thumb{background:#c4d4e5;border-radius:9px;}
}
/* Compact windows keep normal page scrolling rather than risk inaccessible content. */
@media (max-width:899px), (max-height:569px){
 [data-testid="stMain"]{overflow-y:auto!important;}
 .st-key-tdv_main_fixed {position:sticky;top:0;z-index:5;background:#f3f7fc;padding-bottom:3px;}
 .tdv-main-hero {min-height:100px;padding:11px;gap:11px;}
 .tdv-main-logo{width:73px;min-width:73px;min-height:64px;padding-right:8px;}
 .tdv-main-title{font-size:1.07rem;}
 .tdv-main-art,.tdv-tags{display:none;}
 .tdv-main-subtitle{font-size:.72rem;}
}

/* Some Streamlit releases wrap each keyed container in an element container.
   Allocate height/scroll to that FLEX CHILD too, not just its nested block. */
@media (min-width:900px) and (min-height:570px) {
 [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] > div:has(.st-key-tdv_sidebar_brand) {
   flex:0 0 auto!important;min-height:0!important;z-index:3;position:relative;
 }
 [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] > div:has(.st-key-tdv_sidebar_scroll) {
   flex:1 1 auto!important;min-height:0!important;overflow-y:auto!important;
 }
 [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:has(.st-key-tdv_main_fixed) {
   flex:0 0 auto!important;min-height:0!important;position:relative;z-index:5;
 }
 [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:has(.st-key-tdv_main_scroll) {
   flex:1 1 auto!important;min-height:0!important;overflow-y:auto!important;
   overscroll-behavior:contain;
 }
}

/* Approved executive dashboard visual restoration (19/10 reference). */
.tdv-left-head {background:#edf6ff!important;padding:9px 12px 15px!important;}
.tdv-left-brand img {width:156px!important;max-height:130px!important;object-fit:contain!important;}
.tdv-sidebar-name {font-size:1.05rem!important;margin-top:2px!important;}
.tdv-main-hero {min-height:221px!important;gap:20px!important;padding:17px 22px!important;
 background:linear-gradient(106deg,#f3faff 0%,#eaf6ff 58%,#cde9f9 100%)!important;
 border-color:#c9e2f2!important;}
.tdv-main-logo {width:218px!important;min-width:218px!important;min-height:162px!important;
 padding-right:19px!important;}
.tdv-main-logo img {width:193px!important;max-height:160px!important;object-fit:contain!important;}
.tdv-main-body {width:calc(100% - 228px);max-width:980px;}
.tdv-main-title {font-size:clamp(1.4rem,2.4vw,2.21rem)!important;text-align:center;
 letter-spacing:0!important;line-height:1.14!important;}
.tdv-main-subtitle {font-size:.97rem!important;text-align:center;}
.tdv-main-hero .tdv-pill {font-size:.74rem;padding:5px 12px;}
.tdv-main-hero .tdv-tags {justify-content:center;gap:10px;margin-top:12px;}
.tdv-main-hero .tdv-tags span {background:#fffc;border:1px solid #d9e5f1;padding:6px 10px;}
.tdv-main-art {width:23%;opacity:.52;pointer-events:none;}
.tdv-main-art:before {content:"" !important;}
.tdv-section-label {font-size:1.3rem;font-weight:850;color:#103669;margin:10px 0 12px;}
.tdv-subhead {font-size:.84rem;color:#56718c;margin-bottom:9px;}
.tdv-workflow-card {min-height:181px;border:1px solid #d9e8fa;border-radius:17px;
 padding:16px 15px 8px;background:#eff6ff;box-shadow:0 3px 11px #2469a70b;}
.tdv-workflow-card.stage2{background:#effcf5;border-color:#d5eedf;}
.tdv-workflow-card.stage3{background:#fff8ed;border-color:#f5e3c6;}
.tdv-workflow-card.stage4{background:#f6f2ff;border-color:#e5d8fc;}
.tdv-workflow-top {display:flex;gap:11px;align-items:center;margin-bottom:8px;}
.tdv-workflow-number {width:39px;height:39px;min-width:39px;display:grid;place-items:center;
 border-radius:50%;background:#277eea;color:#fff;font-size:1.25rem;font-weight:850;}
.stage2 .tdv-workflow-number{background:#1ca968;}
.stage3 .tdv-workflow-number{background:#ec971f;}
.stage4 .tdv-workflow-number{background:#8459e7;}
.tdv-workflow-icon{font-size:2.5rem;line-height:1;}
.tdv-workflow-card h3{font-size:1rem;font-weight:850;color:#153867;margin:8px 0 7px;}
.tdv-workflow-card p{font-size:.85rem;min-height:62px;line-height:1.42;color:#57718d;margin:0;}
.st-key-tdv_action_1 button,.st-key-tdv_action_2 button,.st-key-tdv_action_3 button,
.st-key-tdv_action_4 button {width:100%!important;border-radius:10px!important;
 color:white!important;font-weight:750!important;min-height:42px!important;border:0!important;}
.st-key-tdv_action_1 button{background:#2a7de6!important;}
.st-key-tdv_action_2 button{background:#18a46b!important;}
.st-key-tdv_action_3 button{background:#e99320!important;}
.st-key-tdv_action_4 button{background:#7c56df!important;}
.tdv-dashboard-card{background:#fff;border:1px solid #dce8f5;border-radius:16px;
 padding:17px 15px;min-height:114px;}
.tdv-dashboard-card .name{font-size:.8rem;font-weight:730;color:#375779;margin:8px 0 6px;}
.tdv-dashboard-card .num{font-size:1.65rem;font-weight:850;color:#8ca3b9;}
.tdv-dashboard-card .ico{font-size:1.5rem;line-height:1.2;}
.tdv-bottom-panel{background:#fff;border:1px solid #dae6f2;border-radius:15px;
 padding:17px 18px;min-height:150px;}
.tdv-bottom-panel h4{color:#163e71;font-size:1.02rem;font-weight:820;margin:0 0 11px;}
.tdv-bottom-panel p{font-size:.86rem;color:#557390;line-height:1.55;}
.tdv-bottom-panel table{width:100%;border-collapse:collapse;font-size:.82rem;}
.tdv-bottom-panel th{background:#eff6ff;color:#3b5b7f;text-align:left;padding:8px;}
.tdv-bottom-panel td{border-bottom:1px solid #e7eef7;padding:10px 8px;color:#5e7890;}
.tdv-summary-note{background:#edf6ff;border:1px solid #d4e7f9;border-radius:12px;
 padding:13px 16px;color:#315c8b;font-size:.88rem;}
.tdv-approval{background:#f0faf6;border:1px solid #d1e9dc;border-radius:12px;
 padding:15px 16px;font-size:.85rem;color:#24654d;}
.tdv-pending{background:#fff8eb;border:1px solid #f0ddb4;border-radius:12px;
 padding:15px 16px;font-size:.85rem;color:#775b23;}
.st-key-tdv_main_scroll [data-testid="stVerticalBlock"] {gap:.65rem;}
@media (max-width:1220px){
 .tdv-main-logo{width:138px!important;min-width:138px!important;padding-right:8px!important;}
 .tdv-main-logo img{width:125px!important;}
 .tdv-main-title{font-size:1.42rem!important;}
 .tdv-main-body{width:auto;}
}
@media (max-width:899px), (max-height:569px) {
 .tdv-main-hero{min-height:104px!important;padding:10px!important;gap:10px!important;}
 .tdv-main-logo{width:72px!important;min-width:72px!important;min-height:70px!important;}
 .tdv-main-logo img{width:66px!important;}
 .tdv-main-title{font-size:1.04rem!important;}
 .tdv-main-art,.tdv-main-hero .tdv-tags{display:none!important;}
 .tdv-workflow-card{min-height:150px;}
}


/* Approved mockups: compact toolbar and navigation highlight. */
.tdv-globalbar{display:flex;align-items:center;justify-content:space-between;
 min-height:44px;padding:5px 16px;margin-bottom:8px;border:1px solid #e1eaf5;
 border-radius:12px;background:#fff;}
.tdv-globalbar-search{width:min(58%,480px);border-radius:11px;background:#f0f5fc;
 color:#6b849d;padding:8px 13px;font-size:.83rem;}
.tdv-globalbar-status{border-radius:10px;background:#eaf8f1;color:#227653;
 font-size:.78rem;font-weight:800;padding:7px 12px;}
.st-key-tdv_sidebar_scroll [data-testid="stRadio"] [role="radiogroup"] > label{
 padding:9px 11px!important;margin:0 0 3px!important;border-radius:11px!important;
 border:1px solid transparent!important;cursor:pointer;}
.st-key-tdv_sidebar_scroll [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked){
 background:#d7e9ff!important;border-color:#c2dcff!important;color:#075fc3!important;
 font-weight:750!important;}
.tdv-demo-project{background:#fff;border:1px solid #dae8f8;border-radius:15px;
 padding:19px 20px;min-height:138px;margin-bottom:7px;}
.tdv-demo-project .title{color:#163e77;font-size:1.16rem;font-weight:850;margin-bottom:8px;}
.tdv-demo-project .desc{font-size:.86rem;color:#5c7791;line-height:1.5;}
.tdv-demo-security{background:#f0faf5;border:1px solid #d4ece0;padding:16px;
 border-radius:15px;margin-bottom:7px;font-size:.85rem;color:#216d4e;}
.tdv-demo-warning{background:#fff9ea;border:1px solid #f2e2be;padding:16px;
 border-radius:15px;font-size:.85rem;color:#906d2b;}
@media(max-width:899px){
 .tdv-globalbar{min-height:32px;padding:3px 6px;}
 .tdv-globalbar-search{display:none;}
 .tdv-globalbar-status{font-size:.7rem;}
}

/* Banner thống nhất theo yêu cầu Vỹ: nền một khối, không có hai đường phân cách. */
.tdv-main-hero{
 background:linear-gradient(102deg,#e9f7ff 0%,#e3f5ff 25%,#ecf9ff 57%,#bfe9fa 85%,#75c9ed 100%)!important;
 box-shadow:0 5px 17px rgba(26,85,145,.10)!important;
 border:1px solid #c7e4f9!important;
 isolation:isolate;
}
.tdv-main-hero::after{
 content:"";position:absolute;inset:0;z-index:0;pointer-events:none;
 background:
  radial-gradient(circle at 21% 80%,rgba(83,194,242,.19),transparent 26%),
  radial-gradient(circle at 65% 15%,rgba(255,255,255,.71),transparent 39%),
  linear-gradient(0deg,rgba(33,159,223,.12),transparent 40%);
}
.tdv-main-logo{
 border-right:0!important;
 background:transparent!important;
}
.tdv-main-logo,.tdv-main-body{
 position:relative;z-index:3;
}
.tdv-main-art{
 width:24.5%!important;
 left:auto;right:0;top:0;bottom:0;
 z-index:1;opacity:1!important;
 border:0!important;
 background-repeat:no-repeat!important;
 background-position:center right!important;
 background-size:cover!important;
 /* Chuyển tiếp nhẹ trên chính một nền banner, không có đường thẳng ngăn cách. */
 -webkit-mask-image:linear-gradient(to right,transparent 0%,rgba(0,0,0,.45) 12%,#000 33%);
 mask-image:linear-gradient(to right,transparent 0%,rgba(0,0,0,.45) 12%,#000 33%);
}
.tdv-main-art::before{display:none!important;}
.tdv-main-title{color:#0a336e!important;text-shadow:0 1px 0 rgba(255,255,255,.65);}
.tdv-main-subtitle{color:#456b8e!important;}
@media(max-width:1220px){
 .tdv-main-art{width:22%!important;opacity:.8!important;}
}
@media(max-width:899px){
 .tdv-main-art{display:none!important;}
}

/* 20/10: Bright transparent logo, subtle medical focus in left whitespace,
   and wider clinical illustration reaching the end of the main headline. */
.tdv-main-hero{
 background:linear-gradient(104deg,#e6f4ff 0%,#d9effc 22%,#e9f6fe 46%,#d7effb 75%,#93d9f1 100%)!important;
}
.tdv-main-hero::after{
 background:
   radial-gradient(ellipse at 18% 82%,rgba(43,173,225,.19),transparent 30%),
   radial-gradient(ellipse at 33% 20%,rgba(255,255,255,.86),transparent 35%),
   radial-gradient(ellipse at 72% 12%,rgba(255,255,255,.54),transparent 32%),
   linear-gradient(to top,rgba(37,150,215,.08),transparent 38%)!important;
}
.tdv-main-logo{
 background:none!important;
 overflow:visible!important;
 isolation:isolate;
}
.tdv-main-logo img,.tdv-left-brand img{
 background:transparent!important;
 border:0!important;
 box-shadow:none!important;
 filter:drop-shadow(0 2px 2px rgba(11,66,101,.12));
}
.tdv-main-logo::before{
 content:"";
 position:absolute;
 width:102px;height:102px;
 right:-142px;top:30%;
 border-radius:34px;
 border:2px solid rgba(47,153,212,.17);
 transform:rotate(26deg);
 background:linear-gradient(140deg,rgba(255,255,255,.22),rgba(95,189,232,.075));
 box-shadow:0 0 0 14px rgba(255,255,255,.06);
 pointer-events:none;
}
.tdv-main-logo::after{
 content:"+";
 position:absolute;
 width:100px;height:100px;display:flex;
 align-items:center;justify-content:center;
 right:-140px;top:30%;
 color:rgba(30,143,207,.19);
 font-size:5.3rem;font-weight:850;line-height:1;
 pointer-events:none;
}
.tdv-main-art{
 width:42%!important;
 background-position:center right!important;
 background-size:cover!important;
 opacity:1!important;
 -webkit-mask-image:linear-gradient(to right,transparent 0%,rgba(0,0,0,.16) 12%,rgba(0,0,0,.66) 34%,#000 55%)!important;
 mask-image:linear-gradient(to right,transparent 0%,rgba(0,0,0,.16) 12%,rgba(0,0,0,.66) 34%,#000 55%)!important;
}
.tdv-main-body{position:relative;z-index:3;}
.tdv-main-title{color:#0b3575!important;}
@media(max-width:1400px) and (min-width:900px){
 .tdv-main-art{width:37%!important;}
 .tdv-main-logo::before,.tdv-main-logo::after{
   transform:scale(.74);
   right:-103px;
 }
}
@media(max-width:899px){
 .tdv-main-logo::before,.tdv-main-logo::after{display:none!important;}
 .tdv-main-art{display:none!important;}
}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

PAGES = [
    "🏠 Trang chủ / Dự án",
    "📄 E-HSMT",
    "💊 Báo giá & hồ sơ NSX",
    "🔬 TDV-IDP 3.0 · Đọc đa tầng",
    "🛡️ Chứng cứ nhà sản xuất",
    "⚖️ So sánh kỹ thuật",
    "📊 Báo cáo lãnh đạo",
    "🔗 Google Sheets",
    "☁️ Tình trạng Online",
]

if "tdv_section" not in st.session_state:
    st.session_state.tdv_section = PAGES[0]

logo = (f'<img alt="Logo DUBIPHARMA" style="width:110px;max-height:92px;object-fit:contain" '
        f'src="data:image/{LOGO_MIME};base64,{LOGO_DISPLAY_DATA}">' if LOGO_DISPLAY_DATA else
        '<div class="tdv-logo-word" aria-label="Logo DUBI">DB<br>DUBI</div>')
art = (f'<div class="tdv-main-art" style="opacity:.77;'
       f'background-image:linear-gradient(to right,#eaf4fd00,#d9ecfa18),'
       f'url(data:image/webp;base64,{ART_DATA});'
       f'background-size:cover;background-position:center"></div>' if ART_DATA else
       '<div class="tdv-main-art" aria-hidden="true"></div>')

with st.sidebar:
    with st.container(key="tdv_sidebar_brand"):
        st.markdown(
            '<div class="tdv-left-head"><div class="tdv-left-brand">' + logo +
            '</div><div class="tdv-sidebar-name">DUBIPHARMA DŨNG BÍCH</div>'
            '<div class="tdv-sidebar-sub">TDV QC7 ONLINE · IDP 3.0</div></div>',
            unsafe_allow_html=True,
        )
    with st.container(key="tdv_sidebar_scroll"):
        st.markdown('<div class="tdv-heading-section">ĐIỀU HÀNH & NGHIỆP VỤ</div>',
                    unsafe_allow_html=True)
        page = st.radio(
            "Chọn chức năng",
            PAGES, key="tdv_sidebar_nav", label_visibility="collapsed"
        )
        st.markdown('<div class="tdv-left-note">🔒 BẢN XEM TRƯỚC RIÊNG TƯ.'
                    ' Chưa nhập hồ sơ NSX, GMP, báo giá hoặc thông tin mật.</div>',
                    unsafe_allow_html=True)
        st.divider()
        st.caption("Ứng dụng: Streamlit Preview")
        st.caption("Dữ liệu nghiệp vụ: CHƯA KẾT NỐI")
        st.caption("Tài khoản nội bộ: CHƯA TÍCH HỢP")
        st.caption("Báo cáo: chỉ để xem cấu trúc giao diện")

with st.container(key="tdv_main_fixed"):
    st.markdown('<div class="tdv-globalbar"><div class="tdv-globalbar-search">🔎 Tìm kiếm dự án, gói thầu, thuốc… (đang tích hợp)</div><div class="tdv-globalbar-status">🔒 TDV QC7 · PRIVATE PREVIEW</div></div>', unsafe_allow_html=True)
    st.markdown(
        '<section class="tdv-main-hero">' + art +
        '<div class="tdv-main-logo">' + logo + '</div>'
        '<div class="tdv-main-body">'
        '<div style="text-align:center">'
        '<span class="tdv-pill">HỆ THỐNG QUẢN LÝ ĐẤU THẦU CHUYÊN NGHIỆP</span></div>'
        '<div class="tdv-main-title">TRUNG TÂM ĐIỀU HÀNH ĐẤU THẦU'
        '<br>DUBIPHARMA DŨNG BÍCH</div>'
        '<div class="tdv-main-subtitle">Quản lý tập trung · Minh bạch · Hiệu quả · Vì sức khỏe cộng đồng</div>'
        '<div class="tdv-tags"><span>🎯 Chủ động kế hoạch</span>'
        '<span>📊 Tối ưu hiệu quả</span><span>🛡️ Minh bạch & tuân thủ</span></div>'
        '</div></section>', unsafe_allow_html=True,
    )

def panel(title: str, description: str) -> None:
    st.markdown('<div class="tdv-panel"><h3>'+title+'</h3><p>'+description+'</p></div>',
                unsafe_allow_html=True)

def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).strip().casefold())

def exact_simple_dose(text: str):
    match = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*(mg|g|mcg|µg)\s*", text, re.I)
    if not match:
        return None
    try:
        value = Decimal(match.group(1).replace(",", "."))
        mul = {"mg":Decimal("1"),"g":Decimal("1000"),
               "mcg":Decimal("0.001"),"µg":Decimal("0.001")}[match.group(2).lower()]
        return value*mul if value>0 else None
    except (InvalidOperation, ValueError):
        return None

def tdv_open_section(destination: str) -> None:
    """Streamlit callback runs before widgets are recreated on navigation."""
    st.session_state["tdv_sidebar_nav"] = destination

with st.container(key="tdv_main_scroll"):
    st.markdown('<div class="tdv-notice">🛡️ <b>TDV QC7 ONLINE — BẢN DEMO ĐANG NGHIỆM THU.</b>'
                ' Chưa có xác thực nghiệp vụ, kho dữ liệu dùng chung hoặc đồng bộ Google Sheets.'
                ' Tuyệt đối không tải hồ sơ đấu thầu, GMP hay báo giá thật vào bản này.</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="tdv-crumb">🏠 TDV QC7 &nbsp;›&nbsp; {page}</div>',
                unsafe_allow_html=True)
    if page == PAGES[0]:
        st.markdown('<div class="tdv-section-label">🏛️ Trang chủ · Quy trình điều hành dự án</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="tdv-subhead">Bốn bước nghiệp vụ của TDV QC7 — từ tiếp nhận hồ sơ đến báo cáo lãnh đạo.</div>',
                    unsafe_allow_html=True)
        stages = [
            ("stage1", "1", "📁", "Tiếp nhận E-HSMT",
             "Nhận hồ sơ mời thầu; phân tích danh mục, kiểm chứng mã thuốc, hàm lượng, số lượng và giá.",
             "Mở E-HSMT", PAGES[1]),
            ("stage2", "2", "🏭", "Hồ sơ nhà sản xuất",
             "Tiếp nhận thuốc, GMP, giấy ủy quyền, báo giá và liên kết chứng cứ đúng nhà máy.",
             "Hồ sơ NSX", PAGES[2]),
            ("stage3", "3", "🔬", "Đọc – lọc – đối chiếu",
             "IDP 3.0 kiểm tra dữ liệu nhiều tầng; chỉ các kết quả đủ căn cứ mới được đề xuất.",
             "Kiểm chứng", PAGES[3]),
            ("stage4", "4", "📊", "Báo cáo lãnh đạo",
             "Tổng hợp đáp ứng, pháp lý, giá và trạng thái xác minh; phê duyệt theo thẩm quyền.",
             "Báo cáo", PAGES[6]),
        ]
        cols = st.columns(4, gap="small")
        for i, (cl, number, emoji, heading, description, button_text, destination) in enumerate(stages):
            with cols[i]:
                st.markdown(
                    '<div class="tdv-workflow-card '+cl+'"><div class="tdv-workflow-top">'
                    '<span class="tdv-workflow-number">'+number+'</span>'
                    '<span class="tdv-workflow-icon">'+emoji+'</span></div>'
                    '<h3>'+heading+'</h3><p>'+description+'</p></div>',
                    unsafe_allow_html=True,
                )
                with st.container(key=f"tdv_action_{i+1}"):
                    st.button(
                        button_text+" →", key=f"tdv_go_{i}", use_container_width=True,
                        on_click=tdv_open_section, args=(destination,)
                    )
        project_left, project_right = st.columns([1.45,1], gap="small")
        with project_left:
            st.markdown(
                '<div class="tdv-demo-project"><div class="title">📦 Chưa kết nối dữ liệu dự án</div>'
                '<div class="desc">Bản trình diễn Online hiện chưa có kho hồ sơ nghiệp vụ. '
                'Giao diện sẽ hướng dẫn tiếp nhận E-HSMT để mở dự án sau khi xác thực '
                'và lưu trữ bền vững được nghiệm thu.</div></div>',
                unsafe_allow_html=True,
            )
        with project_right:
            st.markdown(
                '<div class="tdv-demo-security"><b>🛡️ Chế độ QC7 Online đang kiểm thử</b>'
                '<div>Không ghi Google Sheets, không tự duyệt GMP hoặc giá dự thầu.</div></div>'
                '<div class="tdv-demo-warning"><b>🔐 Lưu ý bảo mật</b>'
                '<div>Chưa đưa hồ sơ thật vào bản Preview.</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="tdv-section-label">📊 Tổng quan điều hành & thống kê lãnh đạo</div>',
                    unsafe_allow_html=True)
        st.caption("Các ô đang hiển thị dấu — vì chưa có kết nối dữ liệu đã xác minh. Không dùng số liệu giả để trình lãnh đạo.")
        for col, ico, label in zip(
            st.columns(4, gap="small"),
            ["📄", "💊", "🛡️", "✅"],
            ["Mã E-HSMT đã xác minh", "Sản phẩm NSX có chứng cứ",
             "GMP đã kiểm tra", "Ứng viên được phê duyệt"]
        ):
            with col:
                st.markdown(
                    '<div class="tdv-dashboard-card"><div class="ico">'+ico+'</div>'
                    '<div class="name">'+label+'</div><div class="num">—</div></div>',
                    unsafe_allow_html=True,
                )
        left, right = st.columns([1.1, 1], gap="medium")
        with left:
            st.markdown(
                '<div class="tdv-bottom-panel"><h4>📋 Danh sách dự án và gói thầu</h4>'
                '<table><tr><th>Dự án</th><th>Trạng thái</th><th>Ghi chú</th></tr>'
                '<tr><td>Chưa kết nối</td><td>Chờ xác minh</td>'
                '<td>Không đọc trực tiếp dữ liệu mật từ bản Preview</td></tr></table>'
                '<p>Các dự án đã lưu sẽ hiển thị sau khi phân quyền,'
                ' lưu trữ tập trung và đồng bộ được nghiệm thu.</p></div>',
                unsafe_allow_html=True,
            )
        with right:
            st.markdown(
                '<div class="tdv-bottom-panel"><h4>📣 Thông báo điều hành</h4>'
                '<p>🔒 Ứng dụng Online đang ở giai đoạn thử nghiệm giao diện.</p>'
                '<p>🔍 Dữ liệu E-HSMT và GMP cần được xác minh từ chứng cứ nguồn.</p>'
                '<p>✍️ Giá dự thầu và kết luận tham gia thầu chỉ được sử dụng sau phê duyệt.</p>'
                '</div>', unsafe_allow_html=True,
            )
        a,b = st.columns(2)
        with a:
            st.markdown('<div class="tdv-approval"><strong>🛡️ Kiểm soát chất lượng</strong>'
                        '<div>Kiểm chứng từng trường dữ liệu, có nguồn và lịch sử trước khi đưa vào nghiệp vụ.</div>'
                        '</div>', unsafe_allow_html=True)
        with b:
            st.markdown('<div class="tdv-pending"><strong>⏳ Trạng thái triển khai</strong>'
                        '<div>Giao diện Online: Preview · Chưa có cơ sở dữ liệu và tài khoản nội bộ.</div>'
                        '</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="tdv-summary-note">📁 <b>Dự án DEMO độc lập:</b> dự kiến '
            'cho phép kiểm thử riêng với dữ liệu giả lập sau khi thiết lập kho an toàn.'
            ' Hiện chưa tạo hoặc ghi dữ liệu DEMO vào Google Sheets.</div>',
            unsafe_allow_html=True,
        )
    elif page == PAGES[3]:
        st.markdown('<div class="tdv-page-title">🔬 TDV-IDP 3.0 · Kiểm chứng dữ liệu</div>',
                    unsafe_allow_html=True)
        st.info("Chế độ trình diễn một quy tắc nhỏ; không phải bộ đọc PDF/OCR hoàn chỉnh.")
        left,right=st.columns(2)
        with left:
            a=st.text_input("Hoạt chất E-HSMT (dữ liệu mẫu)",value="Acenocoumarol")
            x=st.text_input("Hàm lượng E-HSMT",value="1 mg")
        with right:
            b=st.text_input("Hoạt chất NSX (dữ liệu mẫu)",value="Acenocoumarol")
            y=st.text_input("Hàm lượng NSX",value="4 mg")
        if st.button("Kiểm tra mẫu",type="primary"):
            dx,dy=exact_simple_dose(x),exact_simple_dose(y)
            if not a.strip() or not b.strip() or dx is None or dy is None:
                st.warning("Không đủ dữ liệu/đơn vị chưa hỗ trợ — cần xác minh.")
            elif normalized(a)==normalized(b) and dx==dy:
                st.success("Hai trường mẫu khớp; chưa đủ để kết luận đáp ứng E-HSMT.")
            else:
                st.error("Sai khác hoạt chất hoặc hàm lượng — không tự ghép ứng viên.")
        st.caption("Chưa xử lý tên muối, phối hợp hoạt chất, dạng bào chế, đường dùng và pháp lý GMP.")
    elif page == PAGES[-1]:
        st.markdown('<div class="tdv-page-title">☁️ Tiến độ Online</div>',unsafe_allow_html=True)
        st.table([
            {"Hạng mục":"Giao diện / menu","Trạng thái":"Preview có giao diện"},
            {"Hạng mục":"Quyền xem Streamlit","Trạng thái":"Thiết lập riêng tư; cần duy trì kiểm tra"},
            {"Hạng mục":"GitHub","Trạng thái":"Nhánh thử nghiệm, không chứa dữ liệu mật"},
            {"Hạng mục":"Đăng nhập và phân quyền nghiệp vụ","Trạng thái":"CHƯA TÍCH HỢP"},
            {"Hạng mục":"Google Sheets","Trạng thái":"CHƯA KẾT NỐI / KHÔNG GHI"},
            {"Hạng mục":"Dữ liệu và kho chứng cứ","Trạng thái":"CHƯA KẾT NỐI"},
            {"Hạng mục":"Bộ đọc đa tầng IDP 3.0","Trạng thái":"CHƯA TÍCH HỢP BẢN CLOUD"},
        ])
        st.warning("Không cho phép vận hành hồ sơ thật khi chưa hoàn thành dữ liệu, xác thực và kiểm thử an toàn.")
    else:
        st.markdown('<div class="tdv-page-title">'+page+'</div>',unsafe_allow_html=True)
        st.markdown('<div class="tdv-empty"><b>Phân hệ đang tích hợp trên TDV QC7 Online.</b>'
                    '<br>Không nhập hoặc hiển thị dữ liệu nhà sản xuất, E-HSMT hoặc giá dự thầu thật ở bản này.'
                    '</div>',unsafe_allow_html=True)
        for name, desc in [
            ("📁 Tiếp nhận và lưu hồ sơ gốc", "Dự kiến: phát hiện file trùng, ghi dấu SHA-256, lịch sử."),
            ("🔎 Đọc – kiểm chứng – chuẩn hóa", "Dự kiến: nhiều bộ đọc, chứng cứ trang/ô, cảnh báo."),
            ("✅ Xét duyệt và báo cáo", "Dự kiến: quy trình người duyệt, phiên bản và nhật ký.")]:
            panel(name, desc)
    st.divider()
    st.caption("© DUBIPHARMA DŨNG BÍCH · TDV QC7 / IDP 3.0 · Bản xem trước bảo mật")
