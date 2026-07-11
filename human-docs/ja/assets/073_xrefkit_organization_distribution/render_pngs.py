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
        "question": "実行証跡から、組織の知識と手順をどう改善するのですか。",
        "title": "Evidenceを、人間が改善判断を行うための入力にします。",
        "copy": "利用したXID、成果物、判断、unknown、結果を確認し、人間がKnowledge、Skill、routing、受入条件の改訂要否を判断します。",
        "cards": [("Evidence", "実行で使った知識、判断、未解決事項、結果を確認します。"), ("人間による評価", "不足、過剰、誤選択、受入条件の妥当性を判断します。"), ("改訂候補", "Knowledge、Skill、routing、受入条件へ変更を戻します。")],
        "takeaway": "AIが組織ルールを自動更新せず、改訂責任は人間に残します。",
    },
    {
        "name": "02_unit",
        "question": "改訂したKnowledgeやSkillは、そのまま公開するのですか。",
        "title": "改訂内容を検証し、承認された版だけを配布対象にします。",
        "copy": "参照整合性、必須項目、互換性、契約内容を検証し、人間が承認した正本をバージョン化します。",
        "cards": [("改訂", "人間が変更内容と責任範囲を確定します。"), ("検証", "XID参照、契約、版、互換性を決定的に確認します。"), ("承認", "公開可能な次の版として人間が受け入れます。")],
        "takeaway": "Evidenceから配布までの間に、人間の評価・改訂・承認を置きます。",
    },
    {
        "name": "03_package",
        "question": "これらの配布資産は、どこにまとめられるのですか。",
        "title": "xrefkitパッケージに、実行、MCP、ツール、責務資産をまとめます。",
        "copy": "Pythonパッケージを共通の配布単位とし、実行管理、参照解決、MCP接続、クライアント用ツールを同じ版として扱います。",
        "cards": [("実行管理", "目標、責務実行、記録、終了判定を扱います。"), ("MCP", "起動情報、責務定義、XID本文を配信します。"), ("ツールと責務", "決定的コマンドと配布対象の責務資産を持ちます。")],
        "takeaway": "分割された機能を、一つの版を持つPythonパッケージとして配布します。",
    },
    {
        "name": "04_generation",
        "question": "更新途中の資産が混ざることはありませんか。",
        "title": "実行時資産は世代単位で公開し、current.jsonが現在世代を示します。",
        "copy": "新しい世代を完成させてから参照先を切り替えるため、利用側が複数世代の契約や知識を混ぜて読むことを防ぎます。",
        "cards": [("世代", "契約本文、必須XID、マニフェストを一つの世代にまとめます。"), ("原子的公開", "世代を完成させた後で現在世代の参照先を切り替えます。"), ("利用契約", "正式な利用側はcurrent.jsonが指す世代を必ず読みます。")],
        "takeaway": "配布資産の一貫性は、世代単位の公開と正式な参照点で守ります。",
    },
    {
        "name": "05_providers",
        "question": "利用環境が違っても、同じXIDを参照できますか。",
        "title": "同じXIDを、リポジトリ、導入済みパッケージ、MCPから解決します。",
        "copy": "利用場所に応じて参照元を切り替えても、XIDを主キーとする契約は変えません。競合する本文を黙って優先することもありません。",
        "cards": [("リポジトリ", "開発時は管理中の正本を直接解決します。"), ("導入済みパッケージ", "組み込まれた世代の資産から解決します。"), ("MCP", "外部の利用環境へ必要な本文だけを返します。")],
        "takeaway": "参照元が変わってもXIDの意味は同じであり、競合は明示的に扱います。",
    },
    {
        "name": "06_mcp",
        "question": "MCPサーバーが、責務の作業まで実行するのですか。",
        "title": "MCPは配布と参照解決を担い、作業実行はクライアント側が行います。",
        "copy": "サーバーは起動契約、責務定義、XID本文、実行用資産を提供します。AIの作業とクライアント用コマンドの実行主体にはなりません。",
        "cards": [("起動", "起動情報と読込み順をクライアントへ返します。"), ("参照解決", "要求された責務定義とXID本文を返します。"), ("相関", "実行識別子を結び、配信したXIDを観測可能にします。")],
        "takeaway": "MCPを薄い配布境界に保ち、実行責任をクライアントから奪いません。",
    },
    {
        "name": "07_bootstrap",
        "question": "クライアントは、受け取った配布物をそのまま信頼するのですか。",
        "title": "取得後に、ハッシュ、版、互換性を確認してから利用します。",
        "copy": "パッケージの導入または必要資産の配置後に、内容ハッシュと版の条件を確認します。ネットワーク経由の信頼は配置環境の責任として扱います。",
        "cards": [("導入", "Pythonパッケージとして導入するか、必要資産を配置します。"), ("整合性", "マニフェスト、ハッシュ、版、拡張条件を確認します。"), ("信頼境界", "通信、認証、配布元の信頼を配置環境で管理します。")],
        "takeaway": "配布できることと信頼できることを分け、利用前の検証を要求します。",
    },
    {
        "name": "08_conclusion",
        "question": "配布された次の版は、どこへ戻るのですか。",
        "title": "一つの管理済み正本を、同じ契約で複数のAI利用環境へ届けられます。",
        "copy": "正本の更新責任をリポジトリへ残したまま、利用側は環境に合う経路から同じ責務定義、必須知識、実行契約を取得できます。",
        "cards": [("一つの正本", "知識と手順の変更元をリポジトリへ集約します。"), ("複数の経路", "直接利用、パッケージ導入、MCP配信を選べます。"), ("同じ契約", "経路が変わっても実行境界とXIDの意味を保ちます。")],
        "takeaway": "改善と配布の終点は、次の業務実行ループの開始です。",
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
    draw.text((56, 44), "組織配布", font=font(24, bold=True), fill=BLUE)
    draw_multiline(draw, (56, 86), title_text, text_font=font(46, bold=True), fill=INK, max_width=1120, line_gap=4)
    draw.rounded_rectangle((1310, 42, 1528, 92), radius=24, fill=PANEL, outline=LINE, width=2)
    draw.text((1360, 53), "XRefKit", font=font(26, bold=True), fill=INK)


def render_question(slide: dict[str, object]) -> None:
    image, draw = base_image()
    draw_header(draw, title_text="管理された知識と手順を組織へ届けます。")
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
