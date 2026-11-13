# Generates stats.svg (GitHub stats + top languages) in the same terminal style as terminal.svg.
# Replaces the public stats/trophy services, which went down. Stdlib only.
#   GITHUB_TOKEN=... GH_USER=harrycpc python3 scripts/gen_stats.py dist/stats.svg
#   python3 scripts/gen_stats.py --demo out.svg      (sample data, no network; also runs the self-check)
import html, json, os, sys, urllib.request
from collections import Counter

BG, FG, DIM, GREEN, BLUE = '#1e1e2e', '#cdd6f4', '#7f849c', '#a6e3a1', '#89b4fa'
W, LH, TOP, PAD = 820, 26, 64, 24
Q = '''query($login:String!){ user(login:$login){
  followers{totalCount}
  repositories(ownerAffiliations:OWNER, isFork:false, first:100, orderBy:{field:PUSHED_AT, direction:DESC}){
    totalCount nodes{ stargazerCount languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } } }
  contributionsCollection{ totalCommitContributions totalPullRequestContributions contributionCalendar{ totalContributions } } } }'''

def fetch(user, token):
  req = urllib.request.Request('https://api.github.com/graphql', json.dumps({'query': Q, 'variables': {'login': user}}).encode(),
                               {'Authorization': f'bearer {token}', 'Content-Type': 'application/json'})
  data = json.load(urllib.request.urlopen(req, timeout=30))
  if 'errors' in data: sys.exit(f"GitHub API error: {data['errors']}")
  return data['data']['user']

def summarise(u):
  repos = u['repositories']; cc = u['contributionsCollection']; langs = Counter()
  for r in repos['nodes']:
    for e in r['languages']['edges']: langs[e['node']['name']] += e['size']
  total = sum(langs.values()) or 1
  return {'repos': repos['totalCount'], 'stars': sum(r['stargazerCount'] for r in repos['nodes']),
          'commits': cc['totalCommitContributions'], 'prs': cc['totalPullRequestContributions'],
          'contribs': cc['contributionCalendar']['totalContributions'], 'followers': u['followers']['totalCount'],
          'langs': [(n, s / total * 100) for n, s in langs.most_common(5)]}

def render(user, s):
  esc = html.escape
  prompt = lambda cmd: f'<tspan fill="{GREEN}">harry@github</tspan>:<tspan fill="{BLUE}">~</tspan>$ {esc(cmd)}'
  cell = lambda k, v: f'<tspan fill="{DIM}">{k:<11}</tspan>{str(v):<10}'
  lines = [prompt(f'gh stats {user}'),
           '  ' + cell('repos', s['repos']) + cell('stars', s['stars']) + cell('followers', s['followers']),
           '  ' + cell('commits', s['commits']) + cell('PRs', s['prs']) + cell('this year', f"{s['contribs']} contribs"),
           prompt('gh langs --top 5')]
  for name, pct in s['langs']:
    full = round(pct / 5)
    lines.append(f'  {esc(name):<14}<tspan fill="{GREEN}">{"█" * full}</tspan><tspan fill="#45475a">{"░" * (20 - full)}</tspan>'
                 f'  <tspan fill="{DIM}">{pct:5.1f}%</tspan>')
  lines.append(prompt(''))
  H = TOP + (len(lines) - 1) * LH + 24
  body = '\n'.join(f'<text x="{PAD}" y="{TOP + i * LH}">{l}</text>' for i, l in enumerate(lines))
  return f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">GitHub stats for {esc(user)}: {s['repos']} repos, {s['stars']} stars, {s['commits']} commits this year. Top languages: {esc(', '.join(n for n, _ in s['langs']))}.</title>
<defs><linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#313244"/><stop offset="1" stop-color="#2a2b3d"/></linearGradient></defs>
<style>text{{font:16px ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;white-space:pre;fill:{FG}}}
.cur{{animation:blink 1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}@media (prefers-reduced-motion:reduce){{.cur{{animation:none}}}}</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="#45475a"/>
<path d="M1 11a10 10 0 0 1 10-10h{W - 22}a10 10 0 0 1 10 10v25H1z" fill="url(#bar)"/><path d="M1 36h{W - 2}" stroke="#11111b"/>
<circle cx="20" cy="18" r="6" fill="#ff5f57"/><circle cx="40" cy="18" r="6" fill="#febc2e"/><circle cx="60" cy="18" r="6" fill="#28c840"/>
<text x="{W / 2}" y="23" text-anchor="middle" style="font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#a6adc8">harry@github: ~ — stats</text>
{body}
<rect class="cur" x="{PAD + 16 * 9.7:.1f}" y="{TOP + (len(lines) - 1) * LH - 15}" width="10" height="19" fill="{FG}" fill-opacity=".8"/>
</svg>
'''

DEMO = {'followers': {'totalCount': 7}, 'repositories': {'totalCount': 2, 'nodes': [
  {'stargazerCount': 3, 'languages': {'edges': [{'size': 600, 'node': {'name': 'TypeScript'}}, {'size': 200, 'node': {'name': 'Python'}}]}},
  {'stargazerCount': 1, 'languages': {'edges': [{'size': 200, 'node': {'name': 'Python'}}]}}]},
  'contributionsCollection': {'totalCommitContributions': 120, 'totalPullRequestContributions': 9, 'contributionCalendar': {'totalContributions': 150}}}

if __name__ == '__main__':
  demo = '--demo' in sys.argv; out = [a for a in sys.argv[1:] if a != '--demo'][0]
  user = os.environ.get('GH_USER', 'harrycpc')
  if demo:
    s = summarise(DEMO)
    assert (s['repos'], s['stars'], s['commits']) == (2, 4, 120)
    assert s['langs'] == [('TypeScript', 60.0), ('Python', 40.0)], s['langs']
    assert '<script' not in render('<x>', s) and '&lt;x&gt;' in render('<x>', s)
  else:
    s = summarise(fetch(user, os.environ['GITHUB_TOKEN']))
  os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
  open(out, 'w').write(render(user, s))
  print(f'wrote {out}: {s["repos"]} repos, top langs {[n for n, _ in s["langs"]]}')
