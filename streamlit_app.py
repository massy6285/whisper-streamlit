from typing import Any, Dict, List, Optional

import streamlit as st
from openai import BadRequestError, OpenAI
import tempfile
import os
from datetime import datetime
import math
from pydub import AudioSegment

st.set_page_config(
    page_title="スチームパンク文字起こしラボ",
    page_icon="🕰️",
    layout="wide",
)

STEAMPUNK_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;700&family=Special+Elite&display=swap');

:root {
    --steam-brass: #c8a46a;
    --steam-copper: #a4692b;
    --steam-iron: #2a2016;
    --steam-slate: #45392c;
    --steam-cream: #f8f1e2;
}

html, body {
    background: radial-gradient(circle at top left, rgba(79,55,32,0.7), rgba(26,20,15,0.95)),
                url('https://upload.wikimedia.org/wikipedia/commons/4/4d/Antique-paper-texture.jpg');
    background-size: cover;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, rgba(35,26,19,0.95), rgba(17,13,10,0.9));
    color: var(--steam-cream);
    font-family: 'Shippori Mincho', 'Noto Serif JP', serif;
}

.stApp { background-color: transparent; }

[data-testid="stHeader"] {
    background: rgba(0, 0, 0, 0);
}

div.block-container {
    background: rgba(39, 29, 21, 0.85);
    padding: 2.5rem 3rem;
    border-radius: 18px;
    border: 2px solid var(--steam-brass);
    box-shadow: 0 25px 40px rgba(0,0,0,0.45);
}

[data-testid="stSidebar"] {
    background: rgba(26, 18, 12, 0.92);
    border-right: 2px solid var(--steam-copper);
}

[data-testid="stSidebar"] * {
    color: var(--steam-cream) !important;
    font-family: 'Special Elite', 'Shippori Mincho', serif;
}

h1, h2, h3, h4, h5 {
    font-family: 'Special Elite', 'Shippori Mincho', serif;
    color: var(--steam-brass);
    text-shadow: 0 0 8px rgba(160, 114, 51, 0.6);
}

.stMarkdown p {
    color: var(--steam-cream);
    line-height: 1.7;
}

[data-testid="stFileUploader"] > label,
[data-testid="stSelectbox"] > label,
[data-testid="stSlider"] > label,
[data-testid="stTextInput"] > label,
[data-testid="stCheckbox"] > label {
    font-weight: 700;
    color: var(--steam-brass);
}

[data-testid="stFileUploader"] section {
    background: rgba(54, 40, 28, 0.8);
    border: 1px dashed var(--steam-brass);
    border-radius: 12px;
}

button[kind="secondary"] {
    background: linear-gradient(145deg, rgba(84, 59, 38, 0.9), rgba(37, 27, 19, 0.95));
    color: var(--steam-cream);
    border: 1px solid var(--steam-brass);
    box-shadow: inset 0 0 10px rgba(0,0,0,0.3), 0 8px 18px rgba(0,0,0,0.4);
}

button[kind="secondary"]:hover {
    border-color: #e3c995;
    color: #fff3d5;
    transform: translateY(-1px);
}

div[data-testid="stTabs"] button {
    background: linear-gradient(135deg, rgba(70, 51, 34, 0.9), rgba(30, 22, 16, 0.9));
    border: 1px solid var(--steam-copper);
    color: var(--steam-cream);
    font-family: 'Special Elite', 'Shippori Mincho', serif;
    position: relative;
}

div[data-testid="stTabs"] button:hover {
    border-color: var(--steam-brass);
}

div[data-testid="stTabs"] button:nth-child(1)::after,
div[data-testid="stTabs"] button:nth-child(2)::after {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    bottom: -55px;
    padding: 6px 12px;
    border-radius: 8px;
    background: rgba(54, 39, 26, 0.95);
    border: 1px solid var(--steam-brass);
    color: var(--steam-cream);
    white-space: nowrap;
    font-size: 0.8rem;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease-in-out;
    box-shadow: 0 8px 16px rgba(0,0,0,0.45);
}

div[data-testid="stTabs"] button:nth-child(1)::after {
    content: '音声ファイルを文字起こしするためのメイン画面です。';
}

div[data-testid="stTabs"] button:nth-child(2)::after {
    content: '保存された文字起こし結果を振り返り、再ダウンロードできます。';
}

div[data-testid="stTabs"] button:hover::after {
    opacity: 1;
}

div[data-testid="stExpander"] > details > summary {
    position: relative;
    font-family: 'Special Elite', 'Shippori Mincho', serif;
    color: var(--steam-brass);
}

div[data-testid="stExpander"] > details > summary::after {
    content: '高度なオプションを開きます。マウスオーバーで説明を確認できます。';
    position: absolute;
    left: 0;
    top: 100%;
    padding: 6px 12px;
    border-radius: 8px;
    background: rgba(54, 39, 26, 0.95);
    border: 1px solid var(--steam-brass);
    color: var(--steam-cream);
    font-size: 0.8rem;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease-in-out;
    margin-top: 6px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.45);
}

div[data-testid="stExpander"] > details > summary:hover::after {
    opacity: 1;
}

div[data-testid="stStatusWidget"] {
    border: 1px solid var(--steam-copper);
    background: rgba(40, 28, 19, 0.85);
}

div[data-baseweb="textarea"] textarea,
input,
.st-bp {
    background: rgba(32, 24, 18, 0.8) !important;
    color: var(--steam-cream) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(200,164,106,0.6) !important;
}

div[data-testid="stProgress"] div[role="progressbar"] {
    background: linear-gradient(90deg, rgba(141, 104, 54, 0.9), rgba(197, 173, 120, 0.9));
}

.stDownloadButton button,
.stButton button {
    background: linear-gradient(145deg, rgba(126, 89, 46, 0.95), rgba(61, 42, 25, 0.95));
    border: 1px solid var(--steam-brass);
    color: var(--steam-cream);
    box-shadow: inset 0 0 10px rgba(0,0,0,0.35), 0 10px 20px rgba(0,0,0,0.5);
    font-family: 'Special Elite', 'Shippori Mincho', serif;
    letter-spacing: 0.05em;
}

.stDownloadButton button:hover,
.stButton button:hover {
    border-color: #ffe2a9;
    color: #fff6dc;
}

.stAlert {
    background: rgba(56, 39, 27, 0.85);
    border: 1px solid var(--steam-copper);
}

.st-cg {
    color: var(--steam-cream) !important;
}

.stCaption, .stInfo {
    font-family: 'Shippori Mincho', serif;
}
</style>
"""

st.markdown(STEAMPUNK_STYLE, unsafe_allow_html=True)

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッション状態の初期化 - 履歴保存用
if "transcription_history" not in st.session_state:
    st.session_state.transcription_history = []

# メインアプリのタイトル
st.title("🕰️ スチームパンク・トランスクリプションラボ")
st.caption("歯車がきしむ実験室で、音声の謎を丁寧に記録しましょう。")

# 制限についての情報
st.info(
    "📌 **利用上のご案内**\n"
    "- ファイルサイズ: 最大25MB\n"
    "- 音声の長さ: 最大25分（1500秒）\n\n"
    "※ 制限を超える場合は、自動分割処理で適切に対応します。"
)

# タブ作成: 文字起こしと履歴
tab1, tab2 = st.tabs(["⚙️ 文字起こし工房", "📜 履歴アーカイブ"])

# ユーティリティ関数 - 先に定義しておく
def format_timestamp(seconds: Optional[float]) -> str:
    """秒数を MM:SS.MS 形式に変換"""
    if seconds is None:
        return "??:??.???"

    seconds = float(seconds)
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{minutes:02}:{secs:02}.{millisecs:03}"


def srt_timestamp(seconds: Optional[float]) -> str:
    """秒数をSRT形式のタイムスタンプに変換 (HH:MM:SS,MS)"""
    if seconds is None:
        return "00:00:00,000"

    seconds = float(seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)

    return f"{hours:02}:{minutes:02}:{secs:02},{millisecs:03}"

def _segment_get(segment: Any, key: str, default: Optional[Any] = None) -> Optional[Any]:
    """セグメントオブジェクト/辞書から値を取得"""

    if isinstance(segment, dict):
        return segment.get(key, default)

    return getattr(segment, key, default)


def _normalize_word(word: Any, time_offset: float = 0.0) -> Optional[Dict[str, Any]]:
    """単語レベルの情報を正規化"""

    start = _segment_get(word, "start")
    end = _segment_get(word, "end")
    token_text = _segment_get(word, "word")
    if token_text is None:
        token_text = _segment_get(word, "text", "")

    if start is None and end is None and not token_text:
        return None

    if start is not None:
        start = float(start) + time_offset

    if end is not None:
        end = float(end) + time_offset

    return {
        "start": start,
        "end": end,
        "text": str(token_text).strip(),
    }


def normalize_segment(segment: Any, time_offset: float = 0.0) -> Optional[Dict[str, Any]]:
    """APIからのセグメント情報を統一フォーマットに変換"""

    try:
        start = _segment_get(segment, "start")
        end = _segment_get(segment, "end")
        text = _segment_get(segment, "text", "")

        speaker: Optional[str] = None
        for key in ("speaker", "speaker_label", "speaker_id"):
            value = _segment_get(segment, key)
            if value not in (None, ""):
                speaker = str(value)
                break

        confidence = _segment_get(segment, "confidence")
        words_raw = _segment_get(segment, "words")
        normalized_words: List[Dict[str, Any]] = []

        if isinstance(words_raw, list):
            for word in words_raw:
                normalized_word = _normalize_word(word, time_offset)
                if normalized_word:
                    normalized_words.append(normalized_word)

        if start is not None:
            start = float(start) + time_offset

        if end is not None:
            end = float(end) + time_offset

        normalized_segment: Dict[str, Any] = {
            "start": start,
            "end": end,
            "text": str(text).strip(),
            "speaker": speaker,
        }

        if confidence is not None:
            normalized_segment["confidence"] = confidence

        if normalized_words:
            normalized_segment["words"] = normalized_words

        return normalized_segment
    except Exception:
        return None


def normalize_segments(segments: Any, time_offset: float = 0.0) -> List[Dict[str, Any]]:
    """セグメントのリストを正規化"""

    if segments is None:
        return []

    if not isinstance(segments, list):
        try:
            segments = list(segments)
        except TypeError:
            segments = []

    normalized: List[Dict[str, Any]] = []
    for segment in segments:
        normalized_segment = normalize_segment(segment, time_offset)
        if normalized_segment:
            normalized.append(normalized_segment)

    return normalized


def extract_segments_from_result(result: Any, time_offset: float = 0.0) -> List[Dict[str, Any]]:
    """APIレスポンスからセグメント情報を抽出"""

    if result is None:
        return []

    raw_segments: Any = []
    if hasattr(result, "segments"):
        raw_segments = getattr(result, "segments")
    elif isinstance(result, dict):
        raw_segments = result.get("segments", [])

    return normalize_segments(raw_segments, time_offset=time_offset)


def get_transcript_text(result: Any) -> str:
    """レスポンスから文字起こしテキストを取得"""

    if result is None:
        return ""

    if isinstance(result, str):
        return result

    text = getattr(result, "text", None)
    if text is not None:
        return str(text)

    if isinstance(result, dict):
        for key in ("text", "transcript"):
            value = result.get(key)
            if isinstance(value, str):
                return value

    return str(result)


def has_speaker_labels(segments: List[Dict[str, Any]]) -> bool:
    """話者情報の有無を判定"""

    return any(segment.get("speaker") for segment in segments)


def format_speaker_label(raw_label: Optional[str]) -> Optional[str]:
    """話者ラベルを表示用に整形"""

    if raw_label is None:
        return None

    label = str(raw_label).strip()
    if not label:
        return None

    return label


def display_speaker_timeline(segments: List[Dict[str, Any]]):
    """話者ごとの発話ブロックを表示"""

    if not segments:
        return

    blocks: List[Dict[str, Any]] = []
    current_block: Optional[Dict[str, Any]] = None

    for segment in segments:
        speaker_label = format_speaker_label(segment.get("speaker")) or "話者未識別"
        start = segment.get("start")
        end = segment.get("end")
        text = segment.get("text", "").strip()

        if current_block and current_block["speaker"] == speaker_label:
            if text:
                current_block["texts"].append(text)
            if end is not None:
                current_block["end"] = end
            if start is not None and current_block.get("start") is None:
                current_block["start"] = start
        else:
            if current_block:
                blocks.append(current_block)

            current_block = {
                "speaker": speaker_label,
                "start": start,
                "end": end,
                "texts": [text] if text else [],
            }

    if current_block:
        blocks.append(current_block)

    for block in blocks:
        start_label = format_timestamp(block.get("start"))
        end_label = format_timestamp(block.get("end"))
        st.markdown(f"**{block['speaker']} ({start_label} → {end_label})**")

        if block["texts"]:
            st.write(" ".join(block["texts"]))


def create_timestamped_text(segments, time_offset=0):
    """タイムスタンプ付きテキストを作成（オフセット付き）"""

    normalized_segments = normalize_segments(segments, time_offset=time_offset)
    timestamped_text = ""

    for segment in normalized_segments:
        start_time = format_timestamp(segment.get("start"))
        end_time = format_timestamp(segment.get("end"))
        segment_text = segment.get("text", "")
        speaker_label = format_speaker_label(segment.get("speaker"))

        if speaker_label:
            timestamped_text += f"[{start_time} → {end_time}] ({speaker_label}) {segment_text}\n\n"
        else:
            timestamped_text += f"[{start_time} → {end_time}] {segment_text}\n\n"

    return timestamped_text


def convert_to_srt(segments, time_offset=0):
    """Whisper APIの結果をSRT形式に変換（オフセット付き）"""

    normalized_segments = normalize_segments(segments, time_offset=time_offset)
    srt_content = ""

    for i, segment in enumerate(normalized_segments):
        start_time = srt_timestamp(segment.get("start"))
        end_time = srt_timestamp(segment.get("end"))
        text = segment.get("text", "")
        speaker_label = format_speaker_label(segment.get("speaker"))

        if speaker_label:
            text = f"{speaker_label}: {text}"

        srt_content += f"{i+1}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{text}\n\n"

    return srt_content

# 音声分割関数を追加
def split_audio_file(file_path, max_duration=1440):
    """音声ファイルを指定された最大長で分割する
    
    Args:
        file_path: 音声ファイルのパス
        max_duration: 最大分割長（秒）、デフォルトは24分
    
    Returns:
        分割されたファイルのパスのリスト
    """
    try:
        # 音声を読み込む
        st.info("⚙️ 歯車を調整しながら音声ファイルの分割を準備中です...")
        audio = AudioSegment.from_file(file_path)
        
        # 総時間（ミリ秒）
        total_duration_ms = len(audio)
        total_duration_sec = total_duration_ms / 1000
        
        # 必要な分割数を計算
        max_duration_ms = max_duration * 1000
        num_parts = math.ceil(total_duration_ms / max_duration_ms)
        
        if num_parts <= 1:
            # 分割の必要がない場合は元のファイルを返す
            return [file_path]
        
        st.info(f"🧭 音声を{num_parts}巻に切り分けています（合計時間: {total_duration_sec:.1f}秒）")
        
        # 一時ファイルのパスのリスト
        split_files = []
        
        # 分割して一時ファイルに保存
        for i in range(num_parts):
            start_ms = i * max_duration_ms
            end_ms = min((i + 1) * max_duration_ms, total_duration_ms)
            
            # セグメント切り出し
            segment = audio[start_ms:end_ms]
            
            # 一時ファイルに保存
            format_ext = os.path.splitext(file_path)[1].lstrip('.')
            if format_ext == '':
                format_ext = 'mp3'  # デフォルトフォーマット
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format_ext}") as tmp_file:
                segment_path = tmp_file.name
                segment.export(segment_path, format=format_ext)
                split_files.append(segment_path)
            
            st.info(f"🔩 パート {i+1}/{num_parts} を加工しました（{start_ms/1000:.1f}秒 → {end_ms/1000:.1f}秒）")
        
        return split_files
    
    except Exception as e:
        st.error(f"音声ファイル分割エラー: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return [file_path]  # エラーの場合は元のファイルを返す

# 文字起こしタブの内容
with tab1:
    # ファイルアップロード
    audio = st.file_uploader(
        "音声ファイルを選択",
        type=["mp3", "wav", "m4a", "mp4", "webm", "mpeg4"],
        help="歯車の中に投入する音声データをアップロードします。対応形式はMP3/WAV/M4A/MP4/WEBM/MPEG4です。",
    )

    # モデル選択
    model_labels = {
        "whisper-1": "Whisper-1（クラシックな高精度モデル）",
        "gpt-4o-mini-transcribe": "GPT-4o mini transcribe（話者分離に対応）",
    }
    model = st.selectbox(
        "モデルを選択",
        ["whisper-1", "gpt-4o-mini-transcribe"],
        format_func=lambda m: model_labels.get(m, m),
        help="文字起こしを担う機械の種類を選びます。話者分離を使う場合はGPT-4o mini transcribeがおすすめです。",
    )

    # 詳細設定エリア
    with st.expander("⚙️ 詳細設定"):
        show_timestamps = st.checkbox(
            "タイムスタンプを表示",
            value=True,
            help="各発話の開始・終了時刻を記録します。台本づくりや映像編集に便利です。",
        )
        enable_diarization = st.checkbox(
            "話者分離（スピーカー識別）を有効にする",
            value=False,
            help="※ 現在は gpt-4o-mini-transcribe での利用を推奨します。whisper-1 では話者情報が返されない場合があります。",
        )
        
        # 自動分割設定
        max_segment_duration = st.slider(
            "分割セグメントの最大長（分）", 
            min_value=5, 
            max_value=24, 
            value=20,
            help="制限を超える長い音声ファイルを分割する際の1セグメントあたりの最大長"
        )
        
        # 音声の種類
        audio_context = st.selectbox(
            "音声の内容",
            ["指定なし", "講演/プレゼン", "会議/ミーティング", "インタビュー", "授業/講義", "商談", "説教/スピーチ"],
            help="音声のおおまかな種類を選ぶと、モデルが文脈を理解しやすくなります。",
        )

        # 固有名詞
        proper_nouns = st.text_input(
            "固有名詞（カンマ区切り）",
            "",
            help="よく登場する名前や専門用語をカンマ区切りで入力すると、誤認識を減らせます。",
        )

    if 'enable_diarization' not in locals():
        enable_diarization = False

    if enable_diarization and model != "gpt-4o-mini-transcribe":
        st.warning("話者分離は gpt-4o-mini-transcribe モデルでの利用を推奨します。whisper-1 では話者情報が付与されない可能性があります。")
    
    # 文字起こし関数の定義
    def transcribe_audio(
        file_path,
        model_name,
        with_timestamps,
        context="",
        nouns="",
        enable_diarization=False,
    ):
        try:
            # プロンプト作成
            prompt = ""
            if context != "指定なし":
                prompt += f"この音声は{context}です。"
            
            if nouns:
                nouns_list = [n.strip() for n in nouns.replace("、", ",").split(",") if n.strip()]
                if nouns_list:
                    prompt += f" 次の固有名詞が含まれています: {', '.join(nouns_list)}。"
            
            # 進捗表示用のプレースホルダー
            progress = st.progress(5, text="蒸気機関を起動しています...")
            
            needs_segments = with_timestamps or enable_diarization
            diarization_requested = enable_diarization and model_name != "whisper-1"

            # 一時ファイルを開いてAPIに渡す
            with open(file_path, "rb") as audio_file:
                # APIオプション
                base_options: Dict[str, Any] = {
                    "model": model_name,
                    "file": audio_file,
                }

                if model_name == "whisper-1":
                    if needs_segments:
                        base_options["response_format"] = "verbose_json"
                        base_options["timestamp_granularities"] = ["segment"]
                    else:
                        base_options["response_format"] = "text"
                else:
                    if needs_segments:
                        base_options["response_format"] = "verbose_json"
                    else:
                        base_options["response_format"] = "json"

                if diarization_requested:
                    base_options["diarization"] = True

                # プロンプトが指定されている場合は追加
                if prompt:
                    base_options["prompt"] = prompt
                    st.info(f"📝 カスタム指示: {prompt}")

                attempt_options = dict(base_options)
                progress.progress(60, text="OpenAI 工房へ伝書鳩を飛ばしています...")

                try:
                    result = client.audio.transcriptions.create(**attempt_options)
                except BadRequestError as api_error:
                    fallback_applied = False
                    fallback_reasons: List[str] = []

                    if diarization_requested and "diarization" in attempt_options:
                        attempt_options.pop("diarization", None)
                        fallback_applied = True
                        fallback_reasons.append("話者分離")

                    if (
                        model_name != "whisper-1"
                        and attempt_options.get("response_format") == "verbose_json"
                    ):
                        attempt_options["response_format"] = "json"
                        attempt_options.pop("timestamp_granularities", None)
                        fallback_applied = True
                        fallback_reasons.append("詳細なタイムスタンプ")

                    if fallback_applied:
                        audio_file.seek(0)
                        fallback_note = "と".join(fallback_reasons)
                        st.warning(
                            f"{fallback_note}の指定がAPIでサポートされなかったため、設定を調整して再試行します。\n"
                            f"詳細: {api_error}"
                        )
                        result = client.audio.transcriptions.create(**attempt_options)
                    else:
                        raise

            # 進捗を更新
            progress.progress(100, text="完了! 蒸気機関を停止します。")

            return result
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None
    
    # 文字起こし実行ボタン
    if audio and st.button(
        "🛠️ 文字起こしを開始",
        help="アップロードした音声を解析し、文字とタイムスタンプを生成します。",
    ):
        # ファイルサイズチェック - 25MB以上は警告表示
        if audio.size > 25 * 1024 * 1024:  # 25MB
            st.warning("⚠️ ファイルサイズが25MBを超えています。OpenAI APIの制限により処理できない可能性があります。")
        
        # ファイル情報表示
        st.info(f"📁 取り扱いファイル: {audio.name} ({audio.size} bytes)")
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.name)[1]) as tmp_file:
            tmp_file.write(audio.getvalue())
            tmp_file_path = tmp_file.name
        
        # 音声の長さを取得して確認
        try:
            audio_segment = AudioSegment.from_file(tmp_file_path)
            duration_seconds = len(audio_segment) / 1000
            st.info(
                f"⏱️ 音声の長さ: {duration_seconds:.1f}秒（約{int(duration_seconds/60)}分{int(duration_seconds%60)}秒）"
            )
            
            # APIの制限（1500秒 = 25分）を超える場合は分割処理
            if duration_seconds > 1500:
                st.warning(f"⚠️ 音声ファイルの長さがOpenAI APIの制限（25分）を超えています。自動分割処理を行います。")
                
                # 音声ファイルを分割（最大で指定された分数）
                split_files = split_audio_file(
                    tmp_file_path, 
                    max_duration=max_segment_duration * 60  # 分を秒に変換
                )
                
                all_text_parts: List[str] = []
                all_segments: List[Dict[str, Any]] = []
                segment_offset = 0.0  # タイムスタンプオフセット（秒）

                for i, part_file in enumerate(split_files):
                    st.info(f"パート {i+1}/{len(split_files)} を処理中...")

                    result = transcribe_audio(
                        file_path=part_file,
                        model_name=model,
                        with_timestamps=show_timestamps,
                        context=audio_context,
                        nouns=proper_nouns,
                        enable_diarization=enable_diarization,
                    )

                    if result:
                        part_text = get_transcript_text(result).strip()
                        if part_text:
                            all_text_parts.append(f"--- パート {i+1} ---\n\n{part_text}")

                        part_segments = extract_segments_from_result(
                            result,
                            time_offset=segment_offset,
                        )
                        if part_segments:
                            all_segments.extend(part_segments)

                    part_duration = len(AudioSegment.from_file(part_file)) / 1000
                    segment_offset += part_duration

                    os.unlink(part_file)

                os.unlink(tmp_file_path)

                combined_text = "\n\n".join(all_text_parts).strip()
                has_segments = bool(all_segments)

                if combined_text:
                    st.subheader("文字起こし結果（複数パートを統合）")
                    st.text_area(
                        "テキスト",
                        combined_text,
                        height=300,
                        help="分割された全パートの文字起こしをまとめた全文です。必要に応じてコピーしてご利用ください。",
                    )
                else:
                    st.warning("文字起こしテキストを取得できませんでした。")

                if show_timestamps and has_segments:
                    st.subheader("タイムスタンプ付きセグメント")
                    for segment in all_segments:
                        start_time = format_timestamp(segment.get("start"))
                        end_time = format_timestamp(segment.get("end"))
                        segment_text = segment.get("text", "")
                        speaker_label = format_speaker_label(segment.get("speaker"))
                        prefix = f"**[{start_time} → {end_time}]**"
                        if speaker_label:
                            prefix += f" ({speaker_label})"
                        st.markdown(f"{prefix} {segment_text}")

                if enable_diarization:
                    st.subheader("話者ごとの発話")
                    if has_segments and has_speaker_labels(all_segments):
                        display_speaker_timeline(all_segments)
                    else:
                        st.warning("話者情報を取得できませんでした。モデルまたはレスポンス形式が未対応の可能性があります。")

                st.subheader("結果のダウンロード")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.download_button(
                        "テキストのみ (.txt)",
                        combined_text,
                        file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        help="文字起こし全文をテキスト形式で保存します。読み返しや編集にご利用ください。",
                    )

                if has_segments:
                    with col2:
                        timestamped_text = create_timestamped_text(all_segments)
                        st.download_button(
                            "タイムスタンプ付きテキスト (.txt)",
                            timestamped_text,
                            file_name=f"文字起こし_タイムスタンプ付き_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            help="各セグメントの開始・終了時刻を含むテキストを保存します。映像編集や原稿整理に便利です。",
                        )

                    with col3:
                        srt_content = convert_to_srt(all_segments)
                        st.download_button(
                            "字幕ファイル (.srt)",
                            srt_content,
                            file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                            mime="text/plain",
                            help="SRT形式の字幕ファイルを生成します。動画編集ソフトに取り込んで活用できます。",
                        )

                st.session_state.transcription_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "filename": audio.name,
                    "text": combined_text[:5000],
                    "has_timestamps": has_segments,
                    "segments": all_segments if has_segments else [],
                })
                st.success("結果を履歴に保存しました！")

                
            else:
                # APIの制限内の場合は通常処理
                with st.spinner("文字起こし中..."):
                    result = transcribe_audio(
                        file_path=tmp_file_path,
                        model_name=model,
                        with_timestamps=show_timestamps,
                        context=audio_context,
                        nouns=proper_nouns,
                        enable_diarization=enable_diarization,
                    )

                os.unlink(tmp_file_path)

                if result:
                    plaintext = get_transcript_text(result)
                    st.subheader("文字起こし結果")
                    st.text_area(
                        "テキスト",
                        plaintext,
                        height=300,
                        help="今回の文字起こしで得られた全文です。コピーしてメモや原稿に貼り付けられます。",
                    )

                    segments = extract_segments_from_result(result)
                    has_segments = bool(segments)

                    if show_timestamps and has_segments:
                        st.subheader("タイムスタンプ付きセグメント")
                        for segment in segments:
                            start_time = format_timestamp(segment.get("start"))
                            end_time = format_timestamp(segment.get("end"))
                            segment_text = segment.get("text", "")
                            speaker_label = format_speaker_label(segment.get("speaker"))
                            prefix = f"**[{start_time} → {end_time}]**"
                            if speaker_label:
                                prefix += f" ({speaker_label})"
                            st.markdown(f"{prefix} {segment_text}")

                    if enable_diarization:
                        st.subheader("話者ごとの発話")
                        if has_segments and has_speaker_labels(segments):
                            display_speaker_timeline(segments)
                        else:
                            st.warning("話者情報を取得できませんでした。モデルまたはレスポンス形式が未対応の可能性があります。")

                    st.subheader("結果のダウンロード")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.download_button(
                            "テキストのみ (.txt)",
                            plaintext,
                            file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            help="今回の文字起こし結果をテキストファイルとして保存します。",
                        )

                    if has_segments:
                        with col2:
                            timestamped_text = create_timestamped_text(segments)
                            st.download_button(
                                "タイムスタンプ付きテキスト (.txt)",
                                timestamped_text,
                                file_name=f"文字起こし_タイムスタンプ付き_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain",
                                help="タイムスタンプ入りのテキストを保存します。映像と同期させたい場合に便利です。",
                            )

                        with col3:
                            srt_content = convert_to_srt(segments)
                            st.download_button(
                                "字幕ファイル (.srt)",
                                srt_content,
                                file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                                mime="text/plain",
                                help="動画編集ソフトで使えるSRT形式の字幕ファイルをダウンロードします。",
                            )

                    st.session_state.transcription_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "filename": audio.name,
                        "text": plaintext[:5000],
                        "has_timestamps": has_segments,
                        "segments": segments if has_segments else [],
                    })
                    st.success("結果を履歴に保存しました！")

        
        except Exception as e:
            st.error(f"音声ファイルの長さ取得エラー: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            
            # エラーが発生しても通常処理を試みる
            st.warning("音声ファイルの長さを取得できませんでしたが、処理を続行します。")
            
            # 以下、通常の文字起こし処理（上記のコードと同様なので省略）
            with st.spinner("文字起こし中..."):
                result = transcribe_audio(
                    file_path=tmp_file_path,
                    model_name=model,
                    with_timestamps=show_timestamps,
                    context=audio_context,
                    nouns=proper_nouns,
                    enable_diarization=enable_diarization,
                )
            
            # 処理結果の表示（エラー処理のため省略）
            # ...

# 履歴タブの内容
with tab2:
    st.header("📜 文字起こし履歴アーカイブ")

    if not st.session_state.transcription_history:
        st.info("まだ記録された巻物はありません。文字起こしを実行すると、ここに成果が保管されます。")
    else:
        # 履歴の表示（新しい順）
        for i, item in enumerate(reversed(st.session_state.transcription_history)):
            with st.expander(f"{item['timestamp']} - {item['filename']}"):
                st.text_area(
                    "文字起こし結果",
                    item["text"],
                    height=200,
                    help="保存済みの文字起こし全文です。必要に応じて再確認やコピーができます。",
                    key=f"history_{i}"
                )
                
                # ダウンロードボタン - 履歴からも異なる形式でダウンロード可能に
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "テキストを保存",
                        item["text"],
                        file_name=f"{item['filename']}_{item['timestamp']}.txt",
                        help="この履歴の文字起こし全文をテキストファイルで保存します。",
                        key=f"download_txt_{i}"
                    )

                # タイムスタンプ情報がある場合は追加のダウンロードオプションを表示
                if item.get("has_timestamps", False) and item.get("segments"):
                    with col2:
                        timestamped_text = create_timestamped_text(item["segments"])
                        st.download_button(
                            "タイムスタンプ付きテキスト",
                            timestamped_text,
                            file_name=f"{item['filename']}_{item['timestamp']}_timestamps.txt",
                            help="タイムスタンプ入りのテキストを再ダウンロードします。再利用に便利です。",
                            key=f"download_timestamps_{i}"
                        )

                    with col3:
                        srt_content = convert_to_srt(item["segments"])
                        st.download_button(
                            "字幕ファイル (.srt)",
                            srt_content,
                            file_name=f"{item['filename']}_{item['timestamp']}.srt",
                            help="履歴からSRT形式の字幕ファイルを再取得します。",
                            key=f"download_srt_{i}"
                        )

                if item.get("segments") and has_speaker_labels(item["segments"]):
                    st.markdown("**話者ごとの発話プレビュー**")
                    display_speaker_timeline(item["segments"])
        
        # 履歴クリアボタン
        if st.button(
            "🧹 履歴をクリア",
            help="保存済みの文字起こし履歴をすべて削除します。必要なデータを保存済みかご確認ください。",
        ):
            st.session_state.transcription_history = []
            st.experimental_rerun()  # 画面を更新
