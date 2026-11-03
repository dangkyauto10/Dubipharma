package vn.dubipharma.seeproreader;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.graphics.Bitmap;
import android.graphics.Typeface;
import android.view.View;
import android.view.Gravity;
import android.widget.*;
import java.io.*;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final int FILE_REQUEST = 3301;
    private static final int MAX_FILE_SIZE = DocumentExtractor.MAX_BYTES;
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private SpeechPlayer speech;
    private TextView status;
    private TextView content;
    private ImageView preview;
    private Button open;
    private String currentText = "";
    private int currentJob = 0;
    private boolean processing = false;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        buildUi();
        speech = new SpeechPlayer(this, new SpeechPlayer.Listener() {
            @Override public void status(String message) { runOnUiThread(() -> status.setText(message)); }
            @Override public void finished() { runOnUiThread(() -> status.setText("Đã đọc hết tài liệu.")); }
        });
    }

    private int dp(float n) { return (int) (n * getResources().getDisplayMetrics().density + 0.5f); }

    private Button button(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextSize(17);
        b.setAllCaps(false);
        b.setMinHeight(dp(54));
        return b;
    }

    private void buildUi() {
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(14), dp(12), dp(14), dp(14));
        body.setBackgroundColor(0xfffafafa);

        TextView heading = new TextView(this);
        heading.setText("SEE PRO READER  •  BOOX");
        heading.setTextSize(23);
        heading.setTypeface(null, Typeface.BOLD);
        heading.setTextColor(0xff202020);
        body.addView(heading);

        TextView sub = new TextView(this);
        sub.setText("Word · Excel · PDF · Ảnh chụp · Đọc tiếng Việt");
        sub.setTextColor(0xff555555);
        sub.setTextSize(15);
        body.addView(sub);

        open = button("MỞ TÀI LIỆU TỪ BOOX");
        body.addView(open);
        open.setOnClickListener(v -> chooseFile());

        LinearLayout r1 = new LinearLayout(this);
        r1.setOrientation(LinearLayout.HORIZONTAL);
        Button play = button("▶ ĐỌC");
        Button pause = button("Ⅱ TẠM DỪNG");
        r1.addView(play, new LinearLayout.LayoutParams(0, dp(57), 1));
        r1.addView(pause, new LinearLayout.LayoutParams(0, dp(57), 1));
        body.addView(r1);

        LinearLayout r2 = new LinearLayout(this);
        r2.setOrientation(LinearLayout.HORIZONTAL);
        Button resume = button("↻ TIẾP TỤC");
        Button stop = button("■ DỪNG");
        r2.addView(resume, new LinearLayout.LayoutParams(0, dp(57), 1));
        r2.addView(stop, new LinearLayout.LayoutParams(0, dp(57), 1));
        body.addView(r2);

        LinearLayout r3 = new LinearLayout(this);
        r3.setGravity(Gravity.CENTER_VERTICAL);
        Button slower = button("− CHẬM");
        TextView speed = new TextView(this);
        speed.setGravity(Gravity.CENTER);
        speed.setTextSize(17);
        speed.setText("1.0×");
        Button faster = button("+ NHANH");
        r3.addView(slower, new LinearLayout.LayoutParams(0, dp(52), 1));
        r3.addView(speed, new LinearLayout.LayoutParams(0, dp(52), 1));
        r3.addView(faster, new LinearLayout.LayoutParams(0, dp(52), 1));
        body.addView(r3);

        status = new TextView(this);
        status.setText("Chọn tài liệu trên BOOX để bắt đầu.");
        status.setTextColor(0xff333333);
        status.setTextSize(16);
        status.setPadding(0, dp(8), 0, dp(10));
        body.addView(status);

        ScrollView scroll = new ScrollView(this);
        LinearLayout doc = new LinearLayout(this);
        doc.setOrientation(LinearLayout.VERTICAL);
        preview = new ImageView(this);
        preview.setAdjustViewBounds(true);
        preview.setMaxHeight(dp(470));
        preview.setScaleType(ImageView.ScaleType.FIT_CENTER);
        preview.setVisibility(View.GONE);
        doc.addView(preview);
        content = new TextView(this);
        content.setTextSize(19);
        content.setTextColor(0xff111111);
        content.setTextIsSelectable(true);
        content.setLineSpacing(dp(5), 1.05f);
        content.setPadding(dp(5), dp(8), dp(5), dp(28));
        content.setText("Mở tệp .docx, .xlsx, .pdf hoặc ảnh JPG/PNG. Ứng dụng đọc trực tiếp trên thiết bị, không tải lên máy chủ.");
        doc.addView(content);
        scroll.addView(doc);
        body.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(body);

        play.setOnClickListener(v -> speech.play(currentText));
        pause.setOnClickListener(v -> speech.pause());
        resume.setOnClickListener(v -> speech.resume());
        stop.setOnClickListener(v -> { speech.stop(); status.setText("Đã dừng."); });
        slower.setOnClickListener(v -> { speech.setRate(speech.getRate() - 0.1f); speed.setText(String.format(Locale.US,"%.1f×", speech.getRate())); });
        faster.setOnClickListener(v -> { speech.setRate(speech.getRate() + 0.1f); speed.setText(String.format(Locale.US,"%.1f×", speech.getRate())); });
    }

    private void chooseFile() {
        if (processing) return;
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[] {
            "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/jpeg", "image/png", "image/webp", "text/plain"
        });
        startActivityForResult(intent, FILE_REQUEST);
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == FILE_REQUEST && result == RESULT_OK && data != null && data.getData() != null) {
            loadFile(data.getData());
        }
    }

    private String nameOf(Uri uri) {
        try (Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int column = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (column >= 0 && !cursor.isNull(column)) return cursor.getString(column);
            }
        } catch (Exception ignored) {}
        String last = uri.getLastPathSegment();
        return last != null ? last : "document";
    }

    private void loadFile(Uri uri) {
        speech.stop();
        final int job = ++currentJob;
        processing = true;
        open.setEnabled(false);
        currentText = "";
        content.setText("Đang đọc nội dung tài liệu...");
        preview.setImageDrawable(null);
        preview.setVisibility(View.GONE);
        status.setText("Đang nhận dạng nội dung trên BOOX...");
        worker.execute(() -> {
            String name = nameOf(uri);
            Bitmap image = null;
            try {
                byte[] bytes;
                try (InputStream input = getContentResolver().openInputStream(uri)) {
                    if (input == null) throw new IOException("Không mở được file.");
                    ByteArrayOutputStream output = new ByteArrayOutputStream();
                    byte[] buffer = new byte[8192];
                    int n;
                    while ((n = input.read(buffer)) != -1) {
                        if (output.size() + n > MAX_FILE_SIZE) throw new IOException("File quá 30 MB.");
                        output.write(buffer, 0, n);
                    }
                    bytes = output.toByteArray();
                }
                String lower = name.toLowerCase(Locale.ROOT);
                DocumentExtractor.Result r;
                if (lower.endsWith(".jpg") || lower.endsWith(".jpeg") ||
                    lower.endsWith(".png") || lower.endsWith(".webp")) {
                    r = LocalOcr.fromImage(bytes);
                    image = LocalOcr.decodeImage(bytes);
                } else {
                    r = DocumentExtractor.parse(getApplicationContext(), name, bytes);
                    if (lower.endsWith(".pdf") && !r.blankPdfPages.isEmpty()) {
                        LocalOcr.fillBlankPdfPages(getApplicationContext(), bytes, r);
                    }
                }
                final Bitmap bitmap = image;
                final String text = r.content;
                final String warn = r.warning;
                runOnUiThread(() -> {
                    if (job != currentJob || isFinishing()) {
                        if (bitmap != null) bitmap.recycle();
                        return;
                    }
                    processing = false; open.setEnabled(true);
                    currentText = text == null ? "" : text;
                    content.setText(currentText.isEmpty() ? "Không nhận dạng được chữ. Hãy kiểm tra tài liệu hoặc ảnh gốc." : currentText);
                    if (bitmap != null) {
                        preview.setImageBitmap(bitmap);
                        preview.setVisibility(View.VISIBLE);
                    }
                    status.setText("Đã mở: " + name + "\n" +
                        (warn.isEmpty() ? "Sẵn sàng đọc thành tiếng." : "Lưu ý: " + warn));
                });
            } catch (Exception err) {
                if (image != null) image.recycle();
                String message = err.getMessage() == null ? err.toString() : err.getMessage();
                runOnUiThread(() -> {
                    if (job != currentJob || isFinishing()) return;
                    processing = false; open.setEnabled(true);
                    currentText = "";
                    content.setText("Không thể đọc tài liệu này.");
                    status.setText("Lỗi: " + message);
                });
            }
        });
    }

    @Override public void onDestroy() {
        currentJob++;
        if (speech != null) speech.shutdown();
        worker.shutdownNow();
        super.onDestroy();
    }
}
