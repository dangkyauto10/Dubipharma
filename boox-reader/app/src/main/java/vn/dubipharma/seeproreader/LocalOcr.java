package vn.dubipharma.seeproreader;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.content.Context;
import com.google.android.gms.tasks.Tasks;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.Text;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;
import com.google.mlkit.vision.text.TextRecognizer;
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader;
import com.tom_roush.pdfbox.pdmodel.PDDocument;
import com.tom_roush.pdfbox.rendering.PDFRenderer;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

final class LocalOcr {
    private LocalOcr() {}
    static String fromBitmap(Bitmap bitmap) throws Exception {
        try (TextRecognizer recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)) {
            Text text = Tasks.await(recognizer.process(InputImage.fromBitmap(bitmap, 0)), 45, TimeUnit.SECONDS);
            return text.getText() == null ? "" : text.getText().trim();
        }
    }
    static Bitmap decodeImage(byte[] bytes) throws IOException {
        BitmapFactory.Options opt = new BitmapFactory.Options();
        opt.inJustDecodeBounds = true;
        BitmapFactory.decodeByteArray(bytes, 0, bytes.length, opt);
        if (opt.outWidth <= 0 || opt.outHeight <= 0) throw new IOException("Không mở được ảnh.");
        int sample = 1;
        while ((long) (opt.outWidth / sample) * (opt.outHeight / sample) > 4000000) sample *= 2;
        opt.inJustDecodeBounds = false;
        opt.inSampleSize = sample;
        Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length, opt);
        if (bitmap == null) throw new IOException("Không giải mã được ảnh.");
        return bitmap;
    }
    static DocumentExtractor.Result fromImage(byte[] bytes) throws Exception {
        Bitmap image = decodeImage(bytes);
        try {
            DocumentExtractor.Result r = new DocumentExtractor.Result();
            r.pages = 1;
            r.content = fromBitmap(image);
            r.warning = "Văn bản nhận dạng từ ảnh là kết quả OCR chưa xác minh. Cần so với ảnh gốc.";
            if (r.content.isEmpty()) r.warning += " Chưa nhận dạng được chữ.";
            return r;
        } finally { image.recycle(); }
    }

    static void fillBlankPdfPages(Context context, byte[] bytes,
                                  DocumentExtractor.Result result) throws Exception {
        if (result.blankPdfPages.isEmpty()) return;
        PDFBoxResourceLoader.init(context.getApplicationContext());
        StringBuilder additional = new StringBuilder(result.content);
        int count = 0;
        try (PDDocument doc = PDDocument.load(bytes)) {
            PDFRenderer renderer = new PDFRenderer(doc);
            for (int page : result.blankPdfPages) {
                if (++count > 20 || additional.length() > DocumentExtractor.MAX_TEXT) {
                    result.warning += " Chỉ OCR tối đa 20 trang không có lớp chữ trong một lần đọc.";
                    break;
                }
                Bitmap bitmap = renderer.renderImageWithDPI(page - 1, 140);
                try {
                    String extracted = fromBitmap(bitmap);
                    if (extracted.isEmpty()) result.warning += " Trang " + page + ": OCR không tìm được chữ.";
                    else additional.append("\nTrang ").append(page).append(" (OCR):\n").append(extracted).append("\n");
                } finally { bitmap.recycle(); }
            }
        }
        if (additional.length() > DocumentExtractor.MAX_TEXT) {
            result.content = additional.substring(0, DocumentExtractor.MAX_TEXT);
            result.warning += " Nội dung quá dài đã bị giới hạn.";
        } else result.content = additional.toString();
        result.warning += " OCR từ PDF quét chưa xác minh.";
    }
}
