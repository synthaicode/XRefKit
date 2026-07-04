from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
W, H = 1600, 1000
BG = "#f7f9fc"
INK = "#172033"
MUTED = "#586174"
LINE = "#c7d0dd"
BLUE = "#2563eb"
GREEN = "#15803d"
AMBER = "#b45309"
ROSE = "#be123c"
PURPLE = "#6d28d9"
SLATE = "#334155"
CARD = "#ffffff"


FONT_REGULAR = "C:/Windows/Fonts/BIZ-UDGothicR.ttc"
FONT_BOLD = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, fill: str = INK, bold: bool = False) -> None:
    draw.text(xy, value, font=font(size, bold), fill=fill)


def wrapped(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], value: str, size: int, fill: str = INK, bold: bool = False, width: int = 26, line_gap: int = 8) -> None:
    x, y, x2, _ = box
    max_chars = max(8, int((x2 - x) / (size * 0.55)))
    max_chars = min(width, max_chars)
    for line in wrap(value, max_chars):
        draw.text((x, y), line, font=font(size, bold), fill=fill)
        y += size + line_gap


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, body: list[str], color: str = BLUE) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=18, fill=CARD, outline=LINE, width=2)
    draw.rectangle((x1, y1, x1 + 12, y2), fill=color)
    wrapped(draw, (x1 + 30, y1 + 24, x2 - 24, y2), title, 30, INK, True, width=18)
    y = y1 + 96
    for item in body:
        draw.ellipse((x1 + 32, y + 8, x1 + 42, y + 18), fill=color)
        wrapped(draw, (x1 + 56, y, x2 - 24, y2), item, 23, MUTED, False, width=25, line_gap=7)
        y += 78


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = SLATE, width: int = 5) -> None:
    draw.line((start, end), fill=color, width=width)
    ex, ey = end
    sx, sy = start
    if ex >= sx:
        pts = [(ex, ey), (ex - 18, ey - 12), (ex - 18, ey + 12)]
    else:
        pts = [(ex, ey), (ex + 18, ey - 12), (ex + 18, ey + 12)]
    draw.polygon(pts, fill=color)


def header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    text(draw, (64, 42), title, 46, INK, True)
    wrapped(draw, (66, 112, 1500, 170), subtitle, 24, MUTED, False, width=80)
    draw.line((64, 174, 1536, 174), fill=LINE, width=2)


def footer(draw: ImageDraw.ImageDraw, note: str) -> None:
    draw.rounded_rectangle((64, 920, 1536, 958), radius=12, fill="#eaf1fb", outline="#c7d8f4")
    text(draw, (84, 926), note, 20, BLUE, True)


def save(name: str, title: str, subtitle: str, cards: list[tuple[str, list[str], str]], note: str, arrows: bool = True) -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    header(draw, title, subtitle)
    count = len(cards)
    gap = 34
    left = 64
    top = 230
    card_w = int((W - 128 - gap * (count - 1)) / count)
    card_h = 610
    boxes = []
    for i, (ctitle, body, color) in enumerate(cards):
        x1 = left + i * (card_w + gap)
        x2 = x1 + card_w
        box = (x1, top, x2, top + card_h)
        boxes.append(box)
        card(draw, box, ctitle, body, color)
    if arrows:
        for a, b in zip(boxes, boxes[1:]):
            arrow(draw, (a[2] + 4, top + card_h // 2), (b[0] - 8, top + card_h // 2))
    footer(draw, note)
    img.save(ROOT / name)


def render() -> None:
    save(
        "01_xrefkit_as_ai_agent_os.png",
        "XRefKit: AIに業務を依頼するための基盤",
        "AI作業の問題を、業務単位・実行制御・観測改善の3層で扱う。",
        [
            ("AI作業で起きる問題", ["途中終了", "推測で補完", "判断の揺れ", "引継ぎ不能"], ROSE),
            ("XRefKitの制御", ["Skillを選ぶ", "KnowledgeをXIDで読む", "unknownを記録", "verify / closeで止める"], BLUE),
            ("業務単位", ["Business Pack", "Skill", "Knowledge", "Handoff", "業務固有の品質観点"], GREEN),
            ("基盤側", ["workflow protocol", "semantic routing", "Guard", "Quality Gate", "Operational Memory / Dashboard"], PURPLE),
        ],
        "現行モデル: Flow / Capability定義層は使わず、Skill triad + routing + workflow protocolで制御する。",
    )
    save(
        "02_business_pack_explained.png",
        "Business Pack Explained",
        "ひとつの業務を、AIへまとめて渡せる再利用単位として束ねる。",
        [
            ("人間の依頼", ["業務を一件として渡す", "Skill単位の細かい指示を減らす", "人間判断点だけ残す"], AMBER),
            ("Packが持つもの", ["job-specific Skills", "判断Knowledge", "handoff points", "業務固有の品質観点"], GREEN),
            ("OS coreが持つもの", ["runtime control", "guard", "routing", "closure", "audit"], BLUE),
            ("実行結果", ["成果物", "judgment / evidence", "unknown / risk", "next handoff"], PURPLE),
        ],
        "PackはSkill集だけではない。作業・判断根拠・受け渡し境界を束ねる。",
    )
    save(
        "03_flow_skill_knowledge_handoff.png",
        "Skill / Knowledge / Handoff と進行制御",
        "実行手順、判断根拠、受け渡し、進行制御を分ける。",
        [
            ("Intent + State", ["目的と現在状態", "semantic routingでSkill候補を選ぶ", "preconditionsを確認"], AMBER),
            ("Skill", ["procedure", "capability / tuning / responsibility", "knowledge_slots", "I/O contract"], BLUE),
            ("Knowledge", ["XIDで取得", "base + local catalog", "必要な断片だけロード", "事実とルールを保持"], GREEN),
            ("Handoff / State", ["成果物", "judgment", "unknown / risk", "次のSkillまたは人間へ渡す"], PURPLE),
        ],
        "決定論はworkflow protocolのverify / closeに置く。Skill内部判断とroutingはgateされる。",
    )
    save(
        "04_code_review_as_split_checks.png",
        "Code Review as Split Checks",
        "レビューを責務別Skillに分け、同じ基準で安定して検出する。",
        [
            ("変更入力", ["要求", "設計", "差分", "XDDP trace"], AMBER),
            ("分割レビュー", ["traceability", "language-specific issues", "system-wide issues", "DB artifacts"], BLUE),
            ("結果統合", ["finding", "risk", "unknown", "evidence", "tradeoff"], GREEN),
            ("人間判断", ["優先順位", "許容tradeoff", "修正方針", "再レビュー指示"], PURPLE),
        ],
        "広いレビューは必要に応じてSubAgentへ分割し、最終判断は人間へ戻す。",
    )
    save(
        "05_execution_outputs_and_followup_work.png",
        "Business Packを実行すると何が出力されるか",
        "回答だけでなく、次作業と観測に使える記録を出す。",
        [
            ("Business Pack実行", ["Skill runtime envelope", "Knowledge解決", "verify", "close"], BLUE),
            ("出力", ["成果物", "execution log", "unknown", "judgment", "evidence", "handoff"], GREEN),
            ("後続作業", ["確認", "差し戻し", "追加調査", "次Skill", "人間判断"], AMBER),
            ("改善入力", ["Operational Memory", "Dashboard", "Skill / Knowledge / Gate改善"], PURPLE),
        ],
        "実行結果は最終回答では終わらず、次状態と改善材料になる。",
    )
    save(
        "06_skill_run_observation_dashboard.png",
        "Skill Run Observation Dashboard",
        "Flowではなく、Skill実行記録を人間が観測するダッシュボード。",
        [
            ("実行記録", ["artifact", "log", "unknown", "judgment", "evidence", "handoff"], BLUE),
            ("Operational Memory", ["何を実行したか", "どの根拠を使ったか", "どこで止まったか"], GREEN),
            ("Dashboard", ["Skill run", "quality gate", "unresolved", "handoff status"], PURPLE),
            ("人間の確認", ["異常検出", "改善判断", "次アクション", "承認 / 差し戻し"], AMBER),
        ],
        "Dashboardは正本知識ではない。観測と改善判断の入口である。",
    )
    save(
        "07_dashboard_observation_and_improvement.png",
        "Dashboardから改善につなげる",
        "観測した実行記録を、管理対象ごとの改善に戻す。",
        [
            ("見るもの", ["どのSkillが動いたか", "どこで止まったか", "unresolved", "quality gate"], BLUE),
            ("判断すること", ["手順不足", "知識不足", "guard不足", "gate不足"], AMBER),
            ("直す対象", ["Skill", "Knowledge", "Guard", "Quality Gate"], GREEN),
            ("再実行", ["同じ目的で再確認", "改善効果を見る", "記録を残す"], PURPLE),
        ],
        "監査で終わらせず、Operational Memoryから改善ループへ接続する。",
    )
    save(
        "08_human_direction_ai_modification_loop.png",
        "人間が方向を決め、AIが修正する",
        "人間は方針と判断点を持ち、AIは具体変更と検証を実行する。",
        [
            ("人間が決める", ["方向性", "優先順位", "許容tradeoff", "承認 / 差し戻し"], AMBER),
            ("AIが変更する", ["Skill修正", "Knowledge追加", "Guard調整", "Quality Gate調整"], BLUE),
            ("検証する", ["fm xref fix", "Skill verify", "テスト", "Dashboard確認"], GREEN),
            ("次の判断へ", ["結果を見る", "未解決を残す", "必要なら再指示"], PURPLE),
        ],
        "AIが方針を独断で決めるのではなく、人間の判断を実装作業へ落とす。",
    )
    save(
        "09_business_pack_reuse.png",
        "Business Packはどう再利用するか",
        "再利用単位を、Skill単体・Knowledge断片・Business Packで分けて考える。",
        [
            ("Skill単体", ["方法を再利用", "triadで責務を固定", "domain corpusは持たない"], BLUE),
            ("Knowledge断片", ["XIDで取得", "ルール / 事実 / 観点", "base + local catalog"], GREEN),
            ("Business Pack", ["業務責務を再利用", "Skill + Knowledge + Handoff", "品質観点を束ねる"], PURPLE),
            ("再利用条件", ["責務が同じ", "handoff境界が保てる", "OS coreを再定義しない"], AMBER),
        ],
        "技術名ではなく、変更影響調査・計画化・QA判定のような業務責務で再利用する。",
    )


if __name__ == "__main__":
    render()
