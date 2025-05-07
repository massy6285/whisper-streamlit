import time
import streamlit as st
from openai import OpenAI

# APIキーをシークレットから取得して初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッションステート初期化
if "busy_until" not in st.session_state:
    st.session_state.busy_until = 0

# パスワード認証機能（オプション）
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "APP_PASSWORD" in st.secrets and not st.session_state.authenticated:
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("パスワードが違います")
    st.stop()

# メインアプリ
st.title("🎤 Whisper文字起こしアプリ")

audio = st.file_uploader("音声ファイルを選択", type=["mp3","wav","m4a","mp4","webm","mpeg4"])
model = st.selectbox("モデルを選択", ["whisper-1", "gpt-4o-mini-transcribe"])

def transcribe_once(file, model_name):
    now = time.time()
    # 1分以内はブロック
    if now < st.session_state.busy_until:
        st.error("1分以内の連続呼び出しは禁止です。少し待ってから再度実行してください。")
        return None
    st.session_state.busy_until = now + 60

    try:
        return client.audio.transcriptions.create(
            model=model_name,
            file=file,
            response_format="text"
        )
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        return None

if audio and st.button("文字起こし開始"):
    with st.spinner("文字起こし中…"):
        result = transcribe_once(audio, model)
    if result:
        st.text_area("文字起こし結果", result, height=300)
        st.download_button("テキストを保存", result, file_name="transcript.txt")
