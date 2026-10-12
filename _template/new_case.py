#!/usr/bin/env python3
"""Create VN/EN Markdown drafts; convention from Cryovault 2026 Quals."""
import argparse
import datetime as dt
import json
from pathlib import Path
import re


def create(root, event, title, category=None, solve_date=None, wip=False):
    root = Path(root).resolve()
    event_path = (root / event).resolve()
    if not event_path.is_relative_to(root) or event_path == root:
        raise ValueError('Event must be inside the repository')
    slug = re.sub(r'[^A-Za-z0-9]+', '-', title).strip('-').lower()
    if not slug:
        raise ValueError('Challenge needs a usable filename')
    if solve_date:
        dt.datetime.fromisoformat(solve_date)
    destination = event_path / ('_wip' if wip else '') / (slug + '.md')
    destinations = [destination, destination.with_name(slug + '.en.md')]
    if any(path.exists() for path in destinations):
        raise FileExistsError('A VN or EN edition already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for path, template_name in zip(destinations, ['writeup.md', 'writeup.en.md']):
            template = (Path(__file__).parent / template_name).read_text(encoding='utf-8')
            template = template.replace('title: "<Challenge Name>"', 'title: ' + json.dumps(title, ensure_ascii=False))
            template = template.replace('<Challenge Name>', title)
            if category:
                template = template.replace('category: "<Primary category>"', 'category: ' + json.dumps(category))
            if solve_date:
                template = template.replace('solve_date: "YYYY-MM-DD"', 'solve_date: ' + json.dumps(solve_date))
            with path.open('x', encoding='utf-8', newline='\n') as output:
                created.append(path)
                output.write(template)
    except Exception:
        for path in created:
            path.unlink()
        raise
    return destinations


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('event')
    parser.add_argument('challenge')
    parser.add_argument('--category')
    parser.add_argument('--solve-date')
    parser.add_argument('--wip', action='store_true')
    options = parser.parse_args()
    for path in create(Path(__file__).resolve().parent.parent, options.event, options.challenge,
                       options.category, options.solve_date, options.wip):
        print(path)
