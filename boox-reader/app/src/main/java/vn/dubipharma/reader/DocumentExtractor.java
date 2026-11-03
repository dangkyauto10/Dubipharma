package vn.dubipharma.seeproreader;

import android.content.Context;
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader;
import com.tom_roush.pdfbox.pdmodel.PDDocument;
import com.tom_roush.pdfbox.text.PDFTextStripper;
import org.xmlpull.v1.XmlPullParser;
import android.util.Xml;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Android adaptation of SEE PRO's read-only multi-format intake.
 * No content is uploaded to a server or written to Drive/Sheets.
 * Extracted content is unverified and must not be used for business approvals.
 */
final class DocumentExtractor {
    static final int MAX_BYTES = 30 * 1024 * 1024;
    static final int MAX_TEXT = 160_000;
    static final int MAX_PDF_PAGES = 120;
    static final int MAX_EXCEL_ROWS = 4_000;
    private static final int MAX_ZIP_XML = 14 * 1024 * 1024;

    static class Result {
        String content = "";
        String warning = "";
        int pages = 0;
        ArrayList<Integer> blankPdfPages = new ArrayList<>();
    }

    static Result parse(Context ctx, String filename, byte[] bytes) throws Exception {
        if (bytes.length == 0 || bytes.length > MAX_BYTES) {
            throw new IOException("Tệp rỗng hoặc lớn hơn 30 MB.");
        }
        String name = filename.toLowerCase(Locale.ROOT);
        if (name.endsWith(".docx")) return word(bytes);
        if (name.endsWith(".xlsx")) return excel(bytes);
        if (name.endsWith(".pdf")) return pdf(ctx, bytes);
        if (name.endsWith(".txt")) {
            Result r = new Result();
            r.content = limited(new String(bytes, StandardCharsets.UTF_8), r);
            return r;
        }
        throw new IOException("Chưa hỗ trợ định dạng này. Hãy dùng DOCX, XLSX, PDF, JPG hoặc PNG.");
    }

    static Result pdf(Context ctx, byte[] bytes) throws Exception {
        PDFBoxResourceLoader.init(ctx.getApplicationContext());
        Result r = new Result();
        StringBuilder out = new StringBuilder();
        try (PDDocument doc = PDDocument.load(bytes)) {
            if (doc.isEncrypted()) throw new IOException("PDF được bảo vệ bằng mật khẩu.");
            r.pages = doc.getNumberOfPages();
            PDFTextStripper stripper = new PDFTextStripper();
            stripper.setSortByPosition(true);
            int pages = Math.min(r.pages, MAX_PDF_PAGES);
            for (int i = 1; i <= pages; i++) {
                stripper.setStartPage(i);
                stripper.setEndPage(i);
                String txt;
                try { txt = stripper.getText(doc); }
                catch (Exception ex) { txt = ""; }
                if (txt == null || txt.trim().isEmpty()) {
                    r.blankPdfPages.add(i);
                    continue;
                }
                out.append("\nTrang ").append(i).append(":\n").append(txt.trim()).append("\n");
                if (out.length() > MAX_TEXT) break;
            }
            if (r.pages > MAX_PDF_PAGES) r.warning += "PDF quá 120 trang, chưa đọc toàn bộ. ";
        }
        r.content = limited(out.toString(), r);
        return r;
    }

    static Result word(byte[] bytes) throws Exception {
        Map<String, byte[]> parts = zipParts(bytes, false);
        byte[] xml = parts.get("word/document.xml");
        if (xml == null) throw new IOException("Không tìm thấy phần nội dung Word.");
        Result r = new Result();
        StringBuilder out = new StringBuilder();
        XmlPullParser p = parser(xml);
        int evt = p.getEventType();
        while (evt != XmlPullParser.END_DOCUMENT) {
            String tag = p.getName();
            if (evt == XmlPullParser.START_TAG && "t".equals(tag)) {
                out.append(p.nextText());
            } else if (evt == XmlPullParser.START_TAG && "tab".equals(tag)) {
                out.append(" ");
            } else if (evt == XmlPullParser.START_TAG && "br".equals(tag)) {
                out.append("\n");
            } else if (evt == XmlPullParser.END_TAG && "tc".equals(tag)) {
                out.append(" | ");
            } else if (evt == XmlPullParser.END_TAG && "p".equals(tag)) {
                out.append("\n");
            } else if (evt == XmlPullParser.END_TAG && "tr".equals(tag)) {
                out.append("\n");
            }
            if (out.length() >= MAX_TEXT) break;
            evt = p.next();
        }
        r.content = limited(out.toString(), r);
        r.warning += "Định dạng phức tạp, ô gộp, hình trong Word có thể chưa chuyển thành chữ. ";
        return r;
    }

    static Result excel(byte[] bytes) throws Exception {
        Map<String, byte[]> parts = zipParts(bytes, true);
        Result r = new Result();
        ArrayList<String> shared = parseShared(parts.get("xl/sharedStrings.xml"));
        ArrayList<String> sheets = new ArrayList<>();
        for (String key : parts.keySet()) {
            if (Pattern.matches("xl/worksheets/sheet[0-9]+\\.xml", key)) sheets.add(key);
        }
        sheets.sort(Comparator.comparingInt(DocumentExtractor::sheetNumber));
        if (sheets.isEmpty()) throw new IOException("Không tìm thấy trang tính Excel.");
        StringBuilder out = new StringBuilder();
        int sheetNo = 0, rows = 0;
        for (String sheet : sheets) {
            sheetNo++;
            out.append("\nTRANG TÍNH ").append(sheetNo).append("\n");
            XmlPullParser p = parser(parts.get(sheet));
            String cellRef = "", type = "", value = "";
            StringBuilder inline = new StringBuilder(), row = new StringBuilder();
            boolean inInline = false, cellActive = false;
            int rowNum = 0;
            int evt = p.getEventType();
            while (evt != XmlPullParser.END_DOCUMENT && rows < MAX_EXCEL_ROWS && out.length() < MAX_TEXT) {
                String tag = p.getName();
                if (evt == XmlPullParser.START_TAG) {
                    if ("row".equals(tag)) {
                        row.setLength(0);
                        rows++;
                        try { rowNum = Integer.parseInt(p.getAttributeValue(null, "r")); }
                        catch (Exception ignored) { rowNum = rows; }
                    } else if ("c".equals(tag)) {
                        cellActive = true;
                        cellRef = p.getAttributeValue(null, "r");
                        type = p.getAttributeValue(null, "t");
                        value = "";
                        inline.setLength(0);
                    } else if ("is".equals(tag)) {
                        inInline = true;
                    } else if (cellActive && "v".equals(tag)) {
                        value = p.nextText();
                    } else if (cellActive && inInline && "t".equals(tag)) {
                        inline.append(p.nextText());
                    }
                } else if (evt == XmlPullParser.END_TAG) {
                    if ("is".equals(tag)) {
                        inInline = false;
                    } else if ("c".equals(tag)) {
                        String cell = inline.length() > 0 ? inline.toString() : value;
                        if ("s".equals(type)) {
                            try {
                                int index = Integer.parseInt(value);
                                cell = index >= 0 && index < shared.size() ? shared.get(index) : "[Lỗi chuỗi Excel]";
                            } catch (NumberFormatException ignored) { cell = "[Lỗi chỉ số chuỗi Excel]"; }
                        }
                        if ("b".equals(type)) cell = "1".equals(cell) ? "Đúng" : "Sai";
                        if (cell != null && !cell.trim().isEmpty()) {
                            if (row.length() > 0) row.append(" | ");
                            row.append(cellRef == null ? "Ô" : cellRef).append(": ").append(cell.trim());
                        }
                        cellActive = false;
                    } else if ("row".equals(tag)) {
                        if (row.length() > 0) {
                            out.append("Dòng ").append(rowNum).append(": ").append(row).append("\n");
                        }
                    }
                }
                evt = p.next();
            }
            if (rows >= MAX_EXCEL_ROWS || out.length() >= MAX_TEXT) break;
        }
        r.content = limited(out.toString(), r);
        r.pages = sheetNo;
        if (rows >= MAX_EXCEL_ROWS) r.warning += "Excel vượt 4.000 dòng, chỉ đọc một phần. ";
        r.warning += "Số/ngày tháng dùng giá trị lưu trong ô; cần đối chiếu định dạng gốc. ";
        return r;
    }

    private static int sheetNumber(String s) {
        try {
            return Integer.parseInt(s.substring(s.lastIndexOf("sheet") + 5, s.lastIndexOf(".xml")));
        } catch (Exception e) { return 99999; }
    }

    private static ArrayList<String> parseShared(byte[] xml) throws Exception {
        ArrayList<String> list = new ArrayList<>();
        if (xml == null) return list;
        XmlPullParser p = parser(xml);
        StringBuilder item = new StringBuilder();
        int evt = p.getEventType();
        while (evt != XmlPullParser.END_DOCUMENT && list.size() < 80_000) {
            String tag = p.getName();
            if (evt == XmlPullParser.START_TAG && "si".equals(tag)) item.setLength(0);
            else if (evt == XmlPullParser.START_TAG && "t".equals(tag)) item.append(p.nextText());
            else if (evt == XmlPullParser.END_TAG && "si".equals(tag)) list.add(item.toString());
            evt = p.next();
        }
        return list;
    }

    private static XmlPullParser parser(byte[] data) throws Exception {
        String s = new String(data, StandardCharsets.UTF_8);
        if (s.contains("<!DOCTYPE") || s.contains("<!ENTITY")) {
            throw new IOException("Tệp XML có khai báo không được hỗ trợ.");
        }
        XmlPullParser p = Xml.newPullParser();
        p.setFeature(XmlPullParser.FEATURE_PROCESS_NAMESPACES, true);
        p.setInput(new StringReader(s));
        return p;
    }

    private static Map<String, byte[]> zipParts(byte[] raw, boolean excel) throws Exception {
        Map<String, byte[]> found = new HashMap<>();
        int total = 0;
        try (ZipInputStream zin = new ZipInputStream(new ByteArrayInputStream(raw))) {
            ZipEntry entry;
            while ((entry = zin.getNextEntry()) != null) {
                String n = entry.getName();
                boolean wanted = excel ?
                    ("xl/sharedStrings.xml".equals(n) || Pattern.matches("xl/worksheets/sheet[0-9]+\\.xml", n))
                    : "word/document.xml".equals(n);
                if (!wanted) { zin.closeEntry(); continue; }
                ByteArrayOutputStream b = new ByteArrayOutputStream();
                byte[] tmp = new byte[8192];
                int count, itemTotal = 0;
                while ((count = zin.read(tmp)) != -1) {
                    itemTotal += count; total += count;
                    if (itemTotal > MAX_ZIP_XML || total > 48 * 1024 * 1024) {
                        throw new IOException("Tệp có nội dung nén quá lớn.");
                    }
                    b.write(tmp, 0, count);
                }
                found.put(n, b.toByteArray());
                zin.closeEntry();
            }
        }
        return found;
    }

    private static String limited(String text, Result r) {
        if (text.length() > MAX_TEXT) {
            r.warning += "Văn bản dài, chỉ đọc 160.000 ký tự đầu. ";
            return text.substring(0, MAX_TEXT);
        }
        return text;
    }
}
