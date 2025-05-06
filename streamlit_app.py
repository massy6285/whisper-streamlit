import openai
import streamlit as st

# Secrets から APIキーとパスワード（任意）を取得
openai.api_key = st.secrets["OPENAI_API_KEY"]
PASSWORD = st.secrets.get("APP_PASSWORD")
if PASSWORD:
    pw = st.text_input("🔒 パスワードを入力", type="password")
    if pw != PASSWORD:
        st.warning("パスワードが違います")
        st.stop()

st.title("🎤 Whisper文字起こしアプリ")

audio_file = st.file_uploader(
    "音声ファイルを選択",
    type=["mp3","wav","m4a","mp4","webm"]
)
model = st.selectbox(
    "モデルを選択",
    ["gpt-4o-mini-transcribe","gpt-4o-transcribe","whisper-1"]
)

if audio_file and st.button("文字起こし開始"):
    with st.spinner("文字起こし中…"):
        resp = openai.Audio.transcribe(
            model=model,
            file=audio_file,
            response_format="text"
        )
    st.text_area("結果テキスト", resp, height=300)
    st.download_button("テキストをダウンロード", resp, file_name="transcript.txt")
