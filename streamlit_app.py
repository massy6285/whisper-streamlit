audio = st.file_uploader("音声を選択", type=["mp3","wav"])
model = st.selectbox("モデル", ["gpt-4o-mini-transcribe","whisper-1"])
if audio and st.button("文字起こし"):
    with st.spinner("処理中…"):
        text = transcribe_once(audio, model)
    if text:
        st.text_area("結果", text)
