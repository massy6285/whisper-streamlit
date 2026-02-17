import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="プリアサイン依頼フォーム", page_icon="📝", layout="centered")

st.title("📝 プリアサイン依頼フォーム")
st.caption("入力内容から依頼文を生成し、クリップボードコピーや推敲用プロンプト作成ができます。")

html_app = r"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>プリアサイン依頼フォーム</title>
    <style>
        :root {
            --primary: #4361ee;
            --primary-light: #5c7cfa;
            --accent: #f72585;
            --text-dark: #2b2d42;
            --text-light: #6c757d;
            --background: #f8f9fa;
            --card-bg: #ffffff;
            --success: #06d6a0;
            --border-radius: 12px;
            --transition-fast: 0.2s ease;
            --gap: 1rem;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 1rem;
            font-family: system-ui, 'SF Pro Display', sans-serif;
            background: var(--background);
            color: var(--text-dark);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
        }
        .container {
            background: var(--card-bg);
            border-radius: var(--border-radius);
            box-shadow: 0 4px 16px rgba(67,97,238,0.1);
            width: 100%;
            max-width: 720px;
            padding: 2rem;
            margin: 0 auto;
        }
        .header-bar {
            height: 6px;
            background: linear-gradient(90deg,var(--primary),var(--accent));
            border-radius: var(--border-radius) var(--border-radius) 0 0;
            margin: -2rem -2rem 1.5rem;
        }
        h2 {
            margin: 0 0 1.5rem;
            font-size: 1.75rem;
            text-align: center;
            color: var(--primary);
        }
        .form-row { display: flex; flex-direction: column; margin-bottom: var(--gap); }
        .form-row label { margin-bottom: 0.5rem; font-weight: 600; }
        .form-row input, .form-row textarea {
            padding: 0.75rem 1rem;
            border: 1px solid #dee2e6;
            border-radius: var(--border-radius);
            font-size: 1rem;
            transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
            background: var(--card-bg);
        }
        .form-row textarea { resize: vertical; }
        .form-row input:focus, .form-row textarea:focus {
            outline: none;
            border-color: var(--primary-light);
            box-shadow: 0 0 0 3px rgba(67,97,238,0.15);
        }
        fieldset {
            border: 1px solid #dee2e6;
            border-radius: var(--border-radius);
            padding: 1rem;
            margin-bottom: var(--gap);
            background: rgba(230,230,250,0.3);
        }
        legend { padding: 0 0.5rem; font-weight: 600; color: var(--text-dark); }
        .checkbox-group { display: flex; flex-wrap: wrap; gap: 0.5rem 1rem; }
        .checkbox-group label { display: flex; align-items: center; cursor: pointer; font-size: 0.95rem; }
        .checkbox-group input[type="checkbox"] {
            appearance: none;
            width: 1.25rem;
            height: 1.25rem;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            margin-right: 0.5rem;
            position: relative;
            transition: background var(--transition-fast), border-color var(--transition-fast);
        }
        .checkbox-group input[type="checkbox"]:checked {
            background: var(--primary);
            border-color: var(--primary);
        }
        .checkbox-group input[type="checkbox"]:checked::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 6px;
            width: 4px;
            height: 8px;
            border: solid white;
            border-width: 0 2px 2px 0;
            transform: rotate(45deg);
        }
        .button-group {
            display: grid;
            grid-template-columns: repeat(auto-fit,minmax(140px,1fr));
            gap: var(--gap);
            margin-top: var(--gap);
        }
        .button-group button {
            padding: 0.75rem;
            border: none;
            border-radius: var(--border-radius);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform var(--transition-fast), box-shadow var(--transition-fast);
        }
        .button-group .primary { background: var(--primary); color: #fff; }
        .button-group .secondary { background: #fff; color: var(--primary); border: 1px solid var(--primary); }
        .button-group button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(67,97,238,0.15);
        }
        .button-group button:active { transform: translateY(0); }
        .copy-message {
            margin-top: 1rem;
            text-align: center;
            color: var(--success);
            font-weight: 600;
            display: none;
        }
        .output {
            margin-top: 2rem;
            padding: 1rem;
            background: #f1f3f5;
            border: 1px solid #dee2e6;
            border-radius: var(--border-radius);
            font-family: monospace;
            white-space: pre-wrap;
            position: relative;
            min-height: 10rem;
        }
        .output::before {
            content: '生成された依頼文';
            position: absolute;
            top: -0.75rem;
            left: 1rem;
            background: #f1f3f5;
            padding: 0 0.5rem;
            font-size: 0.75rem;
            color: var(--text-light);
        }
        @media(max-width:480px){ body{padding:0.5rem;} .container{padding:1.25rem;} }
    </style>
</head>
<body>
<div class="container">
    <div class="header-bar"></div>
    <h2>プリアサイン依頼フォーム</h2>
    <form id="preassign-form">
        <div class="form-row"><label for="eu">E/U (エンドユーザー):</label><input type="text" id="eu" name="eu" placeholder="エンドユーザー名" required></div>
        <div class="form-row"><label for="ptn">PTN (パートナー):</label><input type="text" id="ptn" name="ptn" placeholder="パートナー名" required></div>
        <div class="form-row"><label for="product">検討中製品:</label><input type="text" id="product" name="product" placeholder="製品名を入力"></div>
        <div class="form-row"><label for="currentProduct">利用中製品:</label><input type="text" id="currentProduct" name="currentProduct" placeholder="現在利用中の製品"></div>
        <div class="form-row"><label for="details">詳細:</label><textarea id="details" name="details" placeholder="案件の詳細情報を入力してください" rows="6"></textarea></div>
        <fieldset><legend>支援内容（該当するものをチェック）</legend>
            <div class="checkbox-group">
                <label><input type="checkbox" name="support" value="打ち合わせへの同席" checked>打ち合わせへの同席</label>
                <label><input type="checkbox" name="support" value="技術QA" checked>技術QA</label>
                <label><input type="checkbox" name="support" value="試使用フォロー" checked>試使用フォロー</label>
                <label><input type="checkbox" name="support" value="提案資料作成支援">提案資料作成支援</label>
                <label><input type="checkbox" name="support" value="製品比較">製品比較</label>
                <label><input type="checkbox" name="support" value="ライセンス見積支援">ライセンス見積支援</label>
            </div>
        </fieldset>
        <div class="button-group">
            <button type="button" class="primary" id="generateBtn">依頼文を生成＆コピー</button>
            <button type="button" class="secondary" id="editBtn">ChatGPTで推敲</button>
        </div>
        <div class="copy-message" id="copyMessage" aria-live="polite">✓ テキストをクリップボードにコピーしました</div>
        <div class="output" id="output" aria-live="polite"></div>
    </form>
</div>
<script>
let lastGeneratedText = '';
document.getElementById('generateBtn').addEventListener('click', ()=>{
    const data = new FormData(document.getElementById('preassign-form'));
    const supports = data.getAll('support');
    const supportText = supports.length ? supports.map(s=>`・${s}`).join('\n') : '（特になし）';
    lastGeneratedText =
        `お疲れ様です。第３営業部吉本です。\n\n`+
        `下記案件にて、プリアサインをお願いできますでしょうか。\n\n`+
        `【 案件概要 】\nE/U: ${data.get('eu')}\nPTN: ${data.get('ptn')}\n検討中製品: ${data.get('product')}\n利用中製品: ${data.get('currentProduct')}\n詳細: \n${data.get('details')}\n\n`+
        `【 支援内容 】\n${supportText}\n\n`+
        `アサイン後、個別MTGやチャットで詳細連携いたします。\nよろしくお願いいたします。`;

    document.getElementById('output').innerText = lastGeneratedText;
    navigator.clipboard.writeText(lastGeneratedText).then(()=>{
        const msg = document.getElementById('copyMessage');
        msg.style.display = 'block';
        setTimeout(()=>msg.style.display='none',3000);
    });
});

document.getElementById('editBtn').addEventListener('click', ()=>{
    if(!lastGeneratedText) {
        alert('先に依頼文を生成してください。');
        return;
    }
    const prompt =
`### 指示
あなたは優秀な営業アシスタントです。
今から渡す依頼文書のうち「詳細」セクションを洗練させてください。
「詳細」のみ変更してください。
出力するさいは、「詳細」以外のセクションとマージして出力してください。
ルール: です・ます調、フォーマル度7、箇条書きにできる部分は箇条書きで。

### 引数
${lastGeneratedText}`;

    navigator.clipboard.writeText(prompt).then(()=>{
        alert('推敲用プロンプトをコピーしました。ChatGPTに貼り付けてください。');
        window.open('https://chat.openai.com/', '_blank');
    });
});
</script>
</body>
</html>
"""

components.html(html_app, height=1180, scrolling=True)
