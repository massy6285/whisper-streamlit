import time
import streamlit as st
from openai import OpenAI
import tempfile
import os
from datetime import datetime
import json

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッション状態の初期化 - 履歴保存用
if "transcription_history" not in st.session_state:
    st.session_state.transcription_history = []

# メインアプリのタイトル
st.title("🎤 Whisper文字起こしアプリ")

# タブ作成: 文字起こしと履歴
tab1, tab2 = st.tabs(["文字起こし", "履歴"])

# ユーティリティ関数 - 先に定義しておく
def format_timestamp(seconds):
    """秒数を MM:SS.MS 形式に変換"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{minutes:02}:{secs:02}.{millisecs:03}"

# 文字起こしタブの内容
with tab1:
    # ファイルアップロード
    audio = st.file_uploader("音声ファイルを選択", type=["mp3","wav","m4a","mp4","webm"])
    
    # モデル選択
    model = st.selectbox("モデルを選択", ["whisper-1", "gpt-4o-mini-transcribe"])
    
    # シンプルな詳細設定
    show_timestamps = st.checkbox("タイムスタンプを表示", value=True)
    
    # 音声の種類（シンプルなドロップダウン）
    audio_context = st.selectbox("音声の内容", [
        "指定なし", 
        "講演/プレゼン", 
        "会議/ミーティング", 
        "インタビュー",
        "授業/講義",
        "商談",
        "説教/スピーチ"
    ])
    
    # 固有名詞
    proper_nouns = st.text_input("固有名詞（カンマ区切り）", "")
    
    # 文字起こし関数の定義
    def transcribe_audio(file, model_name, with_timestamps, context="", nouns=""):
        try:
            # プロンプト作成
            prompt = ""
            if context != "指定なし":
                prompt += f"この音声は{context}です。"
            
            if nouns:
                nouns_list = [n.strip() for n in nouns.replace("、", ",").split(",") if n.strip()]
                if nouns_list:
                    prompt += f" 次の固有名詞が含まれています: {', '.join(nouns_list)}。"
            
            # ファイルを一時ファイルとして保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
                tmp_file.write(file.getvalue())
                tmp_file_path = tmp_file.name
            
            # 進捗表示用のプレースホルダー
            progress = st.progress(30, text="文字起こし中...")
            
            # 一時ファイルを開いてAPIに渡す
            with open(tmp_file_path, "rb") as audio_file:
                # APIオプション
                options = {
                    "model": model_name,
                    "file": audio_file
                }
                
                # タイムスタンプを追加（whisper-1でのみ使用可能）
                if with_timestamps and model_name == "whisper-1":
                    options["response_format"] = "verbose_json"
                    options["timestamp_granularities"] = ["segment"]
                else:
                    options["response_format"] = "text"
                
                # プロンプトが指定されている場合は追加
                if prompt:
                    options["prompt"] = prompt
                    st.info(f"使用するプロンプト: {prompt}")
                
                progress.progress(60, text="OpenAI APIに送信中...")
                result = client.audio.transcriptions.create(**options)
                
            # 進捗を更新
            progress.progress(100, text="完了!")
            
            # 一時ファイルを削除
            os.unlink(tmp_file_path)
            
            return result
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None
    
    # 文字起こし実行ボタン
    if audio and st.button("文字起こし開始"):
        # ファイルサイズチェック - 25MB以上は警告表示
        if audio.size > 25 * 1024 * 1024:  # 25MB
            st.warning("⚠️ ファイルサイズが25MBを超えています。OpenAI APIの制限により処理できない可能性があります。")
        
        # ファイル情報表示
        st.info(f"ファイル: {audio.name} ({audio.size} bytes)")
        
        # 文字起こし実行
        with st.spinner("文字起こし中..."):
            result = transcribe_audio(
                file=audio, 
                model_name=model, 
                with_timestamps=show_timestamps,
                context=audio_context,
                nouns=proper_nouns
            )
        
        if result:
            # 結果表示（タイプによって分岐）
            if isinstance(result, str):
                # テキスト形式の場合
                st.subheader("文字起こし結果")
                st.text_area("テキスト", result, height=300)
                plaintext = result
            elif hasattr(result, 'text'):
                # verbose_json形式の場合
                st.subheader("文字起こし結果")
                st.text_area("テキスト", result.text, height=200)
                plaintext = result.text
                
                # タイムスタンプ付きセグメント表示（修正部分）
                if hasattr(result, 'segments'):
                    st.subheader("タイムスタンプ付きセグメント")
                    for segment in result.segments:
                        try:
                            # segment オブジェクトから直接属性にアクセス
                            if hasattr(segment, 'start') and hasattr(segment, 'end') and hasattr(segment, 'text'):
                                start_time = format_timestamp(segment.start)
                                end_time = format_timestamp(segment.end)
                                segment_text = segment.text
                            # dict の場合
                            elif isinstance(segment, dict):
                                start_time = format_timestamp(segment.get('start', 0))
                                end_time = format_timestamp(segment.get('end', 0))
                                segment_text = segment.get('text', '')
                            else:
                                start_time = "??:??"
                                end_time = "??:??"
                                segment_text = str(segment)
                                
                            st.markdown(f"**[{start_time} → {end_time}]** {segment_text}")
                        except Exception as e:
                            st.error(f"セグメント表示エラー: {str(e)}")
                            st.write(f"セグメント内容: {segment}")
            else:
                # その他の形式（JSON文字列など）
                st.subheader("文字起こし結果")
                if isinstance(result, dict) and 'text' in result:
                    plaintext = result['text']
                else:
                    plaintext = str(result)
                st.text_area("テキスト", plaintext, height=300)
            
            # ダウンロードボタン
            st.download_button(
                "テキストファイルをダウンロード", 
                plaintext, 
                file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            # 履歴に保存
            st.session_state.transcription_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "filename": audio.name,
                "text": plaintext[:5000]  # 長すぎる場合は切り詰め
            })
            st.success("結果を履歴に保存しました！")

# 履歴タブの内容
with tab2:
    st.header("文字起こし履歴")
    
    if not st.session_state.transcription_history:
        st.info("まだ履歴がありません。文字起こしを実行すると、ここに結果が表示されます。")
    else:
        # 履歴の表示（新しい順）
        for i, item in enumerate(reversed(st.session_state.transcription_history)):
            with st.expander(f"{item['timestamp']} - {item['filename']}"):
                st.text_area(
                    "文字起こし結果", 
                    item["text"], 
                    height=200,
                    key=f"history_{i}"
                )
                st.download_button(
                    "テキストを保存", 
                    item["text"], 
                    file_name=f"{item['filename']}_{item['timestamp']}.txt",
                    key=f"download_{i}"
                )
        
        # 履歴クリアボタン
        if st.button("履歴をクリア"):
            st.session_state.transcription_history = []
            st.experimental_rerun()
