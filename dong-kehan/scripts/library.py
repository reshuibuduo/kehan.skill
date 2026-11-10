#!/usr/bin/env python3
"""Offline, dependency-free retrieval for the attributed Dong Kehan article index."""
import argparse
import collections
import hashlib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'verified_self', 'verified_other', 'unresolved', 'official_supplement', 'user_supplied'}
SCOPES = {'self': {'verified_self'}, 'other': {'verified_other'},
          'pending': {'unresolved'}, 'supplement': {'official_supplement'},
          'usable': {'verified_self', 'user_supplied'}, 'supplied': STATUSES,
          'all': STATUSES}


def read_library(root=ROOT):
    path = root / 'references' / 'articles.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def normalize(value):
    return unicodedata.normalize('NFKC', value).casefold()


def tokens(value):
    value = normalize(value)
    result = re.findall(r'[a-z0-9]+', value)
    for block in re.findall(r'[\u3400-\u9fff]+', value):
        if len(block) == 1:
            result.append(block)
        else:
            result.extend(block[i:i+2] for i in range(len(block)-1))
    return result


def local_text(row, root=ROOT):
    """Read only an integrity-checked body inside the skill's reference directory."""
    info = row.get('full_text')
    if not info:
        return ''
    relative = Path(info['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('local body path must be relative and stay inside references/user-provided')
    base = (root / 'references' / 'user-provided').resolve()
    path = (root / relative).resolve()
    if base not in path.parents or path.suffix != '.txt':
        raise ValueError('local body path must stay inside references/user-provided')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != info.get('sha256'):
        raise ValueError('local body SHA256 mismatch')
    return data.decode('utf-8')


def select_rows(rows, scope):
    chosen = [r for r in rows if r['status'] in SCOPES[scope]]
    if scope == 'supplied':
        chosen = [r for r in chosen if r.get('full_text', {}).get('origin') == 'user_provided']
    return chosen


def searchable(row, root=ROOT):
    return ' '.join([row['title']] * 3 + row.get('topics', []) * 2 +
                    [row.get('summary', '')] + row.get('key_points', []) +
                    row.get('aliases', []) + [local_text(row, root)])


def rank(rows, query, limit=5, root=ROOT):
    terms = set(tokens(query))
    if not terms:
        return []
    docs = [collections.Counter(tokens(searchable(r, root))) for r in rows]
    df = collections.Counter(term for d in docs for term in d)
    avg = sum(sum(d.values()) for d in docs) / max(len(docs), 1) or 1
    found = []
    for row, doc in zip(rows, docs):
        length = sum(doc.values())
        score = 0.0
        for term in terms:
            tf = doc.get(term, 0)
            if tf:
                idf = math.log(1 + (len(docs) - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * length / avg))
        if score > 0:
            found.append((score, row))
    found.sort(key=lambda pair: (-pair[0], pair[1]['id']))
    return [dict(row, retrieval_score=round(score, 4)) for score, row in found[:limit]]


def validate(rows, root=ROOT):
    errors, seen, urls, bodies = [], set(), set(), set()
    for row in rows:
        rid = row.get('id', '<missing>')
        for field in ['id', 'title', 'status', 'byline', 'sources', 'summary', 'key_points', 'topics', 'content_evidence', 'reviewed_at']:
            if field not in row:
                errors.append(f'{rid}: missing {field}')
        if rid in seen:
            errors.append(f'{rid}: duplicate id')
        seen.add(rid)
        if row.get('status') not in STATUSES:
            errors.append(f'{rid}: invalid status')
        if row.get('status') == 'verified_self':
            if row.get('byline') != ['董科含']:
                errors.append(f'{rid}: verified_self requires explicit 董科含 byline')
            if row.get('content_evidence') not in {'original_read', 'signed_reprint_read'}:
                errors.append(f'{rid}: verified_self requires body+byline evidence')
            if not row.get('authorship_evidence_url'):
                errors.append(f'{rid}: verified_self requires authorship evidence URL')
        if row.get('status') == 'user_supplied':
            if row.get('byline') or row.get('authorship_evidence_url'):
                errors.append(f'{rid}: user_supplied must not imply an independently verified byline')
            if row.get('content_evidence') != 'user_provided_body' or not row.get('full_text'):
                errors.append(f'{rid}: user_supplied requires user-provided local body evidence')
            if not row.get('title_is_provisional'):
                errors.append(f'{rid}: supplied text without original title must mark provisional title')
            if not any(s.get('type') == 'user_submission' for s in row.get('sources', [])):
                errors.append(f'{rid}: user_supplied requires a user-submission source')
        if row.get('full_text'):
            info = row['full_text']
            try:
                body = local_text(row, root)
                if not body.strip():
                    errors.append(f'{rid}: empty local body')
            except (OSError, KeyError, ValueError, UnicodeError) as exc:
                errors.append(f'{rid}: invalid local body: {exc}')
            digest = info.get('sha256')
            if digest in bodies:
                errors.append(f'{rid}: duplicate local body')
            bodies.add(digest)
            if info.get('origin') != 'user_provided' or not info.get('input_numbers'):
                errors.append(f'{rid}: local body must retain origin and input numbers')
        if row.get('content_evidence') in {'index_only', 'mention_only'}:
            if row.get('summary') or row.get('key_points'):
                errors.append(f'{rid}: index-only record contains inferred content')
        url = row.get('wechat_url')
        if url:
            if url in urls:
                errors.append(f'{rid}: duplicate WeChat article URL')
            urls.add(url)
            if urlsplit(url).hostname != 'mp.weixin.qq.com':
                errors.append(f'{rid}: non-WeChat wechat_url')
        for src in row.get('sources', []):
            native = src.get('type') == 'native_ui_observation' and src.get('locator') and src.get('reviewed_at')
            supplied = (src.get('type') == 'user_submission' and src.get('locator')
                        and src.get('reviewed_at') and row.get('full_text')
                        and src.get('path') == row['full_text'].get('path'))
            if not native and not supplied and not str(src.get('url', '')).startswith('https://'):
                errors.append(f'{rid}: source must have https URL')
        if not row.get('sources'):
            errors.append(f'{rid}: source evidence missing')
    return errors


def stats(rows, root=ROOT):
    counts = collections.Counter(r['status'] for r in rows)
    coverage_path = root / 'references' / 'coverage.json'
    coverage = json.loads(coverage_path.read_text(encoding='utf-8'))
    return dict(total=len(rows), **{s: counts[s] for s in sorted(STATUSES)},
                local_full_text_count=sum(bool(r.get('full_text')) for r in rows),
                full_history_verified=coverage['full_history_verified'],
                reviewed_at=coverage['reviewed_at'])


def render(row):
    print(f"{row['id']} | {row['title']} | {row['status']} | 署名：{','.join(row['byline']) or '待核实'}")
    if row.get('summary'):
        print(row['summary'])
    if row['status'] == 'user_supplied':
        print('来源标签：用户提供正文；原标题、署名、公众号链接与首发日期未独立核实。')
    if row.get('full_text'):
        print('本地正文（用户提供）：' + str(ROOT / row['full_text']['path']))
    if row.get('wechat_url'):
        print('微信原文：' + row['wechat_url'])
    if row.get('authorship_evidence_url'):
        print('署名核验：' + row['authorship_evidence_url'])
    elif row.get('sources'):
        src = row['sources'][0]
        print('目录证据：' + (src.get('url') or src.get('locator', '')))
    if row.get('notes'):
        print('核验说明：' + row['notes'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('stats')
    sub.add_parser('validate')
    search = sub.add_parser('search')
    search.add_argument('query')
    search.add_argument('--scope', choices=SCOPES, default='usable')
    search.add_argument('--limit', type=int, default=5)
    search.add_argument('--json', action='store_true')
    show = sub.add_parser('show')
    show.add_argument('id')
    body = sub.add_parser('text', help='Read the saved user-provided body, without rewriting it')
    body.add_argument('id')
    body.add_argument('--offset', type=int, default=0, help='Zero-based character offset')
    body.add_argument('--length', type=int, default=4000, help='Number of characters to return')
    args = parser.parse_args()
    rows = read_library()
    if args.command == 'validate':
        errors = validate(rows)
        if errors:
            print('\n'.join(errors))
            return 1
        print(f'PASS: {len(rows)} attributed records; no duplicate IDs/WeChat URLs; pending records contain no invented summaries')
    elif args.command == 'stats':
        print(json.dumps(stats(rows), ensure_ascii=False, sort_keys=True))
    elif args.command in {'show', 'text'}:
        item = next((r for r in rows if r['id'] == args.id), None)
        if item is None:
            print('NOT_FOUND: ' + args.id)
            return 2
        if args.command == 'show':
            print(json.dumps(item, ensure_ascii=False, indent=2))
        else:
            if args.offset < 0 or not 1 <= args.length <= 20000:
                parser.error('--offset must be nonnegative and --length must be between 1 and 20000')
            text = local_text(item)
            if not text:
                print('NO_LOCAL_TEXT: ' + args.id)
                return 3
            end = min(args.offset + args.length, len(text))
            print(f'{item["id"]} | 用户提供正文 | 字符范围 {args.offset}:{end}/{len(text)}')
            print(text[args.offset:end])
    else:
        if not 1 <= args.limit <= 100:
            parser.error('--limit must be between 1 and 100')
        chosen = select_rows(rows, args.scope)
        hits = rank(chosen, args.query, args.limit)
        if args.json:
            print(json.dumps(hits, ensure_ascii=False, indent=2))
        elif hits:
            for row in hits:
                render(row)
                print()
        else:
            print('NO_MATCH: 当前所选范围没有相关记录；这不等于作者从未讨论此问题。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
