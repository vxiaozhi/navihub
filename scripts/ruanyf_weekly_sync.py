
#!/usr/bin/env python3
import os
import re
import requests
import yaml
from datetime import datetime

def download_readme(url, save_path):
    r = requests.get(url)
    r.raise_for_status()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(r.text)

def parse_issues_from_readme(readme_path):
    with open(readme_path, encoding='utf-8') as f:
        content = f.read()
    # 匹配类似 - [第 360 期](docs/issue-360.md) Dan Wang 的新书
    pattern = re.compile(r'- \[(第 (\d+) 期)\]\((docs/issue-(\d+)\\.md)\) ?(.*)')
    issues = []
    for match in re.finditer(pattern, content):
        title = match.group(1)
        num = match.group(2)
        url = f'https://github.com/ruanyf/weekly/blob/master/{match.group(3)}'
        desc = match.group(5).strip()
        issues.append({
            'title': title,
            'url': url,
            'description': desc,
            'logo': '/assets/images/logos/github.svg',
            'num': int(num)
        })
    return issues

def group_by_year_month(issues):
    # 以每 52 期为一年，约每月4期
    grouped = {}
    for issue in issues:
        year = 2018 + (issue['num'] - 1) // 52  # 2018年为第1期
        month = ((issue['num'] - 1) % 52) // 4 + 1
        y = str(year)
        m = f'{month:02d}'
        if y not in grouped:
            grouped[y] = {}
        if m not in grouped[y]:
            grouped[y][m] = []
        grouped[y][m].append(issue)
    return grouped

def build_yaml_structure(grouped):
    result = []
    for year in sorted(grouped.keys(), reverse=True):
        entry = {
            'taxonomy': year,
            'icon': 'fa-lightbulb-o',
            'list': []
        }
        for month in sorted(grouped[year].keys(), reverse=True):
            month_cn = f'{int(month)}月'
            links = [
                {
                    'title': i['title'],
                    'logo': i['logo'],
                    'url': i['url'],
                    'description': i['description']
                } for i in grouped[year][month]
            ]
            entry['list'].append({
                'term': month_cn,
                'links': links
            })
        result.append(entry)
    return result

def merge_to_yaml(new_data, yaml_path):
    with open(yaml_path, encoding='utf-8') as f:
        old = yaml.safe_load(f)
    # 合并策略：以新数据为主，保留旧数据中未覆盖部分
    merged = {e['taxonomy']: e for e in (old or [])}
    for e in new_data:
        merged[e['taxonomy']] = e
    # 按年份倒序
    return list(sorted(merged.values(), key=lambda x: x['taxonomy'], reverse=True))

def main():
    url = 'https://raw.githubusercontent.com/ruanyf/weekly/master/README.md'
    readme_path = './tmp/ruanyf_weekly_README.md'
    yaml_path = './web/data/ruanyf-weekly.yml'
    download_readme(url, readme_path)
    issues = parse_issues_from_readme(readme_path)
    grouped = group_by_year_month(issues)
    new_data = build_yaml_structure(grouped)
    #merged = merge_to_yaml(new_data, yaml_path)
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(new_data, f, allow_unicode=True, sort_keys=False)
    print(f'已更新 {yaml_path}')

if __name__ == '__main__':
    main()
