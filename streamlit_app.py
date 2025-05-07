import time
import streamlit as st
from openai import OpenAI
import tempfile
import os

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッションステート初期化
if "busy_until" not in st.session_state:
    st.session_state.busy_until = 0

# メインアプリ
st.title("🎤 Whisper文字起こしアプリ")

audio = st.file_uploader("音声ファイルを選択", type=["mp3","wav","m4a","mp4","webm"])
model = st.selectbox("モデルを選択", ["whisper-1", "gpt-4o-mini-transcribe"])

def transcribe_once(file, model_name):
    now = time.time()
    # 1分以内はブロック
    if now < st.session_state.busy_until:
        st.error("1分以内の連続呼び出しは禁止です。少し待ってから再度実行してください。")
        return None
    st.session_state.busy_until = now + 60

    try:
        # ファイルを一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_file_path = tmp_file.name

        st.info(f"一時ファイルに保存: {tmp_file_path}")
        
        # 一時ファイルを開いてAPIに渡す
        with open(tmp_file_path, "rb") as audio_file:
            # APIオプション
            if model_name == "gpt-4o-mini-transcribe":
                options = {
                    "model": model_name,
                    "file": audio_file,
                    "response_format": "text"  # モデルに合わせて簡易な形式を使用
                }
            else:
                options = {
                    "model": model_name,
                    "file": audio_file,
                    "response_format": "text"  # まずはテキストのみで試す
                }
            
            result = client.audio.transcriptions.create(**options)
            
        # 一時ファイルを削除
        os.unlink(tmp_file_path)
        
        return result
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

if audio and st.button("文字起こし開始"):
    # デバッグ情報表示
    st.info(f"ファイル名: {audio.name if hasattr(audio, 'name') else '不明'}")
    st.info(f"ファイルタイプ: {audio.type if hasattr(audio, 'type') else '不明'}")
    st.info(f"ファイルサイズ: {audio.size if hasattr(audio, 'size') else '不明'} bytes")
    
    with st.spinner("文字起こし中…"):
        result = transcribe_once(audio, model)
    
    if result:
        st.subheader("文字起こし結果")
        st.text_area("テキスト", result, height=300)
        st.download_button("テキストを保存", result, file_name="transcript.txt")
