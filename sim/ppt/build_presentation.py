from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DCTERMS_NS = "http://purl.org/dc/terms/"
DCMITYPE_NS = "http://purl.org/dc/dcmitype/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
A16_NS = "http://schemas.microsoft.com/office/drawing/2014/main"

NS = {"p": P_NS, "a": A_NS, "r": R_NS, "cp": CP_NS, "dc": DC_NS}

ET.register_namespace("a", A_NS)
ET.register_namespace("p", P_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("cp", CP_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("dcterms", DCTERMS_NS)
ET.register_namespace("dcmitype", DCMITYPE_NS)
ET.register_namespace("xsi", XSI_NS)
ET.register_namespace("mc", MC_NS)
ET.register_namespace("p14", P14_NS)
ET.register_namespace("a16", A16_NS)


SLIDE_TEXT = {
    1: {
        "Rectangle 10": [
            "Freshness-Aware Unified Speculative Budget Scheduling for SSD",
        ],
        "Rectangle 13": [
            "Ruben | simulator evidence + Qwen3-8B benchmark | 2026-03-17",
        ],
    },
    2: {
        "Title 1": ["Outline"],
        "Content Placeholder 2": [
            "1. Motivation: why linear verifier budgets break under SSD",
            "2. Unified speculative budget formulation",
            "3. Evidence from simulator and real Qwen3-8B runs",
            "4. Calibration roadmap toward real multi-client scheduling",
        ],
    },
    3: {
        "Title 1": ["Motivation and Gap"],
        "Content Placeholder 2": [
            "GoodSpeed and G-FAST model a multi-client, single-verifier system, but still interpret S_i as linear speculative length.",
            "Speculative Speculative Decoding shows one client can spend verifier work over a frontier: deeper, wider, or mixed branch expansion.",
            "Our question is whether cross-client allocation changes once S_i keeps the same symbol but becomes a unified verifier-side speculative budget.",
        ],
    },
    4: {
        "Title 1": ["Problem Framing"],
        "Content Placeholder 2": [
            "Keep the system-level control variable S_i, but reinterpret it as verifier-side speculative budget rather than draft length.",
            "Each client maps S_i into an internal expansion policy over depth, width, and frontier quality xi_i.",
            "Scheduling should maximize fresh accepted utility y_i^SSD, not accepted length under a linear service curve.",
            "Hypothesis: once service semantics change, linear-budget schedulers systematically misallocate verifier compute.",
        ],
    },
    7: {
        "Title 1": ["Conclusion"],
        "Content Placeholder 2": [
            "Verifier compute is the scarce resource, so budget semantics must be modeled on the verifier side.",
            "Under SSD, equal nominal budget can buy very different client-level service depending on frontier state and expansion policy.",
            "The simulator already shows frequent allocation reversals, while real async SSD runs show the regime is worth calibrating, not hand-waving.",
            "The next milestone is calibrated unified scheduling, not yet a claim of production-ready online control.",
        ],
    },
    8: {
        "Title 1": ["Future Directions"],
        "Content Placeholder 2": [
            "Fit simulator service curves from accepted suffix length, cache hit rate, and verifier-side timing metrics.",
            "Use repeat_bench.py to collect repeated runs for k in {4,6,8} and f in {2,3,4} with confidence intervals.",
            "Calibrate frontier state xi_i from hit-heavy versus miss-heavy SSD regimes.",
            "After calibration, test a freshness-aware unified scheduler inside the real SSD runtime.",
        ],
    },
    9: {
        "Content Placeholder 2": [
            "SpecDiff project update",
            "Questions and discussion",
            "Can the structural mismatch signal survive calibration with real SSD metrics?",
        ],
    },
    10: {
        "Title 1": ["References and Thanks"],
        "Content Placeholder 2": [
            "Papers: GoodSpeed: Optimizing Fair Goodput with Adaptive Speculative Decoding in Distributed Edge Inference; Speculative Speculative Decoding.",
            "Project artifacts: paper/idea.md, sim/README.md, sim/guide.md, sim/experiments/repeat_bench.py.",
            "Bench setup: Qwen3-8B target, Qwen3-0.6B draft, 2 x RTX A4500, random prompts, numseqs=32, output_len=128.",
        ],
    },
}


def find_shape(root: ET.Element, name: str) -> ET.Element:
    for shape in root.findall(".//p:sp", NS):
        props = shape.find("./p:nvSpPr/p:cNvPr", NS)
        if props is not None and props.attrib.get("name") == name:
            return shape
    raise KeyError(f"shape not found: {name}")


def replace_text(shape: ET.Element, paragraphs: list[str]) -> None:
    tx_body = shape.find("./p:txBody", NS)
    if tx_body is None:
        tx_body = ET.SubElement(shape, f"{{{P_NS}}}txBody")
        ET.SubElement(tx_body, f"{{{A_NS}}}bodyPr")
        ET.SubElement(tx_body, f"{{{A_NS}}}lstStyle")

    body_pr = tx_body.find("./a:bodyPr", NS)
    lst_style = tx_body.find("./a:lstStyle", NS)
    if body_pr is None:
        body_pr = ET.Element(f"{{{A_NS}}}bodyPr")
    if lst_style is None:
        lst_style = ET.Element(f"{{{A_NS}}}lstStyle")

    for child in list(tx_body):
        tx_body.remove(child)
    tx_body.append(body_pr)
    tx_body.append(lst_style)

    for text in paragraphs:
        p = ET.SubElement(tx_body, f"{{{A_NS}}}p")
        r = ET.SubElement(p, f"{{{A_NS}}}r")
        ET.SubElement(r, f"{{{A_NS}}}rPr", {"lang": "en-US"})
        t = ET.SubElement(r, f"{{{A_NS}}}t")
        t.text = text
        ET.SubElement(p, f"{{{A_NS}}}endParaRPr", {"lang": "en-US"})


def textbox(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    paragraphs: list[str],
    *,
    fill: str | None = None,
    line: str | None = None,
) -> ET.Element:
    sp = ET.Element(f"{{{P_NS}}}sp")

    nv_sp_pr = ET.SubElement(sp, f"{{{P_NS}}}nvSpPr")
    ET.SubElement(nv_sp_pr, f"{{{P_NS}}}cNvPr", {"id": str(shape_id), "name": name})
    c_nv_sp_pr = ET.SubElement(nv_sp_pr, f"{{{P_NS}}}cNvSpPr")
    ET.SubElement(c_nv_sp_pr, f"{{{A_NS}}}spLocks", {"noGrp": "1"})
    ET.SubElement(nv_sp_pr, f"{{{P_NS}}}nvPr")

    sp_pr = ET.SubElement(sp, f"{{{P_NS}}}spPr")
    xfrm = ET.SubElement(sp_pr, f"{{{A_NS}}}xfrm")
    ET.SubElement(xfrm, f"{{{A_NS}}}off", {"x": str(x), "y": str(y)})
    ET.SubElement(xfrm, f"{{{A_NS}}}ext", {"cx": str(cx), "cy": str(cy)})

    if fill is None:
        ET.SubElement(sp_pr, f"{{{A_NS}}}noFill")
    else:
        solid_fill = ET.SubElement(sp_pr, f"{{{A_NS}}}solidFill")
        ET.SubElement(solid_fill, f"{{{A_NS}}}srgbClr", {"val": fill})

    line_elem = ET.SubElement(sp_pr, f"{{{A_NS}}}ln")
    if line is None:
        ET.SubElement(line_elem, f"{{{A_NS}}}noFill")
    else:
        solid_fill = ET.SubElement(line_elem, f"{{{A_NS}}}solidFill")
        ET.SubElement(solid_fill, f"{{{A_NS}}}srgbClr", {"val": line})

    prst = ET.SubElement(sp_pr, f"{{{A_NS}}}prstGeom", {"prst": "rect"})
    ET.SubElement(prst, f"{{{A_NS}}}avLst")

    tx_body = ET.SubElement(sp, f"{{{P_NS}}}txBody")
    ET.SubElement(tx_body, f"{{{A_NS}}}bodyPr", {"wrap": "square"})
    ET.SubElement(tx_body, f"{{{A_NS}}}lstStyle")
    for idx, text in enumerate(paragraphs):
        p = ET.SubElement(tx_body, f"{{{A_NS}}}p")
        if idx > 0:
            ET.SubElement(p, f"{{{A_NS}}}pPr", {"lvl": "0"})
        r = ET.SubElement(p, f"{{{A_NS}}}r")
        attrs = {"lang": "en-US"}
        if idx == 0 and fill is not None:
            attrs["b"] = "1"
        ET.SubElement(r, f"{{{A_NS}}}rPr", attrs)
        t = ET.SubElement(r, f"{{{A_NS}}}t")
        t.text = text
        ET.SubElement(p, f"{{{A_NS}}}endParaRPr", {"lang": "en-US"})

    return sp


def add_slide4_diagram(root: ET.Element) -> None:
    sp_tree = root.find("./p:cSld/p:spTree", NS)
    if sp_tree is None:
        return

    shapes = [
        textbox(
            40,
            "System Sketch Box",
            4940000,
            1540000,
            3300000,
            1100000,
            [
                "System sketch",
                "Verifier budget C -> allocate S_i across clients",
            ],
            fill="F5EEE6",
            line="B35C1E",
        ),
        textbox(
            41,
            "Client Box",
            4940000,
            2770000,
            3300000,
            1180000,
            [
                "Client response",
                "depth / width / mixed frontier expansion",
            ],
            fill="EEF4EA",
            line="557A46",
        ),
        textbox(
            42,
            "Outcome Box",
            4940000,
            4080000,
            3300000,
            1180000,
            [
                "Observed utility",
                "accepted utility depends on frontier state + freshness",
            ],
            fill="EAF1F6",
            line="3F6F8C",
        ),
    ]

    for shape in shapes:
        sp_tree.append(shape)


def add_slide5_content(root: ET.Element) -> None:
    sp_tree = root.find("./p:cSld/p:spTree", NS)
    if sp_tree is None:
        return

    replace_text(find_shape(root, "Title 1"), ["Related Work and Positioning"])
    replace_text(
        find_shape(root, "Content Placeholder 5"),
        [
            "GoodSpeed / G-FAST line",
            "Multi-client, single-verifier scheduling and fair goodput optimization.",
            "Freshness-aware utility is already available at the system level.",
            "But S_i still means linear speculative length in the client service model.",
        ],
    )

    sp_tree.append(
        textbox(
            50,
            "SSD Column",
            4645025,
            1535113,
            4041775,
            3000000,
            [
                "SSD / tree line",
                "Speculative Speculative Decoding uses a frontier rather than one draft chain.",
                "The same verifier work can be spent on depth, width, or mixed branching.",
                "That changes client-level service semantics and motivates unified budget scheduling.",
            ],
        )
    )
    sp_tree.append(
        textbox(
            51,
            "Takeaway Box",
            4645025,
            4700000,
            4041775,
            1100000,
            [
                "Takeaway",
                "Our project sits between these lines: keep GoodSpeed-style scheduling, but replace the linear client service model with SSD-aware unified budget semantics.",
            ],
            fill="F8F4E8",
            line="9D7A31",
        )
    )


def add_slide6_content(root: ET.Element) -> None:
    sp_tree = root.find("./p:cSld/p:spTree", NS)
    if sp_tree is None:
        return

    replace_text(find_shape(root, "Title 1"), ["Evidence So Far"])

    sp_tree.append(
        textbox(
            60,
            "Summary Banner",
            457200,
            1250000,
            8229600,
            800000,
            [
                "Summary",
                "Both the simulator and the real Qwen3-8B runs point in the same direction: verifier-side budget semantics matter.",
            ],
            fill="F3EEE7",
            line="A86A2C",
        )
    )
    sp_tree.append(
        textbox(
            61,
            "Simulator Box",
            457200,
            2300000,
            3900000,
            2900000,
            [
                "Simulator",
                "Baseline utility: unified 70.90 vs linear 70.62, with fairness still about 0.99.",
                "Sweep result: unified wins 60/81 cases; allocation-order reversals also happen in 60/81 cases.",
                "Utility-order reversals are rare at 3/81, so the main signal is structural mismatch.",
                "Representative gain case: budget=14, load=1.30, mix=linear_skewed, utility +3.94.",
            ],
        )
    )
    sp_tree.append(
        textbox(
            62,
            "Real Bench Box",
            4670000,
            2300000,
            4020000,
            2900000,
            [
                "Real Qwen3-8B benchmark",
                "AR baseline: 34.0 tok/s and 120.4 s total time.",
                "Sync spec k=6 reaches 77.4 tok/s.",
                "Async SSD k=6, f=3 reaches 105.0 tok/s, 39.0 s total time, 0.776 cache hits, and accepted suffix 4.34.",
                "That is 3.09x AR throughput and 1.36x the sync baseline.",
            ],
        )
    )
    sp_tree.append(
        textbox(
            63,
            "Interpretation Box",
            457200,
            5450000,
            8120000,
            650000,
            [
                "Interpretation",
                "The next step is calibration: fit simulator service curves from accepted suffix length, cache hit behavior, and verifier-side timing instead of claiming final gains already proven.",
            ],
            fill="EAF1F6",
            line="3F6F8C",
        )
    )


def update_core_properties(root: ET.Element) -> None:
    title = root.find("./dc:title", NS)
    if title is None:
        title = ET.SubElement(root, f"{{{DC_NS}}}title")
    title.text = "Freshness-Aware Unified Speculative Budget Scheduling for SSD"


def finalize_xml(name: str, content: bytes) -> bytes:
    text = content.decode("utf-8")

    if name == "docProps/core.xml":
        text = text.replace('xmlns:ns2="http://purl.org/dc/terms/"', 'xmlns:dcterms="http://purl.org/dc/terms/"')
        text = text.replace("<ns2:created", "<dcterms:created")
        text = text.replace("</ns2:created>", "</dcterms:created>")
        text = text.replace("<ns2:modified", "<dcterms:modified")
        text = text.replace("</ns2:modified>", "</dcterms:modified>")
        if 'xmlns:dcmitype="http://purl.org/dc/dcmitype/"' not in text:
            text = text.replace(
                'xmlns:dcterms="http://purl.org/dc/terms/"',
                'xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/"',
            )

    if name == "ppt/slides/slide4.xml":
        text = text.replace('xmlns:ns2="http://schemas.microsoft.com/office/powerpoint/2010/main"', 'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main"')
        text = text.replace('xmlns:ns3="http://schemas.openxmlformats.org/markup-compatibility/2006"', 'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"')
        text = text.replace("<ns2:creationId", "<p14:creationId")
        text = text.replace("</ns2:creationId>", "</p14:creationId>")
        text = text.replace("<ns3:AlternateContent", "<mc:AlternateContent")
        text = text.replace("</ns3:AlternateContent>", "</mc:AlternateContent>")
        text = text.replace("<ns3:Choice", "<mc:Choice")
        text = text.replace("</ns3:Choice>", "</mc:Choice>")
        text = text.replace("<ns3:Fallback", "<mc:Fallback")
        text = text.replace("</ns3:Fallback>", "</mc:Fallback>")
        text = text.replace(" ns2:dur=", " p14:dur=")

    if name in {"ppt/slides/slide5.xml", "ppt/slides/slide6.xml"}:
        text = text.replace('xmlns:ns2="http://schemas.microsoft.com/office/drawing/2014/main"', 'xmlns:a16="http://schemas.microsoft.com/office/drawing/2014/main"')
        text = text.replace('xmlns:ns3="http://schemas.microsoft.com/office/powerpoint/2010/main"', 'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main"')
        text = text.replace('xmlns:ns4="http://schemas.openxmlformats.org/markup-compatibility/2006"', 'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"')
        text = text.replace("<ns2:creationId", "<a16:creationId")
        text = text.replace("</ns2:creationId>", "</a16:creationId>")
        text = text.replace("<ns3:creationId", "<p14:creationId")
        text = text.replace("</ns3:creationId>", "</p14:creationId>")
        text = text.replace("<ns4:AlternateContent", "<mc:AlternateContent")
        text = text.replace("</ns4:AlternateContent>", "</mc:AlternateContent>")
        text = text.replace("<ns4:Choice", "<mc:Choice")
        text = text.replace("</ns4:Choice>", "</mc:Choice>")
        text = text.replace("<ns4:Fallback", "<mc:Fallback")
        text = text.replace("</ns4:Fallback>", "</mc:Fallback>")
        text = text.replace(" ns3:dur=", " p14:dur=")

    return text.encode("utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    template_path = base_dir / "Slides_Template.pptx"
    output_path = base_dir / "specdiff_project_update.pptx"

    with ZipFile(template_path) as src:
        file_data = {name: src.read(name) for name in src.namelist()}

    for slide_no in range(1, 11):
        slide_name = f"ppt/slides/slide{slide_no}.xml"
        root = ET.fromstring(file_data[slide_name])
        for shape_name, paragraphs in SLIDE_TEXT.get(slide_no, {}).items():
            replace_text(find_shape(root, shape_name), paragraphs)

        if slide_no == 4:
            add_slide4_diagram(root)
        elif slide_no == 5:
            add_slide5_content(root)
        elif slide_no == 6:
            add_slide6_content(root)

        file_data[slide_name] = finalize_xml(
            slide_name,
            ET.tostring(root, encoding="utf-8", xml_declaration=True),
        )

    core_props = "docProps/core.xml"
    core_root = ET.fromstring(file_data[core_props])
    update_core_properties(core_root)
    file_data[core_props] = finalize_xml(
        core_props,
        ET.tostring(core_root, encoding="utf-8", xml_declaration=True),
    )

    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as dst:
        for name, content in file_data.items():
            dst.writestr(name, content)

    print(output_path)


if __name__ == "__main__":
    main()
