import time
import streamlit as st
from openai import OpenAI
import tempfile
import os
from datetime import datetime
import json
import math
from pydub import AudioSegment

# OpenAIクライアントの初期化
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# セッション状態の初期化 - 履歴保存用
if "transcription_history" not in st.session_state:
    st.session_state.transcription_history = []

# メインアプリのタイトル
st.title("🎤 Whisper文字起こしアプリ")

# 制限についての情報
st.info("📌 **注意**: OpenAI Whisper APIには以下の制限があります：\n"
        "- ファイルサイズ: 最大25MB\n"
        "- 音声の長さ: 最大25分（1500秒）\n\n"
        "※ 制限を超える場合は、自動分割処理を行います。")

# タブ作成: 文字起こしと履歴
tab1, tab2 = st.tabs(["文字起こし", "履歴"])

# ユーティリティ関数 - 先に定義しておく
def format_timestamp(seconds):
    """秒数を MM:SS.MS 形式に変換"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{minutes:02}:{secs:02}.{millisecs:03}"

def srt_timestamp(seconds):
    """秒数をSRT形式のタイムスタンプに変換 (HH:MM:SS,MS)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02}:{minutes:02}:{secs:02},{millisecs:03}"

def create_timestamped_text(segments, time_offset=0):
    """タイムスタンプ付きテキストを作成（オフセット付き）"""
    timestamped_text = ""
    
    for segment in segments:
        try:
            # segment オブジェクトから直接属性にアクセス
            if hasattr(segment, 'start') and hasattr(segment, 'end') and hasattr(segment, 'text'):
                start_time = format_timestamp(segment.start + time_offset)
                end_time = format_timestamp(segment.end + time_offset)
                segment_text = segment.text
            # dict の場合
            elif isinstance(segment, dict):
                start_time = format_timestamp(segment.get('start', 0) + time_offset)
                end_time = format_timestamp(segment.get('end', 0) + time_offset)
                segment_text = segment.get('text', '')
            else:
                start_time = "??:??"
                end_time = "??:??"
                segment_text = str(segment)
                
            timestamped_text += f"[{start_time} → {end_time}] {segment_text}\n\n"
        except Exception as e:
            timestamped_text += f"[エラー] セグメント処理エラー: {str(e)}\n\n"
    
    return timestamped_text

def convert_to_srt(segments, time_offset=0):
    """Whisper APIの結果をSRT形式に変換（オフセット付き）"""
    srt_content = ""
    
    for i, segment in enumerate(segments):
        try:
            # セグメントの開始・終了時間を取得
            if hasattr(segment, 'start') and hasattr(segment, 'end') and hasattr(segment, 'text'):
                start = segment.start + time_offset
                end = segment.end + time_offset
                text = segment.text
            elif isinstance(segment, dict):
                start = segment.get('start', 0) + time_offset
                end = segment.get('end', 0) + time_offset
                text = segment.get('text', '')
            else:
                continue  # 不明なセグメント形式はスキップ
            
            # SRT形式のタイムスタンプフォーマット (HH:MM:SS,MS)
            start_time = srt_timestamp(start)
            end_time = srt_timestamp(end)
            
            # SRTエントリーを追加
            srt_content += f"{i+1}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
        except Exception as e:
            # エラーが発生したセグメントはスキップ
            continue
    
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
        st.info("音声ファイルの分割を準備中...")
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
        
        st.info(f"音声ファイルを{num_parts}個のパートに分割します（合計時間: {total_duration_sec:.1f}秒）")
        
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
            
            st.info(f"パート {i+1}/{num_parts} を分割しました（{start_ms/1000:.1f}秒 → {end_ms/1000:.1f}秒）")
        
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
        type=["mp3", "wav", "m4a", "mp4", "webm", "mpeg4"]
    )
    
    # モデル選択
    model = st.selectbox("モデルを選択", ["whisper-1", "gpt-4o-mini-transcribe"])
    
    # 詳細設定エリア
    with st.expander("詳細設定"):
        show_timestamps = st.checkbox("タイムスタンプを表示", value=True)
        
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
            ["指定なし", "講演/プレゼン", "会議/ミーティング", "インタビュー", "授業/講義", "商談", "説教/スピーチ"]
        )
        
        # 固有名詞
        proper_nouns = st.text_input("固有名詞（カンマ区切り）", "")
    
    # 文字起こし関数の定義
    def transcribe_audio(file_path, model_name, with_timestamps, context="", nouns=""):
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
            progress = st.progress(30, text="文字起こし中...")
            
            # 一時ファイルを開いてAPIに渡す
            with open(file_path, "rb") as audio_file:
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
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.name)[1]) as tmp_file:
            tmp_file.write(audio.getvalue())
            tmp_file_path = tmp_file.name
        
        # 音声の長さを取得して確認
        try:
            audio_segment = AudioSegment.from_file(tmp_file_path)
            duration_seconds = len(audio_segment) / 1000
            st.info(f"音声の長さ: {duration_seconds:.1f}秒（約{int(duration_seconds/60)}分{int(duration_seconds%60)}秒）")
            
            # APIの制限（1500秒 = 25分）を超える場合は分割処理
            if duration_seconds > 1500:
                st.warning(f"⚠️ 音声ファイルの長さがOpenAI APIの制限（25分）を超えています。自動分割処理を行います。")
                
                # 音声ファイルを分割（最大で指定された分数）
                split_files = split_audio_file(
                    tmp_file_path, 
                    max_duration=max_segment_duration * 60  # 分を秒に変換
                )
                
                # 結果を保存するための変数
                all_text = ""
                all_segments = []
                segment_offset = 0  # タイムスタンプオフセット（秒）
                
                # 各パートを処理
                for i, part_file in enumerate(split_files):
                    st.info(f"パート {i+1}/{len(split_files)} を処理中...")
                    
                    # 文字起こし実行
                    result = transcribe_audio(
                        file_path=part_file,
                        model_name=model,
                        with_timestamps=show_timestamps,
                        context=audio_context,
                        nouns=proper_nouns
                    )
                    
                    # 結果を蓄積
                    if result:
                        if isinstance(result, str):
                            # テキスト形式の場合
                            all_text += f"\n--- パート {i+1} ---\n\n" + result
                        elif hasattr(result, 'text'):
                            # verbose_json形式の場合
                            all_text += f"\n--- パート {i+1} ---\n\n" + result.text
                            
                            # セグメント情報を保存（オフセット付き）
                            if hasattr(result, 'segments'):
                                # 各セグメントにオフセットを追加
                                for segment in result.segments:
                                    if hasattr(segment, 'start'):
                                        # セグメントが直接属性を持つ場合
                                        original_start = segment.start
                                        original_end = segment.end
                                        
                                        # 今のところPythonでオブジェクトの属性を直接書き換えるのは難しいかもしれないので、
                                        # 表示時にオフセットを考慮する方法を採用
                                        all_segments.append({
                                            'start': original_start + segment_offset,
                                            'end': original_end + segment_offset,
                                            'text': segment.text
                                        })
                                    elif isinstance(segment, dict):
                                        # 辞書型の場合
                                        segment_copy = segment.copy()
                                        segment_copy['start'] = segment.get('start', 0) + segment_offset
                                        segment_copy['end'] = segment.get('end', 0) + segment_offset
                                        all_segments.append(segment_copy)
                    
                    # タイムスタンプオフセットを更新（次のパートのために）
                    part_duration = len(AudioSegment.from_file(part_file)) / 1000
                    segment_offset += part_duration
                    
                    # 一時ファイルを削除
                    os.unlink(part_file)
                
                # 元の一時ファイルを削除
                os.unlink(tmp_file_path)
                
                # 統合された結果を表示
                st.subheader("文字起こし結果（複数パートを統合）")
                st.text_area("テキスト", all_text, height=300)
                
                # タイムスタンプ付きセグメント表示
                if show_timestamps and all_segments:
                    st.subheader("タイムスタンプ付きセグメント")
                    for segment in all_segments:
                        try:
                            if isinstance(segment, dict):
                                start_time = format_timestamp(segment.get('start', 0))
                                end_time = format_timestamp(segment.get('end', 0))
                                segment_text = segment.get('text', '')
                                st.markdown(f"**[{start_time} → {end_time}]** {segment_text}")
                        except Exception as e:
                            st.error(f"セグメント表示エラー: {str(e)}")
                
                # ダウンロードボタンエリア
                st.subheader("結果のダウンロード")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # 通常テキストのダウンロード
                    st.download_button(
                        "テキストのみ (.txt)", 
                        all_text, 
                        file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                if all_segments:
                    with col2:
                        # タイムスタンプ付きテキストのダウンロード
                        timestamped_text = ""
                        for segment in all_segments:
                            if isinstance(segment, dict):
                                start = format_timestamp(segment.get('start', 0))
                                end = format_timestamp(segment.get('end', 0))
                                text = segment.get('text', '')
                                timestamped_text += f"[{start} → {end}] {text}\n\n"
                        
                        st.download_button(
                            "タイムスタンプ付きテキスト (.txt)",
                            timestamped_text,
                            file_name=f"文字起こし_タイムスタンプ付き_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    with col3:
                        # SRT形式のダウンロード
                        srt_content = ""
                        for i, segment in enumerate(all_segments):
                            if isinstance(segment, dict):
                                start = srt_timestamp(segment.get('start', 0))
                                end = srt_timestamp(segment.get('end', 0))
                                text = segment.get('text', '')
                                srt_content += f"{i+1}\n{start} --> {end}\n{text}\n\n"
                        
                        st.download_button(
                            "字幕ファイル (.srt)",
                            srt_content,
                            file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                            mime="text/plain"
                        )
                
                # 履歴に保存
                st.session_state.transcription_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "filename": audio.name,
                    "text": all_text[:5000],  # 長すぎる場合は切り詰め
                    "has_timestamps": bool(all_segments),
                    "segments": all_segments if all_segments else []
                })
                st.success("結果を履歴に保存しました！")
                
            else:
                # APIの制限内の場合は通常処理
                # 文字起こし実行
                with st.spinner("文字起こし中..."):
                    result = transcribe_audio(
                        file_path=tmp_file_path,
                        model_name=model,
                        with_timestamps=show_timestamps,
                        context=audio_context,
                        nouns=proper_nouns
                    )
                
                # 一時ファイルを削除
                os.unlink(tmp_file_path)
                
                if result:
                    # 結果表示（タイプによって分岐）
                    has_segments = False
                    segments = []
                    
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
                        
                        # タイムスタンプ付きセグメント表示
                        if hasattr(result, 'segments'):
                            has_segments = True
                            segments = result.segments
                            
                            st.subheader("タイムスタンプ付きセグメント")
                            for segment in segments:
                                try:
                                    start_time = format_timestamp(segment.start)
                                    end_time = format_timestamp(segment.end)
                                    st.markdown(f"**[{start_time} → {end_time}]** {segment.text}")
                                except Exception as e:
                                    st.error(f"セグメント表示エラー: {str(e)}")
                    else:
                        # その他の形式（JSON文字列など）
                        st.subheader("文字起こし結果")
                        if isinstance(result, dict) and 'text' in result:
                            plaintext = result['text']
                            # JSONからセグメント情報を取得
                            if 'segments' in result:
                                has_segments = True
                                segments = result['segments']
                        else:
                            plaintext = str(result)
                        st.text_area("テキスト", plaintext, height=300)
                    
                    # ダウンロードボタンエリア
                    st.subheader("結果のダウンロード")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # 通常テキストのダウンロード
                        st.download_button(
                            "テキストのみ (.txt)", 
                            plaintext, 
                            file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    # タイムスタンプ付きテキストのダウンロード（セグメントがある場合のみ）
                    if has_segments and segments:
                        with col2:
                            timestamped_text = create_timestamped_text(segments)
                            st.download_button(
                                "タイムスタンプ付きテキスト (.txt)",
                                timestamped_text,
                                file_name=f"文字起こし_タイムスタンプ付き_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain"
                            )
                        
                        with col3:
                            # SRT形式のダウンロード
                            srt_content = convert_to_srt(segments)
                            st.download_button(
                                "字幕ファイル (.srt)",
                                srt_content,
                                file_name=f"文字起こし_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                                mime="text/plain"
                            )
                    
                    # 履歴に保存
                    st.session_state.transcription_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "filename": audio.name,
                        "text": plaintext[:5000],  # 長すぎる場合は切り詰め
                        "has_timestamps": has_segments,
                        "segments": segments if has_segments else []
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
                    nouns=proper_nouns
                )
            
            # 処理結果の表示（エラー処理のため省略）
            # ...

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
                
                # ダウンロードボタン - 履歴からも異なる形式でダウンロード可能に
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "テキストを保存", 
                        item["text"], 
                        file_name=f"{item['filename']}_{item['timestamp']}.txt",
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
                            key=f"download_timestamps_{i}"
                        )
                    
                    with col3:
                        srt_content = convert_to_srt(item["segments"])
                        st.download_button(
                            "字幕ファイル (.srt)",
                            srt_content,
                            file_name=f"{item['filename']}_{item['timestamp']}.srt",
                            key=f"download_srt_{i}"
                        )
        
        # 履歴クリアボタン
        if st.button("履歴をクリア"):
            st.session_state.transcription_history = []
            st.experimental_rerun()  # 画面を更新
