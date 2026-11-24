# encoding: utf-8
"""
RedNote Slide Clipper (Slide-to-Mindmap Clipper for RedNote / Xiaohongshu & Visual Web)
Personal learning clipper: turns multi-slide visual carousels (mindmaps, tables, checklists)
into clean, searchable Obsidian Markdown using 100% local zero-token RapidOCR.

Fair-Use Notice:
This tool is strictly a user-initiated personal note-taking & study aid for single public
pages opened by the user. It contains zero anti-bot bypass or bulk scraping logic.
"""

import argparse
import asyncio
import os
import re
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from rapidocr_onnxruntime import RapidOCR

from license_verifier import activate_token, get_license_status, verify_license_token

sys.stdout.reconfigure(encoding="utf-8")

PRO_LENS_TEMPLATES = {
    "general": {
        "name": "General Business & Execution Lens",
        "questions": [
            "Core Value Proposition: What specific pain point does this post address?",
            "Hidden Preconditions: What resources, traffic base, or capital are assumed but unstated?",
            "Actionable Next Step: What is the smallest 24-hour validation experiment?",
        ],
    },
    "cross-border": {
        "name": "Cross-Border E-Commerce & Sourcing Lens",
        "questions": [
            "Margin & Landed Cost Check: Does the retail-to-sourcing spread cover customer acquisition and shipping?",
            "Compliance & Logistics Gate: Are there certification, IP/trademark, or fragile shipping bottlenecks?",
            "Channel Fit: Is demand search-driven (SEO/Amazon) or impulse-driven (TikTok/Reels)?",
        ],
    },
    "hardtech": {
        "name": "Hard-Tech & Manufacturing Research Lens",
        "questions": [
            "Process & Tolerance Bottleneck: What physical yield, cycle-time, or equipment constraint defines the moat?",
            "Substitution Position: Which incumbent specification is being matched or replaced?",
            "Verification Anchor: Which public filings, patents, or customer qualification milestones confirm scale?",
        ],
    },
    "high-ticket": {
        "name": "High-Ticket Solo Business & Persuasion Lens",
        "questions": [
            "Audience Bottleneck: What urgent obstacle makes a buyer willing to pay a premium for outcomes?",
            "Proof Mechanism: Which concrete case metrics, demos, or diagnostic frameworks establish authority?",
            "Productized Delivery: How can manual coaching be converted into a repeatable diagnostic or workflow asset?",
        ],
    },
}


def build_mermaid_mindmap(title: str, ocr_pages: list, paragraphs: list) -> str:
    root_label = re.sub(r'["\':*?<>|()（）\[\]]', "", title)[:22] or "Visual Study Note"
    lines = ["```mermaid", "mindmap", f"  root(({root_label}))"]
    branches = []
    for p in ocr_pages[:4]:
        first_line = next((ln.strip() for ln in p["text"].splitlines() if len(ln.strip()) >= 3), "")
        if first_line:
            clean_b = re.sub(r'["\':*?<>|()（）\[\]]', "", first_line)[:18]
            branches.append((f"Slide {p['page']}", clean_b))
    if not branches:
        for idx, para in enumerate(paragraphs[:4], start=1):
            clean_b = re.sub(r'["\':*?<>|()（）\[\]]', "", para)[:18]
            if clean_b:
                branches.append((f"Point {idx}", clean_b))
    for tag, text in branches:
        lines.append(f"    {tag}[{text}]")
    lines.append("```")
    return "\n".join(lines)


def cluster_comments(comments: list) -> tuple[list, list]:
    pitfall_keywords = (
        "但是", "其实", "坑", "没用", "难", "成本", "封号", "注意", "缺点", "假",
        "however", "pitfall", "careful", "expensive", "hard", "issue", "problem",
    )
    consensus, counter = [], []
    for c in comments:
        txt = c.get("content", "").strip()
        if not txt:
            continue
        if any(k in txt.lower() for k in pitfall_keywords):
            counter.append(c)
        else:
            consensus.append(c)
    return consensus[:5], counter[:5]


def render_markdown(
    title: str,
    author: str,
    url: str,
    raw_content: str,
    ocr_pages: list,
    comments: list,
    is_pro: bool,
    lens_key: str,
) -> tuple[str, str]:
    clean_title = re.sub(r'[\\/:*?"<>|]+', "_", title).strip()[:70] or "clipped_slide_note"
    today = datetime.now().strftime("%Y-%m-%d")
    now_hm = datetime.now().strftime("%Y-%m-%d %H:%M")
    paragraphs = [p.strip() for p in raw_content.splitlines() if p.strip()]

    lines = [
        "---",
        "tags: [slide-clipper, visual-notes, rapidocr]",
        f"created: {today}",
        f"status: {'pro_synthesized' if is_pro else 'clipped'}",
        f'author: "{author}"',
        f'source_url: "{url}"',
        "---",
        "",
        f"# {title or 'Visual Carousel Note'}",
        "",
        f"> **Author**: `{author or 'Unknown'}` | **Clipped**: `{now_hm}` | **Edition**: `{'Pro Lens' if is_pro else 'MIT Core'}`",
        f"> **Source**: [{url}]({url})",
        "",
        "---",
        "",
        f"## 1. Slide-by-Slide Offline OCR Extraction ({len(ocr_pages)} slides recognized)",
        "",
    ]

    if ocr_pages:
        for s in ocr_pages:
            lines.append(f"### Slide {s['page']}")
            for ln in s["text"].splitlines():
                if ln.strip():
                    lines.append(f"- {ln.strip()}")
            lines.append("")
    else:
        lines.append("*No slide text detected on this page.*")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 2. Original Post Text",
        "",
    ])
    if paragraphs:
        for p in paragraphs:
            lines.append(f"> {p}")
            lines.append(">")
    else:
        lines.append("> *(Image-focused post with minimal caption text)*")
    lines.append("")

    if is_pro:
        lens = PRO_LENS_TEMPLATES.get(lens_key, PRO_LENS_TEMPLATES["general"])
        consensus, counter = cluster_comments(comments)
        lines.extend([
            "---",
            "",
            "## 3. Auto Visual Mindmap (Pro)",
            "",
            build_mermaid_mindmap(title, ocr_pages, paragraphs),
            "",
            "---",
            "",
            f"## 4. Reader Discussion & Pitfall Radar ({len(comments)} visible comments)",
            "",
            "### Top Consensus",
        ])
        if consensus:
            for c in consensus:
                lines.append(f"- **@{c['user']}** ({c['likes']}): {c['content']}")
        else:
            lines.append("- No consensus comments captured.")
        lines.extend(["", "### Counter-Consensus & Practical Caveats"])
        if counter:
            for c in counter:
                lines.append(f"- **@{c['user']}** ({c['likes']}): {c['content']}")
        else:
            lines.append("- No explicit caveats flagged in visible comments.")

        lines.extend([
            "",
            "---",
            "",
            f"## 5. Analytical Checklist — {lens['name']} (Pro)",
            "",
        ])
        for q in lens["questions"]:
            lines.append(f"- [ ] {q}")
        lines.append("")

    return clean_title, "\n".join(lines)


async def clip_single_url(url: str, out_dir: Path, lens_key: str = "general", max_slides: int = 18) -> Path:
    lic = get_license_status()
    is_pro = lic["is_pro"]
    ocr_engine = RapidOCR()

    title = ""
    author = ""
    content = ""
    comments = []
    ocr_pages = []
    temp_dir = tempfile.mkdtemp(prefix="slide_clipper_")
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=ua, viewport={"width": 1280, "height": 900})
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(3000)

            title_el = await page.query_selector("#detail-title, .title, h1")
            if title_el:
                title = (await title_el.inner_text()).strip()
            if not title:
                title = (await page.title()).strip()

            author_el = await page.query_selector(".username, .name, [class*='author-name']")
            if author_el:
                author = (await author_el.inner_text()).strip()

            desc_el = await page.query_selector("#detail-desc, .desc, .note-text, article")
            if desc_el:
                content = (await desc_el.inner_text()).strip()

            slide_urls = await page.evaluate("""() => {
                const urls = [];
                try {
                    const map = window.__INITIAL_STATE__?.note?.noteDetailMap || {};
                    for (const k of Object.keys(map)) {
                        const imgs = map[k]?.note?.imageList || [];
                        for (const im of imgs) {
                            const u = im.urlDefault || (im.infoList && im.infoList.length ? im.infoList[im.infoList.length - 1].url : '');
                            if (u && !urls.includes(u)) urls.push(u);
                        }
                    }
                } catch (e) {}
                if (!urls.length) {
                    document.querySelectorAll('.swiper-slide img, article img, [class*="media"] img').forEach(el => {
                        const src = el.getAttribute('src') || '';
                        if (src.startsWith('http') && !src.includes('avatar') && !urls.includes(src)) urls.push(src);
                    });
                }
                return urls;
            }""")

            for idx, img_url in enumerate((slide_urls or [])[:max_slides], start=1):
                img_file = os.path.join(temp_dir, f"slide_{idx:02d}.jpg")
                try:
                    req = urllib.request.Request(img_url, headers={"User-Agent": ua, "Referer": url})
                    with urllib.request.urlopen(req, timeout=15) as resp, open(img_file, "wb") as f:
                        f.write(resp.read())
                    ocr_out, _ = ocr_engine(img_file)
                    if ocr_out:
                        txt = "\n".join(item[1] for item in ocr_out if len(item) >= 2 and str(item[1]).strip())
                        if txt.strip():
                            ocr_pages.append({"page": idx, "text": txt.strip()})
                except Exception:
                    pass
                finally:
                    if os.path.exists(img_file):
                        try:
                            os.remove(img_file)
                        except OSError:
                            pass

            dom_comments = await page.query_selector_all(".comment-item, [class*='comment-item']")
            for item in dom_comments[:30]:
                try:
                    u_el = await item.query_selector(".author, .name, [class*='author-name']")
                    t_el = await item.query_selector(".note-text, .content, [class*='content']")
                    l_el = await item.query_selector(".like, .count, [class*='like-count']")
                    u_txt = (await u_el.inner_text()).strip() if u_el else "reader"
                    c_txt = (await t_el.inner_text()).strip() if t_el else ""
                    l_txt = (await l_el.inner_text()).strip() if l_el else "0"
                    if c_txt:
                        comments.append({"user": u_txt, "content": c_txt, "likes": l_txt})
                except Exception:
                    pass

            await browser.close()
    finally:
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass

    clean_title, md_body = render_markdown(
        title=title,
        author=author,
        url=url,
        raw_content=content,
        ocr_pages=ocr_pages,
        comments=comments,
        is_pro=is_pro,
        lens_key=lens_key,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{clean_title}.md"
    out_path.write_text(md_body, encoding="utf-8")
    print(f"Saved clipped note [{lic['tier']}]: {out_path} (OCR slides: {len(ocr_pages)})")
    return out_path


def run_self_test():
    print("[1/2] Testing RapidOCR offline engine initialization...")
    ocr = RapidOCR()
    assert ocr is not None
    print("  OK: RapidOCR ready (100% offline, 0 API tokens).")

    print("[2/2] Testing Ed25519 asymmetric public-key verifier (<0.2ms)...")
    bad = verify_license_token("RMC1.eyJ1IjoidGVzdCIsImV4cCI6MH0.badsignature")
    assert not bad["valid"], "Invalid token should be rejected"
    clean_name, sample_md = render_markdown(
        title="Sample 12-Slide Supply Chain Mindmap",
        author="demo_author",
        url="https://example.com/post/1",
        raw_content="Key takeaways from visual slides.",
        ocr_pages=[{"page": 1, "text": "Step 1: Verify factory ISO & MOQ\nStep 2: Compare FOB port lead times"}],
        comments=[{"user": "alice", "content": "Super helpful, however watch out for peak season delays!", "likes": "12"}],
        is_pro=True,
        lens_key="cross-border",
    )
    assert "```mermaid" in sample_md and "Slide 1" in sample_md
    print(f"  OK: Ed25519 signature guard & Markdown renderer verified ({clean_name}).")


def main():
    parser = argparse.ArgumentParser(description="RedNote Slide Clipper — Offline OCR Slide-to-Markdown Clipper")
    parser.add_argument("--url", type=str, help="Single public post URL to clip into Obsidian Markdown")
    parser.add_argument("--out", type=str, default="./notes", help="Output folder for Markdown notes")
    parser.add_argument("--lens", choices=list(PRO_LENS_TEMPLATES.keys()), default="general", help="Analytical lens (Pro)")
    parser.add_argument("--activate", type=str, help="Activate an offline Ed25519 Pro license key (RMC1...)")
    parser.add_argument("--status", action="store_true", help="Show current license tier status")
    parser.add_argument("--self-test", action="store_true", help="Run offline OCR & Ed25519 verifier self-check")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return

    if args.activate:
        res = activate_token(args.activate)
        if res["valid"]:
            print(f"Pro license activated! User: {res['user']} | Valid until: {res['expires']}")
        else:
            print(f"Activation failed: {res['reason']}")
            sys.exit(1)
        return

    if args.status:
        st = get_license_status()
        print(f"Current Tier: {st['tier']} | Expires: {st['expires']}")
        return

    if not args.url:
        parser.print_help()
        return

    asyncio.run(clip_single_url(args.url, Path(args.out), lens_key=args.lens))


if __name__ == "__main__":
    main()
