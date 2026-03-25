import json
import re
import ssl
import urllib.parse
from urllib.request import urlopen, Request

API = "https://monsterhunter.fandom.com/api.php"
HEADERS = {"User-Agent": "aidungeon-monster-hunter-bot/1.0"}
CTX = ssl._create_unverified_context()


def api_get(params):
    query = urllib.parse.urlencode(params)
    req = Request(f"{API}?{query}", headers=HEADERS)
    for _ in range(2):
        try:
            with urlopen(req, timeout=30, context=CTX) as resp:
                return json.loads(resp.read().decode("utf-8", "ignore"))
        except Exception:
            continue
    return {}


def clean(text):
    if not text:
        return ""
    text = re.sub(r"==.*?==", "", text)
    text = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"''+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def first_two_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    return " ".join(parts[:2])


path = "/Users/dsi/projects/aidungeon-monster-hunter/monsterunlisted.json"
with open(path) as f:
    data = json.load(f)

alias_map = {
    "Gajalaka Chief": "Gajalaka"
}

def section_text_for(name, idx, candidates):
    for section_name in candidates:
        index = idx.get(section_name)
        if not index:
            continue
        raw = api_get({"action": "parse", "page": name, "prop": "wikitext", "section": index, "format": "json"}).get("parse", {}).get("wikitext", {}).get("*", "")
        cleaned = first_two_sentences(clean(raw))
        if cleaned:
            return cleaned
    return ""


def intro_text(name):
    extract = api_get({"action": "query", "prop": "extracts", "explaintext": 1, "exintro": 1, "titles": name, "format": "json"}).get("query", {}).get("pages", {})
    for page in extract.values():
        text = page.get("extract", "")
        cleaned = first_two_sentences(clean(text))
        if cleaned:
            return cleaned
    return ""


for entry in data:
    name = entry.get("title") or entry.get("keys")
    if not name:
        continue
    lookup_name = alias_map.get(name, name)
    sections = api_get({"action": "parse", "page": lookup_name, "prop": "sections", "format": "json"}).get("parse", {}).get("sections", [])
    idx = {s.get("line", "").strip().lower(): s.get("index") for s in sections}

    physiology = section_text_for(lookup_name, idx, ["physiology", "appearance", "description", "characteristics", "biology", "in-game description"])
    abilities = section_text_for(lookup_name, idx, ["abilities", "behavior and abilities", "combat", "attacks", "combat abilities", "in-game description"])
    behavior = section_text_for(lookup_name, idx, ["behavior", "behavior and abilities", "behavior and diet", "habitat", "ecology", "behavior and ecology", "diet", "in-game description"])
    if not (physiology or abilities or behavior):
        intro = intro_text(lookup_name)
        if intro:
            physiology = intro
    if not abilities:
        intro = intro_text(lookup_name)
        if intro:
            abilities = intro
    if not behavior:
        intro = intro_text(lookup_name)
        if intro:
            behavior = intro
    if physiology or abilities or behavior:
        parts = []
        if physiology:
            parts.append(f"Physiology: {physiology}")
        if abilities:
            parts.append(f"Abilities: {abilities}")
        if behavior:
            parts.append(f"Behavior: {behavior}")
        entry["value"] = f"{name}. " + " ".join(parts)

with open(path, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")
