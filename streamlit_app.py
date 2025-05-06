import time, streamlit as st, openai
from openai.error import RateLimitError

#── セッションステート準備 ──#
if "busy_until" not in st.session_state:
    st.session_state.busy_until = 0

def transcribe_once(file, model):
    now = time.time()
    # 60秒以内ならブロック
    if now < st.session_state.busy_until:
        st.error("1 分以内の再実行はできません。少し待ってください。")
        return None
    # フラグを次に叩ける時刻にセット
    st.session_state.busy_until = now + 60

    try:
        return openai.Audio.transcribe(model=model, file=file, response_format="text")
    except RateLimitError:
        st.error("リクエストが集中しています。１分後にまたお試しください。")
        return None

#── UI 部分 ──#
audio = st.file_uploader("音声を選択", type=["mp3","wav"])
model = st.selectbox("モデル", ["gpt-4o-mini-transcribe","whisper-1"])
if audio and st.button("文字起こし"):
    with st.spinner("処理中…"):
        text = transcribe_once(audio, model)
    if text:
        st.text_area("結果", text)
