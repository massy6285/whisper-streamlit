import time
import random
import openai
from openai.error import RateLimitError

def transcribe_with_exponential_backoff(audio_file, model="whisper-1", max_retries=5, base_delay=1.0):
    """
    audio_file: ファイルオブジェクト
    model: Whisper のモデル名
    max_retries: 最大リトライ回数
    base_delay: 待ち時間のベース（秒）
    """
    for retry in range(1, max_retries + 1):
        try:
            # ここで実際の API 呼び出し
            return openai.Audio.transcribe(model, audio_file)
        except RateLimitError as e:
            # 再試行するか、最後のリトライか
            if retry == max_retries:
                print(f"リトライ上限({max_retries})に到達。エラーを再送出します。")
                raise

            # 指数バックオフ＋ジッター
            #  例: base_delay * 2^(retry-1) の範囲でランダム待機
            exp_delay = base_delay * (2 ** (retry - 1))
            jitter = random.uniform(0, exp_delay)
            wait_time = jitter

            print(f"[Retry {retry}/{max_retries}] RateLimitError を検知 → {wait_time:.1f}s 待機して再試行…")
            time.sleep(wait_time)

    # ここには到達しない想定
    raise RuntimeError("予期せぬエラー：transcribe_with_exponential_backoff が終了しました")

# 使い方の例
with open("input.wav", "rb") as f:
    result = transcribe_with_exponential_backoff(f)
    print(result["text"])
