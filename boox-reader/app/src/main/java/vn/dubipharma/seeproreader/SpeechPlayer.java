package vn.dubipharma.seeproreader;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import java.util.ArrayList;
import java.util.Locale;

final class SpeechPlayer {
    interface Listener {
        void status(String message);
        void finished();
    }
    private final Handler main = new Handler(Looper.getMainLooper());
    private final Listener listener;
    private final ArrayList<String> chunks = new ArrayList<>();
    private TextToSpeech engine;
    private boolean ready = false;
    private boolean supported = false;
    private boolean playing = false;
    private boolean paused = false;
    private int cursor = 0;
    private long session = 0;
    private float rate = 1.0f;

    SpeechPlayer(Context context, Listener listener) {
        this.listener = listener;
        engine = new TextToSpeech(context.getApplicationContext(), result -> {
            ready = result == TextToSpeech.SUCCESS;
            if (!ready) {
                listener.status("Không khởi tạo được công cụ đọc tiếng trên BOOX.");
                return;
            }
            int rc = engine.setLanguage(new Locale("vi", "VN"));
            supported = (rc != TextToSpeech.LANG_MISSING_DATA &&
                    rc != TextToSpeech.LANG_NOT_SUPPORTED);
            engine.setSpeechRate(rate);
            engine.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                @Override public void onStart(String id) {}
                @Override public void onDone(String id) { main.post(() -> {
                    if (!playing || paused || !id.equals(session + "_" + cursor)) return;
                    cursor++;
                    if (cursor >= chunks.size()) {
                        playing = false;
                        listener.finished();
                    } else speakCurrent();
                });}
                @Override public void onError(String id) {
                    main.post(() -> listener.status("Không phát được đoạn âm thanh. Kiểm tra giọng TTS."));
                }
            });
            listener.status(supported ? "Đã sẵn sàng giọng tiếng Việt." :
                "Chưa có giọng đọc tiếng Việt. Vào Cài đặt → Text-to-Speech để cài và chọn tiếng Việt.");
        });
    }

    boolean isReady() { return ready && supported; }

    void setRate(float speed) {
        rate = Math.max(0.6f, Math.min(1.6f, speed));
        if (engine != null && ready) engine.setSpeechRate(rate);
    }
    float getRate() { return rate; }

    void play(String text) {
        if (!isReady()) {
            listener.status("BOOX chưa có giọng đọc tiếng Việt. Hãy kiểm tra Cài đặt → Chuyển văn bản thành giọng nói.");
            return;
        }
        if (text == null || text.trim().isEmpty()) {
            listener.status("Chưa có nội dung để đọc."); return;
        }
        stop();
        chunks.addAll(segment(text));
        if (chunks.isEmpty()) { listener.status("Không có chữ để đọc."); return; }
        cursor = 0;
        playing = true;
        paused = false;
        speakCurrent();
    }

    void pause() {
        if (!playing || paused) return;
        paused = true;
        engine.stop();
        listener.status("Đã tạm dừng. Tiếp tục sẽ đọc lại từ đầu đoạn hiện tại.");
    }

    void resume() {
        if (!playing || !paused) return;
        paused = false;
        speakCurrent();
    }

    void stop() {
        session++;
        playing = false;
        paused = false;
        cursor = 0;
        chunks.clear();
        if (engine != null) engine.stop();
    }

    void shutdown() {
        stop();
        if (engine != null) engine.shutdown();
        engine = null;
    }

    private void speakCurrent() {
        if (!playing || paused || cursor >= chunks.size()) return;
        String id = session + "_" + cursor;
        listener.status("Đang đọc đoạn " + (cursor + 1) + "/" + chunks.size());
        int result = engine.speak(chunks.get(cursor), TextToSpeech.QUEUE_FLUSH, null, id);
        if (result == TextToSpeech.ERROR) {
            playing = false;
            listener.status("Bộ đọc trả lỗi. Kiểm tra giọng tiếng Việt của Android.");
        }
    }

    private static ArrayList<String> segment(String text) {
        ArrayList<String> output = new ArrayList<>();
        String cleaned = text.replace('\r', '\n').replaceAll("\\n{3,}", "\n\n").trim();
        // Max Android TTS input is 4000; keep each call <= 1200 chars for stability.
        int position = 0;
        while (position < cleaned.length()) {
            int end = Math.min(position + 1100, cleaned.length());
            if (end < cleaned.length()) {
                int split = -1;
                for (int j = end - 1; j > position + 350; j--) {
                    char c = cleaned.charAt(j);
                    if (c == '\n' || c == '.' || c == '!' || c == '?' || c == ';') {
                        split = j + 1; break;
                    }
                }
                if (split > position) end = split;
            }
            String chunk = cleaned.substring(position, end).trim();
            if (!chunk.isEmpty()) output.add(chunk);
            position = end;
        }
        return output;
    }
}
