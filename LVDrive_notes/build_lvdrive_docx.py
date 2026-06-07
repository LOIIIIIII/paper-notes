#!/usr/bin/env python3
from __future__ import annotations

import html
import zipfile
from pathlib import Path


OUT = Path(__file__).resolve().parent / "LVDrive论文精读笔记.docx"


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def p(text: str = "", style: str | None = None) -> str:
    ppr = f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>" if style else ""
    return f"<w:p>{ppr}<w:r><w:t xml:space=\"preserve\">{esc(text)}</w:t></w:r></w:p>"


def bullet(text: str) -> str:
    return (
        "<w:p><w:pPr><w:pStyle w:val=\"ListParagraph\"/>"
        "<w:numPr><w:ilvl w:val=\"0\"/><w:numId w:val=\"1\"/></w:numPr></w:pPr>"
        f"<w:r><w:t xml:space=\"preserve\">{esc(text)}</w:t></w:r></w:p>"
    )


def code(text: str) -> str:
    runs = []
    for line in text.splitlines():
        runs.append(
            "<w:p><w:pPr><w:pStyle w:val=\"Code\"/></w:pPr>"
            f"<w:r><w:t xml:space=\"preserve\">{esc(line)}</w:t></w:r></w:p>"
        )
    return "".join(runs)


def table(rows: list[list[str]], widths: list[int]) -> str:
    grid = "".join(f"<w:gridCol w:w=\"{w}\"/>" for w in widths)
    trs = []
    for r, row in enumerate(rows):
        cells = []
        for text, width in zip(row, widths):
            fill = "<w:shd w:fill=\"F2F4F7\"/>" if r == 0 else ""
            cells.append(
                "<w:tc><w:tcPr>"
                f"<w:tcW w:w=\"{width}\" w:type=\"dxa\"/>"
                f"{fill}"
                "</w:tcPr>"
                f"{p(text)}"
                "</w:tc>"
            )
        trs.append("<w:tr>" + "".join(cells) + "</w:tr>")
    return (
        "<w:tbl><w:tblPr><w:tblStyle w:val=\"TableGrid\"/>"
        "<w:tblW w:w=\"9360\" w:type=\"dxa\"/>"
        "<w:tblLook w:firstRow=\"1\" w:noHBand=\"0\" w:noVBand=\"1\"/>"
        "</w:tblPr><w:tblGrid>"
        + grid
        + "</w:tblGrid>"
        + "".join(trs)
        + "</w:tbl>"
    )


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="160"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="36"/><w:b/><w:color w:val="0B2545"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="180"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="22"/><w:color w:val="555555"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="320" w:after="160"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="32"/><w:b/><w:color w:val="2E74B5"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="26"/><w:b/><w:color w:val="2E74B5"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="160" w:after="80"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="24"/><w:b/><w:color w:val="1F4D78"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph">
    <w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:ind w:left="720" w:hanging="360"/><w:spacing w:after="80" w:line="280" w:lineRule="auto"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Code">
    <w:name w:val="Code"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="40"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="Microsoft YaHei"/><w:sz w:val="20"/><w:color w:val="333333"/></w:rPr>
  </w:style>
  <w:style w:type="table" w:styleId="TableGrid">
    <w:name w:val="Table Grid"/>
    <w:tblPr><w:tblBorders>
      <w:top w:val="single" w:sz="4" w:color="D0D7DE"/>
      <w:left w:val="single" w:sz="4" w:color="D0D7DE"/>
      <w:bottom w:val="single" w:sz="4" w:color="D0D7DE"/>
      <w:right w:val="single" w:sz="4" w:color="D0D7DE"/>
      <w:insideH w:val="single" w:sz="4" w:color="D0D7DE"/>
      <w:insideV w:val="single" w:sz="4" w:color="D0D7DE"/>
    </w:tblBorders><w:tblCellMar>
      <w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>
      <w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/>
    </w:tblCellMar></w:tblPr>
  </w:style>
</w:styles>"""


def numbering_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="0">
    <w:multiLevelType w:val="singleLevel"/>
    <w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>"""


def document_xml() -> str:
    body: list[str] = []
    body.append(p("LVDrive 论文精读笔记", "Title"))
    body.append(p("Latent Future Visual Representation Learning for VLA Autonomous Driving", "Subtitle"))
    body.append(p("本笔记基于论文正文与当前对话精读内容整理，重点覆盖方法机制、实验结论、消融解释和复现启发。"))

    body.append(p("一句话总结", "Heading1"))
    body.append(p("LVDrive 不直接生成未来 RGB 图像，而是在 latent space 中预测未来视觉语义表示，并通过两阶段轨迹解码让这些未来语义显式参与轨迹精修，从而提升 VLA 自动驾驶的 closed-loop planning performance。"))

    body.append(p("论文要解决的问题", "Heading1"))
    for item in [
        "监督稀疏：标准 VLA 主要用 action / trajectory labels 训练，难以充分学习道路结构、目标交互和未来动态。",
        "像素重建偏离规划目标：高保真未来图像会消耗模型容量，规划更需要语义和动态关系。",
        "自回归生成太慢：逐 token 生成未来图像和动作会带来很高推理成本。",
        "未来视觉特征利用不足：已有方法常把未来视觉预测当辅助任务，而没有显式接入 trajectory decoding。",
    ]:
        body.append(bullet(item))

    body.append(p("方法概览", "Heading1"))
    body.append(code("多视角当前/历史图像 + 文本指令\n        ↓\nVision Encoder + LLM/VLA reasoning\n        ↓\nfuture visual placeholder hidden states + planning token\n        ↓\ncoarse trajectory → future-aware trajectory refiner\n        ↓\nfinal trajectory"))

    body.append(p("关键机制", "Heading1"))
    body.append(p("1. Latent Future Visual Representation Learning", "Heading2"))
    body.append(p("LVDrive 为未来帧设置 <img_start>、<img_i>、<img_end> 等 placeholder tokens。每个 <img_i> 在 LLM 最后一层有一个 hidden state；第 t+j 个未来帧的 N 个 hidden states 构成 H_{t+j} ∈ R^{N × D}。"))
    body.append(p("H_{t+j} 不是 frozen Vision Backbone 的输出，而是模型基于当前/历史图像和文本指令推理出的未来视觉表示。它经过 VISθ 解码为 V_{t+j}，再与真实未来帧经 frozen Vision Backbone 得到的 teacher feature 对齐。"))
    body.append(p("2. Lce 与 Lvis 的区别", "Heading2"))
    body.append(p("Lce 是特殊 placeholder tokens 的 cross-entropy loss，负责让 LLM 稳定输出正确格式；Lvis 是语义监督，负责让 placeholder hidden states 真正包含未来视觉语义。"))
    body.append(code("Lce：教模型画出表格栏位\nLvis：教模型在栏位里填对内容"))
    body.append(p("3. Two-stage Trajectory Decoding", "Heading2"))
    body.append(p("第一阶段用 planning embedding 通过 VAE-based generative planner 生成 coarse trajectory；第二阶段用 trajectory refiner 让 ego motion queries 显式 cross-attend future visual embeddings，输出 fine-grained final trajectory。"))

    body.append(p("训练目标", "Heading1"))
    body.append(code("L = Lvis + Lplan + Lplan_r + Lqt + Lce"))
    for item in [
        "Lvis：future visual feature prediction loss，由 cosine similarity 和 L1 loss 组成。",
        "Lplan：coarse trajectory 的规划损失，包括 MSE、boundary loss、collision loss。",
        "Lplan_r：final trajectory 的规划损失。",
        "Lqt：结构化多视角特征提取损失。",
        "Lce：特殊 placeholder tokens 的生成格式监督。",
    ]:
        body.append(bullet(item))

    body.append(p("主实验结果", "Heading1"))
    body.append(table([
        ["Method", "DS", "SR", "Avg. L2"],
        ["ORION", "77.74", "54.62%", "0.68"],
        ["UniDrive-WM-AR", "79.22", "56.36%", "0.64"],
        ["UniDrive-WM-AR+Diff", "79.31", "56.42%", "0.63"],
        ["LVDrive", "80.71", "58.26%", "0.63"],
    ], [3200, 1600, 1600, 1600]))
    body.append(p("LVDrive 在 Bench2Drive closed-loop evaluation 上取得最高 DS 和 SR。它的 open-loop L2 不是全表最低，因此应重点表述为 closed-loop 性能更强，而不是所有指标全面领先。"))

    body.append(p("Multi-Ability 结果", "Heading1"))
    body.append(table([
        ["Skill", "LVDrive"],
        ["Merging", "39.74"],
        ["Overtaking", "68.89"],
        ["Emergency Brake", "71.67"],
        ["Give Way", "20.00"],
        ["Traffic Sign", "74.21"],
        ["Mean", "54.90"],
    ], [4200, 2600]))
    body.append(p("Give Way 表现很弱。论文解释是该场景常需要对后方 emergency vehicle 让行，而 LVDrive 的 future prediction 主要面向 front-view，导致后方交互能力不足。"))

    body.append(p("消融实验", "Heading1"))
    body.append(table([
        ["Variant", "Design", "DS", "SR"],
        ["Mbase", "action-only baseline", "65.25", "4/10"],
        ["Mvis", "add latent future prediction", "66.31", "3/10"],
        ["Mone", "one-stage fusion", "60.43", "3/10"],
        ["LVDrive", "two-stage decoding", "82.39", "7/10"],
    ], [2200, 3600, 1200, 1200]))
    body.append(p("简单加入 latent future prediction 并不稳定；one-stage 直接融合会干扰 motion feature learning；two-stage decoding 先稳定动作特征，再用未来语义精修轨迹，因此提升最大。"))

    body.append(p("视觉监督 backbone 消融", "Heading2"))
    body.append(table([
        ["Variant", "Vision Supervision", "Feature Dim.", "DS", "SR"],
        ["Mbase", "-", "-", "65.25", "4/10"],
        ["M1", "Internal Vision Enc.", "1024", "65.42", "4/10"],
        ["M2", "MoVQGAN", "4", "59.91", "3/10"],
        ["M3", "DINOv3-Large", "1024", "71.72", "5/10"],
        ["LVDrive", "VQGAN-ImageNet", "256", "82.39", "7/10"],
    ], [1500, 3000, 1700, 1000, 1000]))
    body.append(p("teacher backbone 的选择非常关键。VQGAN-ImageNet 的 256 维 latent 在该框架中效果最好；DINOv3 有提升但可能引入过多冗余信息。"))

    body.append(p("推理速度", "Heading1"))
    body.append(table([
        ["Variant", "Inference Time"],
        ["Mbase", "0.93s"],
        ["MAR autoregressive baseline", "36.62s"],
        ["LVDrive", "2.03s"],
    ], [4200, 2600]))
    body.append(p("LVDrive 比 Mbase 慢约 2 倍，但比等长自回归视觉/动作 token 生成快一个数量级以上。效率优势来自 pre-filled placeholder tokens 和 single forward parallel decoding。"))

    body.append(p("局限与疑问", "Heading1"))
    for item in [
        "Front-view bias：只预测前视未来场景会削弱后方交互能力，Give Way 结果已经暴露该问题。",
        "训练成本高：论文使用 32 张 NVIDIA H20 96GB 训练 6 epochs，完整复现资源压力较大。",
        "Dev10 消融规模小：核心 ablation 在 10 条路线的 Dev10 上做，统计稳定性有限。",
        "Teacher backbone 依赖强：不同视觉监督信号对性能影响很大。",
        "语言监督未充分探索：论文主要利用 LLM reasoning space，没有深入研究语言监督如何增强视觉/动作表示学习。",
    ]:
        body.append(bullet(item))

    body.append(p("对普通课题组的启发", "Heading1"))
    body.append(p("LVDrive 最值得借鉴的不是大算力，而是机制：未来信息不必生成像素图像；latent supervision 可能比 image reconstruction 更适合 planning；future feature 应该显式进入 trajectory decoding。"))
    for item in [
        "冻结大模型，只训练 adapter、LoRA、trajectory head 或 refiner。",
        "用 DINO、VQGAN、CLIP、EVA 等现成 backbone 做 teacher。",
        "在传统 E2E planner 上加入轻量 future latent prediction。",
        "用 Dev10、CARLA 子集或 Bench2Drive 小场景做机制验证。",
        "研究多视角 future latent 对 Give Way、Merging、Overtaking 等技能的影响。",
    ]:
        body.append(bullet(item))

    body.append(p("阅读结论", "Heading1"))
    body.append(p("LVDrive 把 world modeling 从“生成未来图像”转成“学习未来语义 latent”，并让这个 latent 直接服务轨迹生成。实验说明未来视觉监督对 VLA 自动驾驶有帮助，但也表明辅助任务必须和 action space 谨慎对齐；two-stage decoding 是性能提升的关键。"))

    sect = '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
        'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
        'mc:Ignorable="w14 wp14"><w:body>'
        + "".join(body)
        + sect
        + "</w:body></w:document>"
    )


def write_docx() -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("word/document.xml", document_xml())
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/numbering.xml", numbering_xml())


if __name__ == "__main__":
    write_docx()
    print(OUT)
