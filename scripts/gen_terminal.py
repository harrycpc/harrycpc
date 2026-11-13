# Generates terminal.svg: a looping "typing" terminal for the README.
# GitHub strips scripts from READMEs, so it's CSS (fades) + SMIL (typing clip). Run: python3 scripts/gen_terminal.py
import html, pathlib
W, LH, TOP, PAD, CW = 820, 26, 64, 24, 9.7   # CW = approx monospace char width at 16px
# restrained terminal palette: mostly plain text, green prompt, blue paths, one yellow highlight
BG, FG, DIM = '#1e1e2e', '#cdd6f4', '#7f849c'
GREEN, BLUE, YELLOW = '#a6e3a1', '#89b4fa', '#f9e2af'

def span(t, c=None): return f'<tspan fill="{c}">{html.escape(t)}</tspan>' if c else html.escape(t)
def row(label, items):  # "  label     item  item  item"
  return [span(f'  {label:<10}', DIM), span('  '.join(items) + '  ')]
PROMPT = span('harry@github', GREEN) + span(':') + span('~', BLUE) + span('$ ')

script = [  # ('cmd', text) is typed; ('out', spans[, 'bars']) fades in
  ('cmd', 'whoami'),
  ('out', [span("Hi everyone, I'm "), span('Harry', GREEN), span(' 🫶')]),
  ('cmd', 'cat about.txt'),
  ('out', [span('  role      ', DIM), span('Graduate DevOps Engineer')]),
  ('out', [span('  learning  ', DIM), span('Red Hat RHCSA (RHEL 10)', YELLOW), span(' — Sander Van Vugt course', DIM)]),
  ('out', [span('  hobbies   ', DIM), span('🏂 snowboarding')]),
  ('cmd', 'cat stack.txt'),
  ('out', row('devops', ['Linux', 'Docker', 'AWS', 'Git', 'CI/CD', 'Bash'])),
  ('out', row('learning', ['RHEL (RHCSA)', 'Red Hat OpenShift', 'ArgoCD']) + [span('▓▓▓░░', YELLOW)]),
  ('out', row('web', ['React', 'Next.js', 'Node.js', 'Python', 'Django'])),
  ('cmd', 'play'),
  ('out', [span('  ♪ now playing  ', DIM), span('harry.fm — snow day loop')], 'bars'),
  ('cmd', './open-terminal --live'),
  ('out', [span('  → harrycpc.github.io/harrycpc', BLUE), span('   ← click to try it (with music!)', DIM)]),
]
t, events = 0.6, []
for n, (kind, *rest) in enumerate(script):
  if kind == 'cmd':
    dur = len(rest[0]) * 0.07
    events.append((kind, rest[0], t, t + dur)); t += dur + 0.45
  else:
    events.append((kind, rest, t, t))
    t += 0.35 if n + 1 < len(script) and script[n + 1][0] == 'out' else 0.9
end = t; T = end + 5   # hold the finished screen for 5s, then loop
pct = lambda s: f'{s / T * 100:.2f}%'

css, defs, body = [], [], []
X0 = PAD + 16 * CW   # where typed text starts (after the 16-char prompt)
for i, (kind, data, a, e) in enumerate(events + [('cursor', None, end, end)]):
  y = TOP + i * LH
  css.append(f'@keyframes o{i}{{0%,{pct(a)}{{opacity:0}}{pct(a + .05)},97%{{opacity:1}}100%{{opacity:0}}}}'
             f'.o{i}{{animation:o{i} {T:.2f}s infinite}}')
  if kind == 'cmd':
    # typing = a clip whose width grows one character at a time (SMIL, discrete steps); nothing is painted over the text
    n = len(data)
    widths = ['0'] + [f'{k * CW:.1f}' for k in range(n + 1)] + [f'{W}', '0']
    times = [0] + [(a + (e - a) * k / n) / T for k in range(n + 1)] + [.97, 1]
    defs.append(f'<clipPath id="c{i}"><rect x="0" y="{y - 20}" width="{X0:.1f}" height="28"/>'
                f'<rect x="{X0:.1f}" y="{y - 20}" width="0" height="28"><animate attributeName="width" dur="{T:.2f}s" '
                f'repeatCount="indefinite" calcMode="discrete" values="{";".join(widths)}" keyTimes="{";".join(f"{k:.4f}" for k in times)}"/></rect></clipPath>')
    body.append(f'<g class="o{i}"><text x="{PAD}" y="{y}" fill="{FG}" clip-path="url(#c{i})">{PROMPT}<tspan fill="{FG}">{html.escape(data)}</tspan></text></g>')
  elif kind == 'out':
    spans, *flags = data
    bars = ''
    if flags:
      bx = PAD + 43 * CW
      bars = ''.join(f'<rect class="bar" x="{bx + j * 7:.1f}" y="{y - 14}" width="5" height="16" rx="1" fill="{GREEN}" '
                     f'style="animation-duration:{.45 + (j * 37 % 9) / 20:.2f}s"/>' for j in range(10))
    body.append(f'<g class="o{i}"><text x="{PAD}" y="{y}" fill="{FG}">{"".join(spans)}</text>{bars}</g>')
  else:
    body.append(f'<g class="o{i}"><text x="{PAD}" y="{y}" fill="{FG}">{PROMPT}</text>'
                f'<rect class="cur" x="{X0:.1f}" y="{y - 15}" width="10" height="19" fill="{FG}" fill-opacity=".8"/></g>')

H = TOP + len(events) * LH + 24
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ttl">
<title id="ttl">Terminal: Harry, Graduate DevOps Engineer — learning RHCSA, loves snowboarding. Click to open the interactive terminal.</title>
<defs>
<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#313244"/><stop offset="1" stop-color="#2a2b3d"/></linearGradient>
{chr(10).join(defs)}
</defs>
<style>
text{{font:16px ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;white-space:pre}}
{chr(10).join(css)}
.bar{{transform-box:fill-box;transform-origin:bottom;animation:eq .6s ease-in-out infinite alternate}}
@keyframes eq{{from{{transform:scaleY(.2)}}to{{transform:scaleY(1)}}}}
.cur{{animation:blink 1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{g,rect{{animation:none!important;opacity:1}}}}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="#45475a"/>
<path d="M1 11a10 10 0 0 1 10-10h{W - 22}a10 10 0 0 1 10 10v25H1z" fill="url(#bar)"/>
<path d="M1 36h{W - 2}" stroke="#11111b"/>
<circle cx="20" cy="18" r="6" fill="#ff5f57"/><circle cx="40" cy="18" r="6" fill="#febc2e"/><circle cx="60" cy="18" r="6" fill="#28c840"/>
<text x="{W / 2}" y="23" text-anchor="middle" fill="#a6adc8" style="font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">harry@github: ~ — zsh — 80×24</text>
{chr(10).join(body)}
</svg>
'''
out = pathlib.Path(__file__).resolve().parent.parent / 'terminal.svg'
out.write_text(svg)
print(f'wrote {out.name}: cycle {T:.1f}s, {len(events)} lines, {W}x{H}')
