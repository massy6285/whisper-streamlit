import time
import streamlit as st
from openai import OpenAI
import tempfile
import os
from datetime import datetime
import random

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッション状態の初期化 - 履歴保存用
if "transcription_history" not in st.session_state:
    st.session_state.transcription_history = []

# メインアプリのタイトル
st.title("🎤 Whisper文字起こしアプリ")

# タブ作成: 文字起こしと履歴
tab1, tab2 = st.tabs(["文字起こし", "履歴"])

# 文字起こしタブの内容
with tab1:
    audio = st.file_uploader("音声ファイルを選択", type=["mp3","wav","m4a","mp4","webm"])
    model = st.selectbox("モデルを選択", ["whisper-1", "gpt-4o-mini-transcribe"])
    
    # 文字起こし関数の定義
    def transcribe_once(file, model_name, progress_bar):
        try:
            # 擬似的な進捗表示のための処理
            progress_bar.progress(10, text="ファイルを準備中...")
            time.sleep(0.5)  # わずかな遅延でUXを向上
            
            # ファイルを一時ファイルとして保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
                tmp_file.write(file.getvalue())
                tmp_file_path = tmp_file.name
            
            progress_bar.progress(30, text="音声分析中...")
            time.sleep(0.5)
            
            # 一時ファイルを開いてAPIに渡す
            with open(tmp_file_path, "rb") as audio_file:
                # APIオプション
                options = {
                    "model": model_name,
                    "file": audio_file,
                    "response_format": "text"  # シンプルなテキスト形式
                }
                
                progress_bar.progress(50, text="OpenAI APIに送信中...")
                result = client.audio.transcriptions.create(**options)
                
            # 進捗を更新
            progress_bar.progress(90, text="結果を処理中...")
            time.sleep(0.5)
            
            # 一時ファイルを削除
            os.unlink(tmp_file_path)
            
            # 完了
            progress_bar.progress(100, text="完了!")
            
            return result
        except Exception as e:
            # エラー発生時も進捗バーを100%にする
            progress_bar.progress(100, text="エラーが発生しました")
            st.error(f"エラーが発生しました: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None
    
    # 文字起こし実行ボタン
    if audio and st.button("文字起こし開始"):
        # ファイルサイズチェック - 25MB以上は警告表示
        if audio.size > 25 * 1024 * 1024:  # 25MB
            st.warning("⚠️ ファイルサイズが25MBを超えています。OpenAI APIの制限により処理できない可能性があります。ファイルを圧縮するか分割してください。")
        
        # デバッグ情報表示
        st.info(f"ファイル名: {audio.name if hasattr(audio, 'name') else '不明'}")
        st.info(f"ファイルタイプ: {audio.type if hasattr(audio, 'type') else '不明'}")
        st.info(f"ファイルサイズ: {audio.size if hasattr(audio, 'size') else '不明'} bytes")
        
        # 進捗状況コンテナ
        progress_container = st.container()
        
        # マメ知識表示用コンテナ
        tips_container = st.container()
        
        # マメ知識リスト
        tips = [
            "音声が明瞭なほど、文字起こしの精度が上がります。",
            "バックグラウンドノイズが少ない環境で録音すると良い結果が得られます。",
            "長い音声ファイルは、5-10分ごとに分割すると処理しやすくなります。",
            "Whisperは25以上の言語に対応しています。",
            "音声ファイルは25MB以下に抑えるのがベストプラクティスです。"
        ]
        
        # 進捗バーの作成
        progress_bar = progress_container.progress(0, text="準備中...")
        
        # マメ知識をランダム表示（シンプル化）
        with tips_container:
            st.info(f"💡 マメ知識: {random.choice(tips)}")
        
        # 文字起こし実行
        with st.spinner("文字起こし中..."):
            result = transcribe_once(audio, model, progress_bar)
        
        if result:
            # 結果表示
            st.subheader("文字起こし結果")
            st.text_area("テキスト", result, height=300)
            st.download_button("テキストを保存", result, file_name="transcript.txt")
            
            # 履歴に保存
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_item = {
                "timestamp": timestamp,
                "filename": audio.name if hasattr(audio, "name") else "不明",
                "model": model,
                "filesize": audio.size if hasattr(audio, "size") else 0,
                "text": result
            }
            st.session_state.transcription_history.append(history_item)
            st.success("文字起こし結果を履歴に保存しました！「履歴」タブで確認できます。")

# 履歴タブの内容
with tab2:
    st.header("文字起こし履歴")
    
    if not st.session_state.transcription_history:
        st.info("まだ履歴がありません。文字起こしを実行すると、ここに結果が表示されます。")
    else:
        # 履歴の表示（新しい順）
        for i, item in enumerate(reversed(st.session_state.transcription_history)):
            with st.expander(f"#{len(st.session_state.transcription_history)-i} - {item['timestamp']} - {item['filename']} ({item['model']})"):
                st.text_area(
                    f"文字起こし結果", 
                    item["text"], 
                    height=200,
                    key=f"history_{i}"
                )
                
                # ダウンロードボタン
                st.download_button(
                    "テキストを保存", 
                    item["text"], 
                    file_name=f"{item['filename']}_{item['timestamp']}.txt",
                    key=f"download_{i}"
                )
        
        # 履歴クリアボタン
        if st.button("履歴をクリア"):
            st.session_state.transcription_history = []
            st.experimental_rerun()  # 画面を更新
