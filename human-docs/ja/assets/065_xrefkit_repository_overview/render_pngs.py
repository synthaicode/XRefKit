from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(__file__).resolve().parent
SIZE = (1600, 900)
BG = "#F8F9FA"
PANEL = "#FFFFFF"
INK = "#0F172A"
MUTED = "#475569"
LINE = "#DBE3EE"
BLUE = "#2563EB"
BLUE_SOFT = "#EFF6FF"

FONT_BOLD = str(Path("C:/Windows/Fonts/YuGothB.ttc"))
FONT_REG = str(Path("C:/Windows/Fonts/YuGothR.ttc"))

SLIDES = [
    {
        "name": "01_title",
        "question": "AIの特性に応じて分けた解決策は、XRefKitのどこに実装されているのですか。",
        "title": "XRefKitは、問題ごとの解決策をリポジトリ構造として実装します。",
        "copy": "通常のAI利用では、完了、責務、進行、判断材料、接続に別々の問題があります。問題ごとに異なる実装構造を対応させます。",
        "cards": [
            ("完了と責務", "目標の状態管理と責務定義を別々に持ちます。"),
            ("進行と判断材料", "実行管理とXID参照知識を分離します。"),
            ("接続と証拠", "次作業選択と実行記録で、責務間を追跡可能につなぎます。"),
        ],
        "takeaway": "ここからは、なぜ必要かではなく、どこに実装されるかを見ます。",
    },
    {
        "name": "02_not_docs",
        "question": "完了、責務、進行、判断材料、接続は、どの実装構造が担当するのですか。",
        "title": "目標、限定責務、進行、判断材料、接続を別の構造で持ちます。",
        "copy": "一つの万能機能にまとめず、問題ごとの責任境界をパッケージ、責務定義、組織固有知識、実行記録へ対応させます。",
        "cards": [
            ("目標と限定責務", "目標状態は実行管理、担当範囲は責務定義が持ちます。"),
            ("進行と組織固有知識", "作業進行規約は実行記録、判断材料はXID本文が持ちます。"),
            ("次作業選択", "責務一覧と現在状態から、次に必要な責務を選びます。"),
        ],
        "takeaway": "問題と解決策の対応を、そのまま実装境界として保ちます。",
    },
    {
        "name": "03_layers",
        "question": "では、このリポジトリは何をどう分けているのですか。",
        "title": "パッケージ、責務定義、組織固有知識、実行記録、元資料を分けています。",
        "copy": "人向け説明、実行手順、共有知識、実行記録、元資料を混ぜずに置くことで、読む相手と目的を分離します。",
        "cards": [
            ("パッケージ", "xrefkitが実行管理、XID参照解決、ツール一覧、MCP接続を持ちます。"),
            ("責務と知識", "責務定義と組織固有知識をXIDで選択し、必要な本文だけを読みます。"),
            ("証拠と元資料", "元資料と実行記録を分け、根拠、判断、履歴を残します。"),
        ],
        "takeaway": "AI が読むもの、従うもの、残すものを分離するための層構造です。",
    },
    {
        "name": "04_runtime",
        "question": "責務定義があれば、そのまま実行すればいいのではないですか。",
        "title": "作業進行規約を、記録と終了判定を持つ実行管理枠として実装します。",
        "copy": "xrefkit skill runコマンドで責務実行を開始し、作業項目、成果物、懸念事項、役割分離を記録してから閉じます。これが作業途中の終了と作業漏れへの実装です。",
        "cards": [
            ("開始", "定義情報を検証し、実行記録を開いてから作業を始めます。"),
            ("途中", "実行項目、成果物、証拠、未知やリスクを機械可読で残します。"),
            ("終了", "未完了、未記録、未解決の懸念事項があると終了が拒否されます。"),
        ],
        "takeaway": "限定責務と作業進行規約を混ぜず、責務定義と実行管理に分けます。",
    },
    {
        "name": "05_guard",
        "question": "外部入力やコピーした文書で、方針が崩れる心配はありませんか。",
        "title": "文脈方向保護が、下位入力による上位方針の書き換えを防ぎます。",
        "copy": "外部タスク入力、ツール結果、生成物は事実や材料として使えても、意図、権限、手順、範囲、エスカレーション経路までは上書きできません。",
        "cards": [
            ("守るもの", "起動方針、責務契約、作業進行規約などの上位制御です。"),
            ("許すもの", "外部入力は根拠、補足、局所事実として利用できます。"),
            ("防ぐもの", "もっともらしい入力が勝手に目的や責任境界を変えることを防ぎます。"),
        ],
        "takeaway": "情報そのものだけでなく、情報が影響してよい範囲も制御します。",
    },
    {
        "name": "06_handoff",
        "question": "複数 AI や継続作業は、どうやって切れずにつなぐのですか。",
        "title": "引継ぎは会話の雰囲気ではなく、実行履歴と引継ぎ元の終了状態でつなぎます。",
        "copy": "次の起動側は前の実行の終了状態と引継ぎ元を確認してから続行します。だから、前の作業が何を終え、何を残したかを追えます。",
        "cards": [
            ("残すもの", "実行単位、成果物、判断、振り返りに分けて記録を残します。"),
            ("受け取り条件", "前の実行の終了状態と引継ぎ元が確認できなければ継続しません。"),
            ("効く場面", "複数 AI、長い作業、途中再開、レビュー引き継ぎで効きます。"),
        ],
        "takeaway": "継続性は記憶頼みではなく、確認可能な引継ぎ元で作ります。",
    },
    {
        "name": "07_human",
        "question": "実行後に、どの組織固有知識が使われたか確認できますか。",
        "title": "責務実行とMCPを実行識別子で結び、XIDの利用を観測します。",
        "copy": "選択、解決、読込み、適用を分けて記録し、使われなかった知識や不足した知識を改善材料にします。",
        "cards": [
            ("相関", "クライアント実行とMCPアクセスを同じ識別子で結びます。"),
            ("区別", "XIDの選択、解決、読込み、適用を別の記録として残します。"),
            ("改善", "証拠から一覧、責務、組織固有知識の正本を見直します。"),
        ],
        "takeaway": "観測は監査の終点ではなく、次の実行を改善する入力です。",
    },
    {
        "name": "08_conclusion",
        "question": "この実装構造を、組織の利用環境へどう届けるのですか。",
        "title": "XRefKitは、同じ実装構造を組織へ配布するPythonパッケージです。",
        "copy": "問題ごとに分けた解決策を、責務定義、組織固有知識、実行管理、証拠、参照解決として実装し、同じ構造を複数の利用環境へ届けます。",
        "cards": [
            ("リポジトリ", "正本と開発時の実装構造を直接利用します。"),
            ("導入済みパッケージ", "圧縮された必須資産と実行機能を利用します。"),
            ("MCP", "同じ参照解決機構から必要なXID本文を配信します。"),
        ],
        "takeaway": "問題ごとに分けた仕組みを、同じ契約のまま実装・配布することが、この資料の結論です。",
    },
]


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        separator = " " if current else ""
        trial = f"{current}{separator}{word}"
        if draw.textbbox((0, 0), trial, font=text_font)[2] <= max_width:
            current = trial
            continue

        if current:
            lines.append(current)
            current = ""

        if draw.textbbox((0, 0), word, font=text_font)[2] <= max_width:
            current = word
            continue

        for ch in word:
            trial = current + ch
            if draw.textbbox((0, 0), trial, font=text_font)[2] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if not current:
            continue
    if current:
        lines.append(current)
    return lines


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    text_font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int,
) -> int:
    x, y = xy
    lines = wrap(draw, text, text_font, max_width)
    for line in lines:
        draw.text((x, y), line, font=text_font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=text_font)
        y = bbox[3] + line_gap
    return y


def base_image() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", SIZE, BG)
    draw = ImageDraw.Draw(image)
    draw.ellipse((1250, -120, 1680, 240), fill="#DBEAFE")
    return image, draw


def draw_header(draw: ImageDraw.ImageDraw, *, title_text: str) -> None:
    draw.text((56, 44), "リポジトリ概要", font=font(24, bold=True), fill=BLUE)
    draw_multiline(draw, (56, 86), title_text, text_font=font(46, bold=True), fill=INK, max_width=1120, line_gap=4)
    draw.rounded_rectangle((1310, 42, 1528, 92), radius=24, fill=PANEL, outline=LINE, width=2)
    draw.text((1360, 53), "XRefKit", font=font(26, bold=True), fill=INK)


def render_question(slide: dict[str, object]) -> None:
    image, draw = base_image()
    draw_header(draw, title_text="現在の XRefKit を短く説明します。")
    draw.rounded_rectangle((260, 220, 1340, 610), radius=30, fill=PANEL, outline="#BFDBFE", width=3)
    draw.text((320, 270), "問い", font=font(24, bold=True), fill=BLUE)
    draw_multiline(draw, (320, 330), str(slide["question"]), text_font=font(58, bold=True), fill=INK, max_width=960, line_gap=10)
    draw.rectangle((0, 820, 1600, 900), fill=BLUE_SOFT)
    draw.rectangle((0, 820, 1600, 824), fill=BLUE)
    draw.text((56, 842), "視聴者の疑問を先に置き、その次に一つずつ説明します。", font=font(24, bold=True), fill=INK)
    image.save(OUT_DIR / f"{slide['name']}_q.png")


def render_answer(slide: dict[str, object]) -> None:
    image, draw = base_image()
    draw_header(draw, title_text=str(slide["title"]))

    draw.rounded_rectangle((56, 200, 1544, 402), radius=24, fill=PANEL, outline=LINE, width=2)
    draw.text((86, 226), "問い", font=font(22, bold=True), fill=BLUE)
    draw_multiline(draw, (86, 260), str(slide["question"]), text_font=font(24), fill=MUTED, max_width=1380, line_gap=6)
    draw_multiline(draw, (86, 300), str(slide["copy"]), text_font=font(36, bold=True), fill=INK, max_width=1380, line_gap=6)

    card_left = 56
    card_top = 432
    card_width = 468
    gap = 20
    for idx, (tag, text) in enumerate(slide["cards"]):  # type: ignore[index]
        left = card_left + idx * (card_width + gap)
        draw.rounded_rectangle((left, card_top, left + card_width, 720), radius=24, fill=PANEL, outline=LINE, width=2)
        draw.rounded_rectangle((left + 24, card_top + 22, left + 150, card_top + 58), radius=18, fill=BLUE_SOFT)
        draw.text((left + 38, card_top + 29), tag, font=font(18, bold=True), fill=BLUE)
        draw_multiline(draw, (left + 24, card_top + 92), text, text_font=font(24), fill=MUTED, max_width=card_width - 48, line_gap=8)

    draw.rectangle((0, 820, 1600, 900), fill=BLUE_SOFT)
    draw.rectangle((0, 820, 1600, 824), fill=BLUE)
    draw_multiline(draw, (56, 838), str(slide["takeaway"]), text_font=font(24, bold=True), fill=INK, max_width=1480, line_gap=4)
    image.save(OUT_DIR / f"{slide['name']}.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slide in SLIDES:
        render_question(slide)
        render_answer(slide)


if __name__ == "__main__":
    main()
