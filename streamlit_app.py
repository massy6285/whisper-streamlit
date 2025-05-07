import time
import streamlit as st
from openai import OpenAI
import tempfile
import os
from datetime import datetime
import random
import json

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッション状態の初期化 - 履歴保存用
if "transcription_history" not in st.session_state:
    st.session_state.transcription_history = []

# メインアプリのタイトル
st.title("🎤 高機能Whisper文字起こしアプリ")

# タブ作成: 文字起こしと履歴
tab1, tab2 = st.tabs(["文字起こし", "履歴"])

# 文字起こしタブの内容
with tab1:
    # ファイルアップロード
    audio = st.file_uploader("音声ファイルを選択", type=["mp3","wav","m4a","mp4","webm"])
    
    # モデル選択
    model = st.selectbox("モデルを選択", ["whisper-1", "gpt-4o-mini-transcribe"])
    
    # 詳細設定セクション
    with st.expander("詳細設定"):
        timestamp_enabled = st.checkbox("タイムスタンプを表示", value=True)
        
        # 音声種類セレクター
        audio_type = st.selectbox(
            "音声の種類を選択",
            ["指定なし", "講演/プレゼン", "会議/ミーティング", "インタビュー", "授業/講義", "商談", "説教/スピーチ", "その他"]
        )
        
        # 音声の言語
        language = st.selectbox(
            "主な言語",
            ["自動検出", "日本語", "英語", "その他"]
        )
        
        # 固有名詞リスト
        proper_nouns = st.text_area(
            "固有名詞/専門用語（カンマ区切りで入力）", 
            placeholder="例: ウイングアーク, SVF, 文字起こし, AI, GPT-4o..."
        )
        
        # カスタムプロンプト（上級者向け）
        custom_prompt = st.text_area(
            "カスタムプロンプト（上級者向け）", 
            placeholder="必要に応じて特別な指示をここに入力"
        )
    
    # 文字起こし関数の定義
    def transcribe_once(file, model_name, progress_bar, with_timestamps=True, prompt=""):
        try:
            # 擬似的な進捗表示のための処理
            progress_bar.progress(10, text="ファイルを準備中...")
            time.sleep(0.5)
            
            # ファイルを一時ファイルとして保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
                tmp_file.write(file.getvalue())
                tmp_file_path = tmp_file.name
            
            progress_bar.progress(30, text="音声分析中...")
            time.sleep(0.5)
            
            # 一時ファイルを開いてAPIに渡す
            with open(tmp_file_path, "rb") as audio_file:
                # APIオプション - モデルによって分岐
                if model_name == "whisper-1" and with_timestamps:
                    options = {
                        "model": model_name,
                        "file": audio_file,
                        "response_format": "verbose_json",
                        "timestamp_granularities": ["segment"]
                    }
                else:
                    # gpt-4o-mini-transcribeの場合またはタイムスタンプ不要の場合
                    options = {
                        "model": model_name,
                        "file": audio_file,
                        "response_format": "json" if model_name == "gpt-4o-mini-transcribe" else "text"
                    }
                
                # プロンプトが指定されている場合は追加
                if prompt:
                    options["prompt"] = prompt
                
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
        
        # プロンプトを構築
        prompt_parts = []
        
        # 音声種類に応じたコンテキスト
        if audio_type != "指定なし":
            prompt_parts.append(f"この音声は{audio_type}です。")
        
        # 言語指定
        if language == "日本語":
            prompt_parts.append("この音声は日本語です。")
        elif language == "英語":
            prompt_parts.append("この音声は英語です。")
        
        # 固有名詞の追加
        if proper_nouns:
            clean_nouns = proper_nouns.strip().replace("、", ",")
            nouns_list = [noun.strip() for noun in clean_nouns.split(",") if noun.strip()]
            if nouns_list:
                prompt_parts.append(f"次の固有名詞や専門用語が含まれています: {', '.join(nouns_list)}。")
        
        # カスタムプロンプトの追加
        if custom_prompt:
            prompt_parts.append(custom_prompt)
        
        # 最終プロンプトの作成
        final_prompt = " ".join(prompt_parts)
        
        # プロンプトがある場合は表示
        if final_prompt:
            st.info(f"使用するプロンプト: {final_prompt}")
        
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
            "音声ファイルは25MB以下に抑えるのがベストプラクティスです。",
            "固有名詞や専門用語を事前に指定すると、認識精度が上がります。",
            "言語を指定すると、特に多言語が混在する場合に精度が向上します。"
        ]
        
        # 進捗バーの作成
        progress_bar = progress_container.progress(0, text="準備中...")
        
        # マメ知識をランダム表示
        with tips_container:
            st.info(f"💡 マメ知識: {random.choice(tips)}")
        
        # 文字起こし実行
        with st.spinner("文字起こし中..."):
            result = transcribe_once(audio, model, progress_bar, timestamp_enabled, final_prompt)
        
        if result:
            # 結果表示 - レスポンス形式によって処理を分岐
            if isinstance(result, str):
                # テキスト形式の場合
                st.subheader("文字起こし結果")
                st.text_area("テキスト", result, height=300)
                plaintext = result
            elif hasattr(result, 'text') and hasattr(result, 'segments'):
                # verbose_json形式の場合（whisper-1のタイムスタンプあり）
                st.subheader("文字起こし結果")
                st.text_area("完全なテキスト", result.text, height=200)
                
                # タイムスタンプ付きセグメントを表示
                st.subheader("タイムスタンプ付きセグメント")
                for segment in result.segments:
                    # 開始時間と終了時間をフォーマット (秒→時:分:秒.ミリ秒)
                    start_time = format_time(segment.start)
                    end_time = format_time(segment.end)
                    
                    st.markdown(f"**[{start_time} → {end_time}]** {segment.text}")
                plaintext = result.text
            else:
                # JSONレスポンス（gpt-4o-mini-transcribe）
                try:
                    # 文字列の場合はJSONに変換
                    if isinstance(result, str):
                        result_json = json.loads(result)
                    else:
                        result_json = result
                    
                    st.subheader("文字起こし結果")
                    plaintext = result_json.get('text', '')
                    st.text_area("テキスト", plaintext, height=200)
                    
                    # セグメントがある場合はタイムスタンプ付きで表示
                    if 'segments' in result_json:
                        st.subheader("タイムスタンプ付きセグメント")
                        for segment in result_json['segments']:
                            start_time = format_time(segment.get('start', 0))
                            end_time = format_time(segment.get('end', 0))
                            text = segment.get('text', '')
                            st.markdown(f"**[{start_time} → {end_time}]** {text}")
                except Exception as e:
                    st.error(f"結果の解析エラー: {str(e)}")
                    st.text_area("生の結果", str(result), height=300)
                    plaintext = str(result)
            
            # ダウンロードボタン
            st.download_button("テキストを保存", plaintext, file_name="transcript.txt")
            
            # SRT形式でダウンロード（タイムスタンプがある場合）
            if (isinstance(result, object) and hasattr(result, 'segments')) or \
               (isinstance(result, dict) and 'segments' in result):
                srt_content = convert_to_srt(result)
                st.download_button(
                    "字幕ファイル(SRT)をダウンロード", 
                    srt_content, 
                    file_name=f"transcript.srt",
                    mime="text/plain"
                )
            
            # 履歴に保存
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_item = {
                "timestamp": timestamp,
                "filename": audio.name if hasattr(audio, "name") else "不明",
                "model": model,
                "filesize": audio.size if hasattr(audio, "size") else 0,
                "text": plaintext,
                "raw_result": str(result)[:1000]  # 容量節約のため最初の1000文字だけ保存
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

# ユーティリティ関数

def format_time(seconds):
    """秒数を HH:MM:SS.MS 形式にフォーマット"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02}:{minutes:02}:{secs:02}.{millisecs:03}"

def convert_to_srt(result):
    """Whisper APIの結果をSRT形式に変換"""
    srt_content = ""
    
    # 結果のタイプによって処理を分岐
    if hasattr(result, 'segments'):
        segments = result.segments
    elif isinstance(result, dict) and 'segments' in result:
        segments = result['segments']
    else:
        return "SRT変換エラー: セグメントが見つかりません"
    
    for i, segment in enumerate(segments):
        # セグメントの開始・終了時間を取得
        if hasattr(segment, 'start'):
            start = segment.start
            end = segment.end
            text = segment.text
        else:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '')
        
        # SRT形式のタイムスタンプフォーマット (HH:MM:SS,MS)
        start_time = srt_timestamp(start)
        end_time = srt_timestamp(end)
        
        # SRTエントリーを追加
        srt_content += f"{i+1}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{text}\n\n"
    
    return srt_content

def srt_timestamp(seconds):
    """秒数をSRT形式のタイムスタンプに変換 (HH:MM:SS,MS)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02}:{minutes:02}:{secs:02},{millisecs:03}"
