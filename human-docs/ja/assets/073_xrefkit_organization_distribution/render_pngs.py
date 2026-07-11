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
        "question": "多くの責務実行から、改善すべき実行をどう見つけるのですか。",
        "title": "実行状況ダッシュボードが、改善判断の入口になります。",
        "copy": "状態、closure、unknown、risk、handoff、不足情報を一覧化し、人間が確認対象を絞ります。",
        "cards": [("観測", "work/sessionsの記録を、人間が比較できる状態へまとめます。"), ("境界", "Skill Run Dashboardは観測画面であり、責務実行や自動改訂は行いません。")],
        "screenshot": "dashboard_overview.jpg",
        "takeaway": "最初に全実行を読み込まず、異常と不足が見える実行から確認します。",
    },
    {
        "name": "02_unit",
        "question": "一覧では、どの状態を確認対象にするのですか。",
        "title": "停止、終了確認、品質確認、不足情報から対象を絞ります。",
        "copy": "状態だけで完了を判断せず、終了確認と品質確認、未確認事項、リスク、引継ぎ、不足情報を組み合わせて見ます。",
        "cards": [("進行", "進行中と停止中の状態から、確認すべき実行を見つけます。"), ("完了", "終了済みでも、終了確認と品質確認が妥当かを分けて確認します。"), ("不足", "記録不足は実行結果と分離し、改善用の観測として扱います。")],
        "takeaway": "集計値は結論ではなく、詳細を読む対象を選ぶための入口です。",
    },
    {
        "name": "03_package",
        "question": "一件の責務実行では、何を確認するのですか。",
        "title": "作業、証跡、懸念、終了判定を一件単位で確認します。",
        "copy": "作業項目、成果物、未確認事項、リスク、判断、引継ぎ、進行状態を見て、どこまで実行され、何が残ったかを確認します。",
        "cards": [("実行内容", "作業項目と進行状態から、予定した処理の進み方を確認します。"), ("根拠", "成果物と証跡から、成果と判断根拠を辿ります。"), ("未解決", "懸念と引継ぎから、人間または次のSkillへ戻す事項を確認します。")],
        "takeaway": "AIの完了報告ではなく、構造化された実行記録から状態を判断します。",
    },
    {
        "name": "04_generation",
        "question": "どのKnowledgeが選ばれ、実際に使われたか分かりますか。",
        "title": "実行識別子で記録を結び、XIDの利用段階を分けます。",
        "copy": "利用可能、選択、解決、読込、適用を区別し、選択後に使われなかったKnowledgeを確認します。",
        "cards": [("相関", "同じ実行識別子（run_id）でクライアント記録とMCP監査記録を結びます。"), ("段階", "選択・解決・読込・適用を同じ意味にまとめません。")],
        "screenshot": "dashboard_xid_usage.jpg",
        "takeaway": "不使用XIDだけで削除を決めず、どの段階で止まったかを確認します。",
    },
    {
        "name": "05_providers",
        "question": "改善判断に必要な記録が足りない場合は、どう分かりますか。",
        "title": "不足情報と相関の切れ目を、実行横断で順位付けします。",
        "copy": "実行識別子、routing、XID読込・適用、検索、人間の評価、実行結果、トークン使用量の不足を分けて示します。",
        "cards": [("一件", "選択した実行で欠けている改善材料を確認します。"), ("横断", "複数実行で繰り返す不足を、優先的な改善候補にします。")],
        "screenshot": "dashboard_missing_information.jpg",
        "takeaway": "記録不足を成果物の失敗と混同せず、観測設計の改善対象として扱います。",
    },
    {
        "name": "06_mcp",
        "question": "実行状況ダッシュボードが、KnowledgeやSkillを自動で直すのですか。",
        "title": "観測結果から何を直すかは、人間が判断します。",
        "copy": "繰り返す停止、誤った選択、過不足のあるKnowledge、弱い受入条件を区別し、変更先を決めます。",
        "cards": [("Skill", "手順、責任範囲、handoff、検査項目の不足を直します。"), ("Knowledge・routing", "内容の不足・過剰と選択条件を分けて直します。"), ("受入条件", "完了と判断できない原因がGoal側なら、受入条件へ戻します。")],
        "takeaway": "実行状況ダッシュボードは判断材料を提供し、改訂と承認の責任は人間に残します。",
    },
    {
        "name": "07_bootstrap",
        "question": "判断した改善を、次の版へどう反映するのですか。",
        "title": "正本を改訂し、検証と人間の承認を通して次版にします。",
        "copy": "Knowledge、Skill、routing、受入条件を正本へ戻し、XID参照、契約、版、互換性を決定的に検証します。",
        "cards": [("改訂", "観測と判断根拠を保ったまま、管理中の正本を変更します。"), ("検証", "参照整合性、契約、互換性、パッケージ内容を確認します。"), ("承認", "人間が配布可能な次版として受け入れます。")],
        "takeaway": "観測値から正本を直接書き換えず、改訂・検証・承認を分離します。",
    },
    {
        "name": "08_conclusion",
        "question": "検証された次版は、改善されたとどう確認するのですか。",
        "title": "次版を配布し、次の責務実行を再び観測します。",
        "copy": "パッケージまたはMCPで承認版を届け、同じ観測項目で停止、不足、XID利用、結果の変化を確認します。",
        "cards": [("配布", "版管理されたKnowledge、Skill、契約を利用環境へ届けます。"), ("再実行", "次のGoalで新しい版を使い、同じ責務を実行します。"), ("再観測", "実行状況ダッシュボードで変化を確認し、次の改善判断へ戻します。")],
        "takeaway": "観測、判断、改訂、検証、配布、再観測を一つの改善循環にします。",
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

    screenshot = slide.get("screenshot")
    if screenshot:
        source = Image.open(OUT_DIR / str(screenshot)).convert("RGB")
        source.thumbnail((920, 540))
        shot_left, shot_top = 56, 210
        draw.rounded_rectangle((shot_left - 2, shot_top - 2, shot_left + source.width + 2, shot_top + source.height + 2), radius=10, fill=PANEL, outline=LINE, width=2)
        image.paste(source, (shot_left, shot_top))

        card_left = 1010
        for idx, (tag, text) in enumerate(slide["cards"]):  # type: ignore[index]
            top = 220 + idx * 240
            draw.rounded_rectangle((card_left, top, 1544, top + 210), radius=20, fill=PANEL, outline=LINE, width=2)
            draw.rounded_rectangle((card_left + 22, top + 20, card_left + 180, top + 56), radius=18, fill=BLUE_SOFT)
            draw.text((card_left + 36, top + 27), tag, font=font(18, bold=True), fill=BLUE)
            draw_multiline(draw, (card_left + 22, top + 82), text, text_font=font(23), fill=MUTED, max_width=490, line_gap=8)

        draw.rectangle((0, 820, 1600, 900), fill=BLUE_SOFT)
        draw.rectangle((0, 820, 1600, 824), fill=BLUE)
        draw_multiline(draw, (56, 838), str(slide["takeaway"]), text_font=font(24, bold=True), fill=INK, max_width=1480, line_gap=4)
        image.save(OUT_DIR / f"{slide['name']}.png")
        return

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
