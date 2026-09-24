(function () {
const W = window;
const Y = '#FFB400', WH = '#FFFFFF', G200 = '#EDEDED', G300 = '#D6D6D6', G500 = '#707070', G700 = '#4D4D4D', PANEL = '#0D0D0D', LINE = '#262626';
const INTER = "'Inter', system-ui, sans-serif", MONO = "'Roboto Mono', ui-monospace, monospace";
const MOTION = { enter: W.Easing.easeOutCubic, draw: W.Easing.easeInOutCubic, pop: W.Easing.easeOutQuart };
const c01 = v => (v < 0 ? 0 : v > 1 ? 1 : v);
const lerp = (a, b, u) => a + (b - a) * u;
function prog(T, a, b, e) { if (T <= a) return 0; if (T >= b) return 1; return (e || MOTION.enter)((T - a) / (b - a)); }
function win(T, a, b, d) { d = d == null ? 0.5 : d; return prog(T, a, a + d) * (1 - prog(T, b - d, b)); }
const fmt = n => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
const frac = v => v - Math.floor(v);

// ---------- camera ----------
function camera(T, C) {
  const k = [];
  const add = (t, cx, cy, s) => k.push({ t, cx, cy, s });
  add(0, 960, 2950, 1.55);
  add(C.Hardvara + 9.6, 960, 2950, 1.38);
  add(C.Containers + 2.6, 960, 2640, 0.93);
  add(C.Containers + 12, 960, 2630, 0.9);
  add(C.Signaler + 2.2, 960, 2250, 0.72);
  add(C.Signaler + 14, 960, 2230, 0.7);
  add(C.Collector + 2.2, 960, 1830, 1.1);
  add(C.Collector + 16, 960, 1830, 1.16);
  add(C.Lagring + 2.2, 960, 1560, 0.8);
  add(C.Lagring + 12, 960, 1550, 0.84);
  add(C.Cardinality + 2.2, 1150, 1330, 1.6);
  add(C.Cardinality + 12, 1150, 1330, 1.66);
  add(C.Grafana + 2.6, 960, 1600, 0.331);
  add(C.Grafana + 5, 960, 1600, 0.34);
  add(C.Grafana + 8.2, 960, 560, 0.94);
  add(C.Grafana + 12, 960, 560, 0.96);
  add(C.Metrics + 2.3, 380, 300, 2.3);
  add(C.Metrics + 15, 390, 300, 2.34);
  add(C.Traces + 2.2, 1290, 610, 1.55);
  add(C.Traces + 16, 1290, 610, 1.6);
  add(C.Logs + 2, 1290, 905, 1.6);
  add(C.Logs + 13, 1290, 905, 1.64);
  add(C.Helheten + 2.2, 960, 560, 0.94);
  add(C.Helheten + 6.4, 960, 560, 0.97);
  add(C.Helheten + 9.6, 960, 1600, 0.331);
  add(C.Slut + 12, 960, 1600, 0.35);
  if (T <= k[0].t) return k[0];
  for (let i = 0; i < k.length - 1; i++) {
    const a = k[i], b = k[i + 1];
    if (T < b.t) {
      const u = MOTION.draw((T - a.t) / (b.t - a.t));
      return { cx: lerp(a.cx, b.cx, u), cy: lerp(a.cy, b.cy, u), s: a.s * Math.pow(b.s / a.s, u) };
    }
  }
  return k[k.length - 1];
}

// ---------- data ----------
const nz = (m, a) => Math.sin(m * 2.1 + a) * 0.5 + Math.sin(m * 5.3 + a * 2) * 0.3 + Math.sin(m * 11.7 + a * 3) * 0.2;
const ramp = (m, a, b) => c01((m - a) / (b - a));
const S = {
  backend: m => lerp(210 + nz(m, 1) * 28, 4300 + nz(m, 1) * 160, ramp(m, 31.9, 32.4)),
  rag: m => lerp(150 + nz(m, 2) * 22, 3950 + nz(m, 2) * 150, ramp(m, 31.9, 32.4)),
  alg: m => 180 + nz(m, 3) * 20,
  gpu: m => lerp(46 + nz(m, 4) * 7, 99 + nz(m, 4) * 0.6, ramp(m, 31.0, 31.3)),
  mem: m => lerp(71 + nz(m, 5) * 1.2, 97, ramp(m, 30.8, 31.2)),
};
function nowMin(T, C) {
  if (T < C.Grafana) return 26;
  if (T < C.Metrics) return lerp(26, 30, (T - C.Grafana) / (C.Metrics - C.Grafana));
  return lerp(30, 36, c01((T - C.Metrics - 1) / 5));
}
function linePath(fn, now, x0, w, y0, h, ymax) {
  let d = '';
  for (let m = 0; m <= now + 1e-6; m += 0.1) {
    const x = x0 + (w * m) / 40, y = y0 + h * (1 - Math.min(fn(m), ymax) / ymax);
    d += (d ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
  }
  return d || 'M0 0';
}

const CONT = [
  ['frontend', 'ts'], ['api-gateway', 'nginx'], ['backend', 'c#'], ['auth', 'c#'], ['algorithm', 'python'],
  ['ai-rag', 'python'], ['reranker', 'python'], ['llm-server', 'python'], ['embeddings', 'python'], ['vector-db', 'db'],
  ['audio', 'python'], ['transcribe', 'python'], ['analytics', 'python'], ['worker', 'c#'], ['scheduler', 'c#'],
  ['postgres', 'db'], ['redis', 'cache'], ['object-store', 'storage'], ['notifier', 'ts'], ['admin-ui', 'ts'],
];
const INFRA = { 'vector-db': 1, postgres: 1, redis: 1, 'object-store': 1 };
const contPos = i => ({ x: 166 + (i % 10) * 160, y: i < 10 ? 2230 : 2450 });

const TP = [[570, 202], [1150, 737], [1150, 959], [480, 1330], [960, 1330], [1440, 1330], [960, 1830], [1040, 2325], [1360, 2325], [766, 2945]];
const TKEYS = ['p95', 'trace', 'logs', 'loki', 'tempo', 'prom', 'coll', 'rag', 'llm', 'dgx'];
function threadState(T, C) {
  const cum = [0];
  for (let i = 1; i < TP.length; i++) cum.push(cum[i - 1] + Math.hypot(TP[i][0] - TP[i - 1][0], TP[i][1] - TP[i - 1][1]));
  const L = cum[cum.length - 1];
  const u = prog(T, C.Helheten + 8.4, C.Helheten + 12.6, MOTION.draw);
  const drawn = u * L;
  const lit = {};
  TKEYS.forEach((k, i) => { lit[k] = u > 0 && drawn >= cum[i] - 1; });
  return { L, drawn, u, lit };
}

// ---------- particles ----------
function along(pts, u) {
  const seg = [];
  let L = 0;
  for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(l); L += l; }
  let d = u * L;
  for (let i = 0; i < seg.length; i++) {
    if (d <= seg[i] || i === seg.length - 1) {
      const t = seg[i] ? d / seg[i] : 0;
      return [lerp(pts[i][0], pts[i + 1][0], t), lerp(pts[i][1], pts[i + 1][1], t)];
    }
    d -= seg[i];
  }
  return pts[0];
}
function Particle({ type, x, y, o }) {
  if (type === 'trace') return <circle cx={x} cy={y} r="6" fill={Y} opacity={o} />;
  if (type === 'log') return <rect x={x - 9} y={y - 2} width="18" height="4" fill={WH} opacity={o} />;
  return <rect x={x - 4.5} y={y - 4.5} width="9" height="9" fill={G300} opacity={o} />;
}
function flowParticles(T, flows) {
  const out = [];
  flows.forEach((f, fi) => {
    for (let k = 0; k < f.n; k++) {
      const age = (T - f.t0) * f.speed - frac(f.seed + k / f.n);
      if (age < 0) continue;
      const u = frac(age);
      const [x, y] = along(f.pts, u);
      const o = Math.min(1, u * 6, (1 - u) * 6) * (f.alpha || 1);
      out.push(<Particle key={fi + '-' + k} type={f.type} x={x} y={y} o={o} />);
    }
  });
  return out;
}

// ---------- shared pieces ----------
function Panel({ x, y, w, h, title, right, lit, children }) {
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, height: h, background: PANEL, border: `${lit ? 2 : 1}px solid ${lit ? Y : LINE}`, boxSizing: 'border-box' }}>
      <div style={{ position: 'absolute', left: 18, top: 14, right: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: MONO, fontSize: 14, letterSpacing: '0.05em', textTransform: 'uppercase', color: G300, zIndex: 2 }}>
        <span>{title}</span>
        <span style={{ color: G500, display: 'flex', gap: 16, alignItems: 'center' }}>{right}</span>
      </div>
      {children}
    </div>
  );
}
const Key = ({ c, dash, label }) => (
  <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
    <svg width="18" height="4"><line x1="0" x2="18" y1="2" y2="2" stroke={c} strokeWidth="3" strokeDasharray={dash ? '4 3' : ''} /></svg>{label}
  </span>
);

// ---------- dashboard ----------
const NODES = { fe: [150, 185, 'frontend'], be: [390, 185, 'backend'], alg: [650, 110, 'algorithm'], rag: [650, 260, 'ai-rag'], vdb: [920, 150, 'vector-db'], llm: [920, 265, 'llm-server'] };
const EDGES = [['fe', 'be'], ['be', 'alg'], ['be', 'rag'], ['rag', 'vdb'], ['rag', 'llm']];
const SPANS = [
  { svc: 'frontend', op: 'GET /ask', d: 0, s: 0, dur: 4310 },
  { svc: 'backend', op: 'POST /api/ask', d: 1, s: 40, dur: 4200 },
  { svc: 'algorithm', op: 'score', d: 2, s: 60, dur: 180 },
  { svc: 'ai-rag', op: 'answer', d: 2, s: 250, dur: 3950 },
  { svc: 'retrieval', op: 'vector-db query', d: 3, s: 260, dur: 30 },
  { svc: 'reranker', op: 'rerank', d: 3, s: 295, dur: 20 },
  { svc: 'llm-server', op: 'generate', d: 3, s: 320, dur: 3880 },
];
const STREAM = [
  ['INFO', 'backend', 'ask_received'], ['INFO', 'frontend', 'page_view route=/'], ['INFO', 'analytics', 'batch_done rows=1204'],
  ['INFO', 'audio', 'chunk_processed ms=84'], ['INFO', 'worker', 'job_done id=7731'], ['INFO', 'ai-rag', 'retrieval_done docs=8'],
  ['INFO', 'scheduler', 'tick'], ['INFO', 'algorithm', 'score_done ms=176'],
];
const TRACE_LOGS = [
  ['14:32:07.112', 'INFO', 'frontend', 'request_started route=/ask'],
  ['14:32:07.153', 'INFO', 'backend', 'ask_received'],
  ['14:32:07.382', 'INFO', 'ai-rag', 'retrieval_done docs=8 ms=30'],
  ['14:32:09.402', 'WARN', 'ai-rag', 'llm_request_retry model=local-model attempt=2 reason=timeout'],
  ['14:32:11.422', 'INFO', 'frontend', 'response_sent duration_ms=4310'],
];

function Dashboard({ T, C, now, th }) {
  const inc = now >= 31.95, hot = now >= 31.1;
  const focP95 = T >= C.Metrics + 0.3 && T < C.Traces;
  const focTr = T >= C.Traces && T < C.Logs;
  const focLg = T >= C.Logs && T < C.Helheten;
  const mm = Math.floor(now), ss = Math.floor((now - mm) * 60);
  const clock = `14:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
  const exOp = prog(T, C.Metrics + 9.2, C.Metrics + 9.8);
  const tipOp = prog(T, C.Metrics + 12.3, C.Metrics + 12.7);
  const callOp = prog(T, C.Metrics + 4.4, C.Metrics + 5);
  const tcur = prog(T, C.Helheten + 2, C.Helheten + 3);
  const gpuCall = prog(T, C.Helheten + 3.8, C.Helheten + 4.4);
  const cursorOp = win(T, C.Metrics + 10.2, C.Traces + 1.2, 0.4);
  const cu = prog(T, C.Metrics + 10.6, C.Metrics + 12.0, MOTION.draw);
  const click = c01((T - (C.Metrics + 12.2)) / 0.6);
  const nowX = (x0, w) => x0 + (w * now) / 40;

  // trace panel
  const rowOp = i => prog(T, C.Traces + 2 + i * 0.45, C.Traces + 2.5 + i * 0.45);
  const prop = prog(T, C.Traces + 5.4, C.Traces + 7.2, MOTION.draw);
  const llmHi = prog(T, C.Traces + 10.2, C.Traces + 10.8);
  const retry = prog(T, C.Traces + 11.2, C.Traces + 11.8);
  const traceEmpty = 1 - prog(T, C.Traces + 1.2, C.Traces + 1.8);
  // logs panel
  const filt = prog(T, C.Logs + 1.6, C.Logs + 2.4, MOTION.draw);
  const filterStr = '| trace_id="abc123"';
  const warnHi = prog(T, C.Logs + 6.2, C.Logs + 6.8);
  const streamIdx = Math.floor(T * 1.2);

  return (
    <div style={{ position: 'absolute', left: 40, top: 40, width: 1840, height: 1000, background: '#050505', border: `1px solid ${LINE}`, boxSizing: 'border-box' }}>
      <div style={{ position: 'absolute', left: 20, right: 20, top: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontSize: 26, fontWeight: 600, letterSpacing: '-0.025em', color: WH }}>Plattform · Översikt</span>
        <span style={{ fontFamily: MONO, fontSize: 16, letterSpacing: '0.05em', color: G300 }}>PROD · SENASTE 40 MIN · <span style={{ color: inc ? Y : WH }}>{clock}</span></span>
      </div>
      <div style={{ position: 'absolute', left: -40, top: -40 }}>
        {/* p95 */}
        <Panel x={60} y={110} w={640} h={330} title="Request p95 · per tjänst" lit={focP95 || th.lit.p95}
          right={[<Key key="a" c={inc ? Y : WH} label="backend" />, <Key key="b" c={G300} label="ai-rag" />, <Key key="c" c={G500} dash label="algorithm" />]}>
          <svg width="640" height="330" style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
            {[0, 1000, 2000, 3000, 4000, 5000].map(v => { const y = 60 + 230 * (1 - v / 5000); return <g key={v}><line x1="70" x2="610" y1={y} y2={y} stroke={LINE} /><text x="60" y={y + 4} fill={G500} fontFamily={MONO} fontSize="13" textAnchor="end">{v === 0 ? '0' : v / 1000 + ' s'}</text></g>; })}
            {[0, 10, 20, 30, 40].map(m => <text key={m} x={70 + (540 * m) / 40} y="312" fill={G500} fontFamily={MONO} fontSize="13" textAnchor="middle">{`14:${String(m).padStart(2, '0')}`}</text>)}
            <line x1={nowX(70, 540)} x2={nowX(70, 540)} y1="60" y2="290" stroke={G700} strokeDasharray="3 4" />
            <path d={linePath(S.alg, now, 70, 540, 60, 230, 5000)} stroke={G500} strokeWidth="2" fill="none" strokeDasharray="5 5" />
            <path d={linePath(S.rag, now, 70, 540, 60, 230, 5000)} stroke={G300} strokeWidth="2" fill="none" />
            <path d={linePath(S.backend, now, 70, 540, 60, 230, 5000)} stroke={inc ? Y : WH} strokeWidth="3" fill="none" />
            <g opacity={tcur}>
              <line x1={70 + (540 * 31.1) / 40} x2={70 + (540 * 31.1) / 40} y1="60" y2="290" stroke={Y} strokeWidth="2" strokeDasharray="6 4" />
              <text x={70 + (540 * 31.1) / 40 - 8} y="74" fill={Y} fontFamily={MONO} fontSize="13" textAnchor="end">14:31</text>
            </g>
            <g opacity={callOp}>
              <text x="430" y="268" fill={G300} fontFamily={MONO} fontSize="14" textAnchor="middle">200 ms</text>
              <text x="530" y="82" fill={Y} fontFamily={MONO} fontSize="15">4 300 ms</text>
            </g>
            <g opacity={exOp}>
              <circle cx="510" cy="92" r={9 + 10 * frac(T * 0.8)} fill="none" stroke={Y} strokeWidth="1.5" opacity={1 - frac(T * 0.8)} />
              <rect x="504" y="86" width="12" height="12" fill={Y} stroke="#000" strokeWidth="1.5" transform="rotate(45 510 92)" />
            </g>
            <g opacity={tipOp}>
              <rect x="290" y="108" width="206" height="72" fill="#000" stroke={Y} strokeWidth="1.5" />
              <text x="304" y="130" fill={G300} fontFamily={MONO} fontSize="12">EXEMPLAR</text>
              <text x="304" y="150" fill={WH} fontFamily={MONO} fontSize="13">trace_id=abc123</text>
              <text x="304" y="169" fill={Y} fontFamily={MONO} fontSize="13">4 310 ms</text>
            </g>
          </svg>
        </Panel>

        {/* GPU */}
        <Panel x={60} y={460} w={640} h={300} title="DGX Spark · GPU & minne" lit={th.lit.dgx || (gpuCall > 0.5 && T < C.Helheten + 8.4)}
          right={[<Key key="a" c={hot ? Y : WH} label="GPU" />, <Key key="b" c={G300} dash label="unified mem" />]}>
          <svg width="640" height="300" style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
            {[0, 50, 100].map(v => { const y = 56 + 194 * (1 - v / 100); return <g key={v}><line x1="70" x2="610" y1={y} y2={y} stroke={LINE} /><text x="60" y={y + 4} fill={G500} fontFamily={MONO} fontSize="13" textAnchor="end">{v + ' %'}</text></g>; })}
            {[0, 10, 20, 30, 40].map(m => <text key={m} x={70 + (540 * m) / 40} y="274" fill={G500} fontFamily={MONO} fontSize="13" textAnchor="middle">{`14:${String(m).padStart(2, '0')}`}</text>)}
            <line x1={nowX(70, 540)} x2={nowX(70, 540)} y1="56" y2="250" stroke={G700} strokeDasharray="3 4" />
            <path d={linePath(S.mem, now, 70, 540, 56, 194, 100)} stroke={G300} strokeWidth="2" fill="none" strokeDasharray="5 5" />
            <path d={linePath(S.gpu, now, 70, 540, 56, 194, 100)} stroke={hot ? Y : WH} strokeWidth="3" fill="none" />
            <g opacity={tcur}>
              <line x1={70 + (540 * 31.1) / 40} x2={70 + (540 * 31.1) / 40} y1="56" y2="250" stroke={Y} strokeWidth="2" strokeDasharray="6 4" />
            </g>
            <g opacity={gpuCall}>
              <rect x="120" y="150" width="270" height="56" fill="#000" stroke={Y} strokeWidth="1.5" />
              <text x="136" y="174" fill={Y} fontFamily={MONO} fontSize="14">14:31 · GPU 100 %</text>
              <text x="136" y="194" fill={WH} fontFamily={MONO} fontSize="14">unified memory 97 %</text>
            </g>
          </svg>
        </Panel>

        {/* stats */}
        {[
          { x: 60, t: 'Felkvot', v: inc ? '3,1 %' : '0,2 %', h: inc },
          { x: 280, t: 'Requests/s', v: '42', h: false },
          { x: 500, t: 'Unified mem', v: hot ? '124 GB' : '91 GB', sub: 'av 128 GB', h: hot },
        ].map(s => (
          <Panel key={s.t} x={s.x} y={780} w={200} h={240} title={s.t}>
            <div style={{ position: 'absolute', left: 18, top: 92, fontSize: 52, fontWeight: 600, letterSpacing: '-0.025em', color: s.h ? Y : WH }}>{s.v}</div>
            {s.sub ? <div style={{ position: 'absolute', left: 18, top: 162, fontFamily: MONO, fontSize: 13, color: G500 }}>{s.sub}</div> : null}
          </Panel>
        ))}

        {/* service graph */}
        <Panel x={720} y={110} w={1140} h={330} title="Service graph" right="Tempo · från traces">
          <svg width="1140" height="330" style={{ position: 'absolute', left: 0, top: 0 }}>
            {EDGES.map(([a, b], i) => {
              const A = NODES[a], B = NODES[b];
              const slow = inc && (b === 'llm' || b === 'rag' || b === 'be');
              return (
                <g key={i}>
                  <line x1={A[0]} y1={A[1]} x2={B[0]} y2={B[1]} stroke={slow ? Y : G700} strokeWidth={slow ? 3 : 2} />
                  {[0, 1].map(k => { const u = frac(T * 0.45 + k * 0.5 + i * 0.17); return <circle key={k} cx={lerp(A[0], B[0], u)} cy={lerp(A[1], B[1], u)} r="4" fill={slow ? Y : G300} />; })}
                </g>
              );
            })}
            <text x="520" y="206" fill={inc ? Y : G500} fontFamily={MONO} fontSize="13" textAnchor="middle">{inc ? 'p95 4,2 s' : 'p95 0,2 s'}</text>
            <text x="790" y="290" fill={inc ? Y : G500} fontFamily={MONO} fontSize="13" textAnchor="middle">{inc ? 'p95 3,9 s' : 'p95 0,1 s'}</text>
            {Object.keys(NODES).map(k => {
              const [x, y, n] = NODES[k];
              const hotN = inc && k === 'llm';
              return (
                <g key={k}>
                  <rect x={x - 80} y={y - 22} width="160" height="44" fill={hotN ? Y : PANEL} stroke={hotN ? Y : G700} strokeWidth="2" />
                  <text x={x} y={y + 6} fill={hotN ? '#000' : WH} fontFamily={INTER} fontWeight="600" fontSize="17" textAnchor="middle">{n}</text>
                </g>
              );
            })}
          </svg>
        </Panel>

        {/* trace */}
        <Panel x={720} y={460} w={1140} h={300} lit={focTr || th.lit.trace}
          title={<span>Trace · <span style={{ color: prop > 0.5 ? Y : G300 }}>trace_id=abc123</span></span>}
          right="4 310 ms · 7 spans">
          <div style={{ position: 'absolute', left: 0, top: 130, width: '100%', textAlign: 'center', fontFamily: MONO, fontSize: 15, color: G500, opacity: traceEmpty }}>Välj ett exemplar för att öppna en trace</div>
          <svg width="1140" height="300" style={{ position: 'absolute', left: 0, top: 0 }}>
            <line x1="16" x2="16" y1={73} y2={lerp(73, 73 + 6 * 34, prop)} stroke={Y} strokeWidth="3" opacity={prop > 0 ? 1 : 0} />
            {SPANS.map((sp, i) => {
              const y = 56 + i * 34, cy = y + 17, o = rowOp(i);
              const bx = 490 + sp.s * 0.1409, bw = Math.max(3, sp.dur * 0.1409);
              const isLlm = sp.svc === 'llm-server';
              const barC = isLlm && llmHi > 0.5 ? Y : llmHi > 0.5 ? G700 : G500;
              return (
                <g key={i} opacity={o}>
                  <rect x={10} y={cy - 3} width="12" height="6" fill={Y} opacity={prop >= i / 6 && prop > 0 ? 1 : 0} />
                  <text x={34 + sp.d * 20} y={cy + 6} fill={WH} fontFamily={INTER} fontWeight="600" fontSize="17">{sp.svc}<tspan dx="10" fill={G500} fontFamily={MONO} fontWeight="400" fontSize="13">{sp.op}</tspan></text>
                  <text x="470" y={cy + 5} fill={isLlm && llmHi > 0.5 ? Y : G300} fontFamily={MONO} fontSize="14" textAnchor="end">{fmt(sp.dur)} ms</text>
                  <rect x={bx} y={cy - 9} width={bw} height="18" fill={barC} />
                  {isLlm ? (
                    <g opacity={retry}>
                      <line x1={490 + 2320 * 0.1409} x2={490 + 2320 * 0.1409} y1={cy - 9} y2={cy + 9} stroke="#000" strokeWidth="2" />
                      <text x={bx + 10} y={cy + 5} fill="#000" fontFamily={MONO} fontSize="12">attempt 1 · timeout</text>
                      <text x={490 + 2320 * 0.1409 + 10} y={cy + 5} fill="#000" fontFamily={MONO} fontSize="12">attempt 2</text>
                    </g>
                  ) : null}
                </g>
              );
            })}
          </svg>
        </Panel>

        {/* logs */}
        <Panel x={720} y={780} w={1140} h={240} title="Logs" right="Loki" lit={focLg || th.lit.logs}>
          <div style={{ position: 'absolute', left: 18, top: 44, fontFamily: MONO, fontSize: 15, color: G300, whiteSpace: 'pre' }}>
            {'{env="prod"} '}<span style={{ color: Y }}>{filterStr.slice(0, Math.round(filt * filterStr.length))}</span>
          </div>
          <div style={{ position: 'absolute', left: 18, right: 18, top: 78, opacity: 1 - filt }}>
            {[0, 1, 2, 3, 4].map(i => {
              const L = STREAM[(streamIdx + i) % STREAM.length];
              const sec = (Math.floor(T * 1.2) * 7 + i * 3) % 60;
              return <LogRow key={i} ts={`${clock.slice(0, 6)}${String(sec).padStart(2, '0')}.${String((i * 137 + streamIdx * 53) % 1000).padStart(3, '0')}`} lvl={L[0]} svc={L[1]} msg={L[2]} dim />;
            })}
          </div>
          <div style={{ position: 'absolute', left: 18, right: 18, top: 78, opacity: filt }}>
            {TRACE_LOGS.map((L, i) => (
              <div key={i} style={{ opacity: prog(T, C.Logs + 2.4 + i * 0.45, C.Logs + 2.9 + i * 0.45) }}>
                <LogRow ts={L[0]} lvl={L[1]} svc={L[2]} msg={L[3]} tid hi={L[1] === 'WARN' ? warnHi : 0} />
              </div>
            ))}
          </div>
        </Panel>

        {/* cursor */}
        <svg width="1920" height="1080" style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', opacity: cursorOp }}>
          <circle cx="572" cy="206" r={4 + click * 22} fill="none" stroke={Y} strokeWidth="2" opacity={click > 0 && click < 1 ? 1 - click : 0} />
          <g transform={`translate(${lerp(700, 572, cu)} ${lerp(430, 206, cu)}) scale(0.6)`}>
            <path d="M0 0 L0 30 L8 23 L14 36 L19 34 L13 21 L23 21 Z" fill={WH} stroke="#000" strokeWidth="2" strokeLinejoin="round" />
          </g>
        </svg>
      </div>
    </div>
  );
}
function LogRow({ ts, lvl, svc, msg, dim, tid, hi }) {
  const warn = lvl === 'WARN';
  const bg = hi ? `rgba(255,180,0,${hi})` : 'transparent';
  const ink = hi > 0.5;
  return (
    <div style={{ display: 'flex', gap: 14, height: 29, alignItems: 'center', fontFamily: MONO, fontSize: 15, whiteSpace: 'nowrap', background: bg, padding: '0 6px', margin: '0 -6px', opacity: dim ? 0.75 : 1 }}>
      <span style={{ color: ink ? '#000' : G500, width: 118 }}>{ts}</span>
      <span style={{ color: ink ? '#000' : warn ? Y : G300, width: 44 }}>{lvl}</span>
      <span style={{ color: ink ? '#000' : WH, width: 92 }}>{svc}</span>
      <span style={{ color: ink ? '#000' : G200 }}>{msg}</span>
      {tid ? <span style={{ color: ink ? '#000' : G500 }}>trace_id=abc123</span> : null}
    </div>
  );
}

// ---------- storage ----------
function StoreBox({ x, name, sig, lit, op, children }) {
  return (
    <div style={{ position: 'absolute', left: x, top: 1200, width: 440, height: 260, background: PANEL, border: `${lit ? 3 : 2}px solid ${lit ? Y : G700}`, boxSizing: 'border-box', opacity: op }}>
      <div style={{ position: 'absolute', left: 26, top: 24, fontFamily: MONO, fontSize: 16, letterSpacing: '0.05em', color: G300 }}>{sig}</div>
      <div style={{ position: 'absolute', left: 26, top: 48, fontSize: 42, fontWeight: 600, letterSpacing: '-0.025em', color: WH }}>{name}</div>
      <div style={{ position: 'absolute', left: 26, right: 26, bottom: 24, height: 100 }}>{children}</div>
    </div>
  );
}
function Storage({ T, C, th }) {
  const op = prog(T, C.Lagring - 0.4, C.Lagring + 0.8);
  const bad = prog(T, C.Cardinality + 2.5, C.Cardinality + 6.5, MOTION.draw);
  const good = prog(T, C.Cardinality + 7, C.Cardinality + 8);
  const promWarn = bad > 0.05 && good < 0.5;
  return (
    <div>
      <StoreBox x={260} name="Loki" sig="LOGS" lit={th.lit.loki} op={op}>
        {['INFO request_started', 'WARN llm_request_retry', 'INFO response_sent'].map((l, i) => (
          <div key={i} style={{ fontFamily: MONO, fontSize: 15, color: i === 1 ? G300 : G500, height: 30 }}>{l}</div>
        ))}
      </StoreBox>
      <StoreBox x={740} name="Tempo" sig="TRACES" lit={th.lit.tempo} op={op}>
        {[[0, 330], [30, 280], [60, 90], [90, 200]].map(([x, w], i) => (
          <div key={i} style={{ position: 'absolute', left: x, top: 8 + i * 24, width: w, height: 14, background: i === 3 ? Y : G700 }}></div>
        ))}
      </StoreBox>
      <StoreBox x={1220} name="Prometheus" sig="METRICS" lit={th.lit.prom || promWarn} op={op}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 100, opacity: 1 - Math.min(1, bad * 3) * (1 - good) }}>
          {[40, 46, 38, 52, 49, 55, 43, 60, 58, 50, 62, 57, 64, 59].map((h, i) => (
            <div key={i} style={{ width: 18, height: h + Math.sin(T * 1.4 + i) * 8, background: G300 }}></div>
          ))}
        </div>
      </StoreBox>
      {bad > 0 && good < 1 ? (
        <svg width="400" height="130" style={{ position: 'absolute', left: 1242, top: 1316, opacity: 1 - good }}>
          {Array.from({ length: Math.floor(616 * bad) }).map((_, i) => (
            <rect key={i} x={(i % 44) * 9} y={Math.floor(i / 44) * 9} width="6" height="6" fill={i % 7 === 0 ? Y : G300} />
          ))}
        </svg>
      ) : null}
    </div>
  );
}

// ---------- collector ----------
const STAGES = [
  ['otlp receiver', 'Tar emot från 20 tjänster', 'OTLP · logs, traces och metrics från 20 tjänster'],
  ['memory_limiter', 'Skyddar minnet', 'limit_mib: 1500 · backar av innan Collector går ner'],
  ['batch', 'Samlar ihop', 'send_batch_size: 8192 · timeout: 5s · färre, större skrivningar'],
  ['filter', 'Rensar brus', 'drop: health checks · /metrics-anrop · DEBUG'],
  ['redaction', 'Tar bort känslig data', null],
  ['tail_sampling', 'Behåller det viktiga', 'behåll: status = ERROR · duration > 2 s · 10 % av resten'],
];
function Collector({ T, C, th }) {
  const op = prog(T, C.Signaler + 2, C.Signaler + 3);
  const st = T >= C.Collector + 2.4 ? Math.min(5, Math.floor((T - C.Collector - 2.4) / 2.1)) : -1;
  const inScene = T >= C.Collector && T < C.Lagring + 1;
  const act = inScene ? st : -1;
  const detOp = inScene ? prog(T, C.Collector + 2.4, C.Collector + 2.9) * (1 - prog(T, C.Lagring, C.Lagring + 1)) : 0;
  const stT0 = C.Collector + 2.4 + Math.max(0, st) * 2.1;
  const sub = prog(T, stT0 + 0.2, stT0 + 0.6);
  return (
    <div style={{ position: 'absolute', left: 160, top: 1640, width: 1600, height: 380, background: PANEL, border: `${th.lit.coll ? 3 : 2}px solid ${th.lit.coll ? Y : G700}`, boxSizing: 'border-box', opacity: op }}>
      <div style={{ position: 'absolute', left: 30, top: 22, fontSize: 38, fontWeight: 600, letterSpacing: '-0.025em', color: WH }}>OpenTelemetry Collector</div>
      <div style={{ position: 'absolute', right: 30, top: 36, fontFamily: MONO, fontSize: 16, letterSpacing: '0.05em', color: G500 }}>RECEIVE · PROCESS · EXPORT</div>
      {STAGES.map((s, i) => {
        const on = i === act, past = act > i;
        return (
          <div key={i} style={{ position: 'absolute', left: 30 + i * 256, top: 96, width: 240, height: 130, boxSizing: 'border-box', border: `2px solid ${on ? Y : past ? G500 : LINE}`, background: on ? '#161616' : 'transparent', padding: '16px 18px' }}>
            <div style={{ fontFamily: MONO, fontSize: 14, color: on ? Y : G500 }}>{String(i + 1).padStart(2, '0')}</div>
            <div style={{ fontFamily: MONO, fontSize: 19, color: WH, marginTop: 10 }}>{s[0]}</div>
            <div style={{ fontSize: 16, color: G300, marginTop: 8 }}>{s[1]}</div>
          </div>
        );
      })}
      <div style={{ position: 'absolute', left: 30, right: 30, top: 250, height: 100, border: `1px solid ${LINE}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', padding: '0 26px', gap: 26, fontFamily: MONO, fontSize: 22, color: G200, opacity: detOp }}>
        {st === 4 ? (
          <span style={{ display: 'flex', gap: 22, opacity: sub }}>
            <span>user.email="anna@kund.se"</span><span style={{ color: G500 }}>→</span><span style={{ color: Y }}>user.email="[REDACTED]"</span>
          </span>
        ) : st >= 0 ? <span style={{ opacity: sub }}>{STAGES[st][2]}</span> : null}
        {st === 5 ? (
          <svg width="260" height="30" style={{ marginLeft: 'auto', opacity: sub }}>
            {Array.from({ length: 10 }).map((_, i) => {
              const keep = i === 2 || i === 5 || i === 8;
              const fade = prog(T, stT0 + 0.8, stT0 + 1.6);
              return <circle key={i} cx={13 + i * 26} cy="15" r="8" fill={keep ? Y : G300} opacity={keep ? 1 : 1 - fade * 0.85} />;
            })}
          </svg>
        ) : null}
      </div>
    </div>
  );
}

// ---------- containers ----------
function Containers({ T, C, th, now }) {
  const groupOp = prog(T, C.Containers + 0.4, C.Containers + 1.2);
  const sigOp = prog(T, C.Signaler + 1, C.Signaler + 2);
  return (
    <div>
      <div style={{ position: 'absolute', left: 150, top: 2170, width: 1620, height: 490, border: `1px dashed ${G700}`, boxSizing: 'border-box', opacity: groupOp }}>
        <div style={{ position: 'absolute', left: 16, top: 16, fontFamily: MONO, fontSize: 16, letterSpacing: '0.05em', color: G300 }}>APPLIKATION · 20 CONTAINERS</div>
      </div>
      {CONT.map(([n, tag], i) => {
        const p = contPos(i);
        const a = prog(T, C.Containers + 1 + i * 0.2, C.Containers + 1.6 + i * 0.2, MOTION.pop);
        const lit = (n === 'ai-rag' && th.lit.rag) || (n === 'llm-server' && th.lit.llm);
        const hotC = n === 'llm-server' && now >= 31.1;
        const cpu = hotC ? 0.94 : 0.2 + 0.3 * (0.5 + 0.5 * Math.sin(T * 0.8 + i * 1.7));
        const types = INFRA[n] ? ['metric'] : ['log', 'trace', 'metric'];
        return (
          <div key={i} style={{ position: 'absolute', left: p.x, top: p.y + (1 - a) * 14, width: 148, height: 190, background: PANEL, border: `${lit ? 3 : 2}px solid ${lit ? Y : G700}`, boxSizing: 'border-box', opacity: a }}>
            <div style={{ position: 'absolute', left: 12, top: 14, fontSize: 19, fontWeight: 600, letterSpacing: '-0.01em', color: WH }}>{n}</div>
            <div style={{ position: 'absolute', left: 12, top: 44, fontFamily: MONO, fontSize: 13, color: G500 }}>{tag}</div>
            <svg width="120" height="16" style={{ position: 'absolute', left: 12, top: 96, opacity: sigOp }}>
              {types.map((t, k) => t === 'trace' ? <circle key={k} cx={30 * k + 6} cy="8" r="6" fill={Y} /> : t === 'log' ? <rect key={k} x={30 * k} y="6" width="18" height="4" fill={WH} /> : <rect key={k} x={30 * k + 1} y="3.5" width="9" height="9" fill={G300} />)}
            </svg>
            <div style={{ position: 'absolute', left: 12, bottom: 30, fontFamily: MONO, fontSize: 12, color: G500 }}>CPU</div>
            <div style={{ position: 'absolute', left: 12, right: 12, bottom: 18, height: 5, background: '#1E1E1E' }}>
              <div style={{ width: `${cpu * 100}%`, height: '100%', background: hotC ? Y : G300 }}></div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------- DGX ----------
function Dgx({ T, C, th, now }) {
  const op = prog(T, 0, 0.9);
  const fill = prog(T, 0.8, 2.4, MOTION.draw);
  const jit = a => Math.sin(T * 1.3 + a) * 2.5;
  const hot = now >= 31.1;
  const g = [
    ['CPU', 34 + jit(1), (34 + jit(1)).toFixed(0) + ' %', false],
    ['GPU', Math.min(100, S.gpu(now) + (hot ? 0 : jit(2))), Math.min(100, S.gpu(now) + (hot ? 0 : jit(2))).toFixed(0) + ' %', hot],
    ['MINNE', S.mem(now), S.mem(now).toFixed(0) + ' %', hot],
    ['DISK', 22 + jit(3) * 0.3, (22 + jit(3) * 0.3).toFixed(0) + ' %', false],
    ['NÄTVERK', 18 + jit(4), fmt(180 + jit(4) * 10) + ' Mb/s', false],
  ];
  return (
    <div style={{ position: 'absolute', left: 460, top: 2760, width: 1000, height: 380, background: PANEL, border: `${th.lit.dgx ? 3 : 2}px solid ${th.lit.dgx ? Y : G500}`, boxSizing: 'border-box', opacity: op }}>
      <div style={{ position: 'absolute', left: 40, top: 26, fontSize: 46, fontWeight: 600, letterSpacing: '-0.025em', color: WH }}>NVIDIA DGX Spark</div>
      <div style={{ position: 'absolute', left: 40, top: 88, fontFamily: MONO, fontSize: 16, letterSpacing: '0.05em', color: G300 }}>GB10 GRACE BLACKWELL · 128 GB UNIFIED MEMORY</div>
      {g.map(([l, v, txt, h], i) => (
        <div key={l} style={{ position: 'absolute', left: 40 + i * 184, top: 140, width: 164, opacity: prog(T, 0.6 + i * 0.15, 1.2 + i * 0.15) }}>
          <div style={{ fontFamily: MONO, fontSize: 14, letterSpacing: '0.05em', color: G500 }}>{l}</div>
          <div style={{ fontSize: 32, fontWeight: 600, color: h ? Y : WH, marginTop: 6 }}>{txt}</div>
          <div style={{ height: 6, background: '#1E1E1E', marginTop: 10 }}>
            <div style={{ width: `${c01(v / 100) * 100 * fill}%`, height: '100%', background: h ? Y : G300 }}></div>
          </div>
        </div>
      ))}
      {[['node-exporter', 'CPU · RAM · disk'], ['cAdvisor', 'per container'], ['dcgm-exporter', 'GPU']].map(([n, d], i) => (
        <div key={n} style={{ position: 'absolute', left: 40 + i * 312, top: 280, width: 296, height: 62, border: `1px solid ${G700}`, boxSizing: 'border-box', padding: '10px 14px', opacity: prog(T, C.Hardvara + 6.8 + i * 0.4, C.Hardvara + 7.4 + i * 0.4) }}>
          <div style={{ fontFamily: MONO, fontSize: 17, color: WH }}>{n}</div>
          <div style={{ fontSize: 14, color: G500, marginTop: 2 }}>{d}</div>
        </div>
      ))}
    </div>
  );
}

// ---------- world overlay (lines, particles, thread) ----------
function Overlay({ T, C, th }) {
  const flows = [];
  CONT.forEach(([n], i) => {
    const p = contPos(i), cx = p.x + 74;
    const types = INFRA[n] ? ['metric'] : ['log', 'trace', 'metric'];
    types.forEach((t, k) => flows.push({ type: t, n: 2, speed: 0.33, seed: i * 0.137 + k * 0.31, t0: C.Signaler + 1.2 + i * 0.06, pts: [[cx + (k - 1) * 22, p.y], [960 + (cx - 960) * 0.75 + (k - 1) * 18, 2020]] }));
  });
  [['log', 480], ['trace', 960], ['metric', 1440]].forEach(([t, x], i) => {
    flows.push({ type: t, n: 4, speed: 0.55, seed: i * 0.21, t0: C.Lagring + 0.6, pts: [[x, 1640], [x, 1460]] });
    flows.push({ type: t, n: 3, speed: 0.55, seed: i * 0.33, t0: C.Grafana, alpha: 0.8, pts: [[x, 1200], [x, 1040]] });
  });
  const scrape = [[1420, 3071], [1820, 3071], [1820, 1330], [1660, 1330]];
  flows.push({ type: 'metric', n: 7, speed: 0.12, seed: 0.1, t0: C.Signaler + 10.6, pts: scrape });

  const scrapeU = prog(T, C.Signaler + 9.8, C.Signaler + 11.4, MOTION.draw);
  const scrapeL = 400 + 1741 + 160;
  const expOp = prog(T, C.Lagring, C.Lagring + 0.8);
  const grafOp = prog(T, C.Grafana, C.Grafana + 1);
  const genU = prog(T, C.Lagring + 5.2, C.Lagring + 6.4, MOTION.draw);
  const otlpOp = win(T, C.Signaler + 1.5, C.Collector + 1, 0.6);
  const TPs = TP.map(p => p.join(',')).join(' ');
  return (
    <svg width="1920" height="3200" style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible', pointerEvents: 'none' }}>
      <polyline points={scrape.map(p => p.join(',')).join(' ')} fill="none" stroke={G700} strokeWidth="2" strokeDasharray={`${scrapeU * scrapeL} ${scrapeL}`} />
      <text x="1836" y="2300" fill={G500} fontFamily={MONO} fontSize="16" opacity={scrapeU} transform="rotate(-90 1836 2300)" textAnchor="middle">SCRAPE · INFRA METRICS</text>
      {[480, 960, 1440].map(x => <line key={x} x1={x} x2={x} y1="1640" y2="1460" stroke={G700} strokeWidth="2" opacity={expOp} />)}
      {[480, 960, 1440].map(x => <line key={'g' + x} x1={x} x2={x} y1="1200" y2="1040" stroke={G700} strokeWidth="2" opacity={grafOp} />)}
      <text x="960" y="2090" fill={G300} fontFamily={MONO} fontSize="18" textAnchor="middle" opacity={otlpOp}>OTLP</text>
      <g opacity={genU}>
        <path d="M1110 1200 Q1200 1110 1290 1200" fill="none" stroke={G300} strokeWidth="2" strokeDasharray="6 5" />
        <path d="M1282 1186 L1292 1202 L1274 1200 Z" fill={G300} />
        <text x="1200" y="1128" fill={G300} fontFamily={MONO} fontSize="16" textAnchor="middle">metrics-generator · RED + service graph</text>
      </g>
      {flowParticles(T, flows)}
      <polyline points={TPs} fill="none" stroke={Y} strokeWidth="10" strokeLinejoin="round" strokeLinecap="round" strokeDasharray={`${th.drawn} ${th.L + 10}`} opacity={th.u > 0 ? 1 - prog(T, C.Slut, C.Slut + 1) : 0} />
      {TP.map((p, i) => th.lit[TKEYS[i]] ? <circle key={i} cx={p[0]} cy={p[1]} r="16" fill={Y} /> : null)}
    </svg>
  );
}

// ---------- screen-space ----------
const CHAPTERS = [
  ['Hardvara', '01 · Hårdvara'], ['Containers', '02 · Applikationen'], ['Signaler', '03 · Signaler'], ['Collector', '04 · OTel Collector'],
  ['Lagring', '05 · Lagring'], ['Cardinality', '06 · Cardinality'], ['Grafana', '07 · Grafana'], ['Metrics', '08 · Metrics: är något fel?'],
  ['Traces', '09 · Traces: var händer det?'], ['Logs', '10 · Logs: vad exakt hände?'], ['Helheten', '11 · Helheten'],
];
const ORDER = ['Hardvara', 'Containers', 'Signaler', 'Collector', 'Lagring', 'Cardinality', 'Grafana', 'Metrics', 'Traces', 'Logs', 'Helheten', 'Slut'];
function Chapter({ T, C }) {
  return CHAPTERS.map(([k, label]) => {
    const a = C[k], b = C[ORDER[ORDER.indexOf(k) + 1]];
    const o = win(T, a + 0.2, b, 0.4);
    return o > 0 ? <div key={k} style={{ position: 'absolute', left: 68, top: 22, background: '#000', padding: '8px 12px', fontFamily: MONO, fontSize: 20, letterSpacing: '0.05em', textTransform: 'uppercase', color: Y, opacity: o }}>{label}</div> : null;
  });
}
function Legend({ T, C }) {
  const o = win(T, C.Signaler + 1, C.Grafana + 1.5, 0.6);
  return (
    <div style={{ position: 'absolute', right: 80, top: 30, display: 'flex', gap: 30, alignItems: 'center', fontFamily: MONO, fontSize: 18, letterSpacing: '0.05em', color: G300, opacity: o }}>
      <span style={{ display: 'flex', gap: 10, alignItems: 'center' }}><svg width="18" height="18"><rect x="0" y="7" width="18" height="4" fill={WH} /></svg>LOGS</span>
      <span style={{ display: 'flex', gap: 10, alignItems: 'center' }}><svg width="14" height="14"><circle cx="7" cy="7" r="6" fill={Y} /></svg>TRACES</span>
      <span style={{ display: 'flex', gap: 10, alignItems: 'center' }}><svg width="12" height="12"><rect x="1" y="1" width="10" height="10" fill={G300} /></svg>METRICS</span>
    </div>
  );
}
const LAYERS = [
  [540, 'Grafana', 'Dashboards · explore · larm'], [1330, 'Loki · Tempo · Prometheus', 'Logs · traces · metrics'],
  [1830, 'OTel Collector', 'Tar emot · processar · exporterar'], [2435, '20 containers', 'Applikationen'], [2950, 'NVIDIA DGX Spark', 'Hårdvaran'],
];
function OverviewLabels({ T, C, cam }) {
  const o = c01((0.45 - cam.s) / 0.1) * (1 - prog(T, C.Slut, C.Slut + 0.8));
  if (o <= 0) return null;
  const x = 960 + 1000 * cam.s + 40;
  return LAYERS.map(([wy, t, d]) => (
    <div key={t} style={{ position: 'absolute', left: x, top: 540 + (wy - cam.cy) * cam.s - 30, opacity: o }}>
      <div style={{ fontSize: 30, fontWeight: 600, letterSpacing: '-0.025em', color: WH }}>{t}</div>
      <div style={{ fontFamily: MONO, fontSize: 16, letterSpacing: '0.05em', color: G500, marginTop: 6, textTransform: 'uppercase' }}>{d}</div>
    </div>
  ));
}
function CardinalityCard({ T, C }) {
  const q = C.Cardinality;
  const o = win(T, q + 1.4, C.Grafana + 0.4, 0.6);
  if (o <= 0) return null;
  const bad = prog(T, q + 2.5, q + 6.5, MOTION.draw);
  const good = prog(T, q + 7, q + 8.4, MOTION.draw);
  const peak = 24 * Math.pow(50000, bad);
  const n = good > 0 ? peak * Math.pow(36 / peak, good) : peak;
  const code = (lines, op) => (
    <div style={{ position: 'absolute', left: 50, top: 100, fontFamily: MONO, fontSize: 28, lineHeight: 1.5, color: G200, whiteSpace: 'pre', opacity: op }}>
      {lines.map((l, i) => <div key={i} style={{ color: l[1] ? l[1] : G200 }}>{l[0]}</div>)}
    </div>
  );
  return (
    <div style={{ position: 'absolute', left: 100, top: 170, width: 880, height: 700, background: '#000', border: `1px solid ${G700}`, boxSizing: 'border-box', opacity: o }}>
      <div style={{ position: 'absolute', left: 50, top: 44, fontFamily: MONO, fontSize: 20, letterSpacing: '0.05em', color: good > 0.5 ? G300 : Y }}>{good > 0.5 ? 'BÄTTRE' : 'UNDVIK'}</div>
      {code([['http_requests_total{'], ['  user_id="938293",', Y], ['  request_id="ABC123",', Y], ['  filename="whatever.pdf"', Y], ['}']], 1 - good)}
      {code([['http_requests_total{'], ['  service="backend",'], ['  method="POST",'], ['  status_code="200"'], ['}']], good)}
      <div style={{ position: 'absolute', left: 50, top: 450, fontFamily: MONO, fontSize: 20, letterSpacing: '0.05em', color: G500 }}>TIDSSERIER I PROMETHEUS</div>
      <div style={{ position: 'absolute', left: 50, top: 486, fontSize: 110, fontWeight: 600, letterSpacing: '-0.025em', color: n > 5000 ? Y : WH, lineHeight: 1 }}>{fmt(n)}</div>
    </div>
  );
}
const CAPS = C => [
  [C.Hardvara + 0.6, 'Allt körs på en maskin: en NVIDIA DGX Spark.'],
  [C.Hardvara + 3.8, 'Maskinen har egna signaler: CPU, GPU, minne, disk och nätverk.'],
  [C.Hardvara + 6.8, 'Exporters läser av dem: node-exporter, cAdvisor och dcgm-exporter.'],
  [C.Containers + 0.6, 'Ovanpå kör applikationen: runt 20 containers från flera repos.'],
  [C.Containers + 6.2, 'Varje container vet något om vad som händer. Ingen vet allt.'],
  [C.Signaler + 0.6, 'Varje tjänst skickar tre signaler över OTLP: logs, traces och metrics.'],
  [C.Signaler + 5.2, 'Allt märks med service.name, service.version och deployment.environment.'],
  [C.Signaler + 9.8, 'Infrastrukturens metrics hämtar Prometheus direkt från exporters.'],
  [C.Collector + 0.6, 'OpenTelemetry Collector är den gemensamma ingången.'],
  [C.Collector + 4.6, 'Den tar emot, batchar och filtrerar innan något lagras.'],
  [C.Collector + 10.6, 'Känsliga fält tas bort. Traces samplas: fel och långsamma requests behålls.'],
  [C.Lagring + 0.6, 'Varje signal får sitt eget lager: Loki, Tempo och Prometheus.'],
  [C.Lagring + 5.4, 'Tempo räknar fram RED-metrics ur traces: rate, errors, duration. Plus en service graph.'],
  [C.Cardinality + 0.6, 'En sak att undvika: unika värden som labels.'],
  [C.Cardinality + 3.6, 'user_id och request_id ger en ny tidsserie per användare och request.'],
  [C.Cardinality + 7.6, 'Håll labels få och stabila. Unika id:n hör hemma i traces och logs.'],
  [C.Grafana + 0.6, 'Hela stacken, från hårdvara till dashboard.'],
  [C.Grafana + 5.8, 'Allt möts i Grafana: samma tidsaxel, samma service.name, samma trace_id.'],
  [C.Metrics + 0.6, 'Metrics svarar på första frågan: är något fel?'],
  [C.Metrics + 4.4, 'Ja. Klockan 14:32 går p95 från 200 ms till 4 300 ms.'],
  [C.Metrics + 9.2, 'Punkten bär ett exemplar: en länk till den trace som gav just det värdet.'],
  [C.Traces + 0.6, 'Exemplaret öppnar exakt den trace som var långsam.'],
  [C.Traces + 5.4, 'Samma trace_id följer requesten genom alla tjänster.'],
  [C.Traces + 10.4, 'Traces svarar på: var händer det? I LLM-anropet, 3 880 av 4 310 ms.'],
  [C.Logs + 0.6, 'Samma trace_id leder vidare till loggarna.'],
  [C.Logs + 6.4, 'Logs svarar på: vad exakt hände? LLM-anropet timeoutade och gjordes om.'],
  [C.Helheten + 0.6, 'Samma tidsaxel går hela vägen ner till hårdvaran.'],
  [C.Helheten + 3.8, 'GPU:n på DGX Spark slog i taket 14:31. Minuten efter började LLM-anropen timeouta.'],
  [C.Helheten + 9.0, 'Från ett larm till en orsak, genom hela stacken.'],
  [C.Slut, null],
];
function Caption({ T, C, cam }) {
  const caps = CAPS(C);
  let idx = -1;
  for (let i = 0; i < caps.length; i++) if (T >= caps[i][0]) idx = i;
  if (idx < 0 || !caps[idx][1]) return null;
  const a = caps[idx][0], b = idx + 1 < caps.length ? caps[idx + 1][0] : a + 99;
  const o = win(T, a, b - 0.1, 0.35);
  return (
    <div style={{ position: 'absolute', left: 120, bottom: 72, maxWidth: cam.s < 0.45 ? 470 : 1500, background: '#000', padding: '18px 28px', fontSize: 38, lineHeight: 1.25, color: WH, opacity: o, textWrap: 'pretty' }}>{caps[idx][1]}</div>
  );
}
function EndCard({ T, C }) {
  const q = C.Slut;
  const bo = prog(T, q, q + 1);
  if (bo <= 0) return null;
  const yo = prog(T, q + 6, q + 6.8);
  const rows = [['METRICS', 'Är något fel?'], ['TRACES', 'Var händer det?'], ['LOGS', 'Vad exakt hände?']];
  return (
    <div style={{ position: 'absolute', inset: 0, background: '#000', opacity: bo }}>
      <div style={{ position: 'absolute', left: 160, top: 250, display: 'grid', gridTemplateColumns: '260px 1fr', rowGap: 56, alignItems: 'baseline' }}>
        {rows.map(([k, v], i) => {
          const o = prog(T, q + 0.8 + i * 1.1, q + 1.5 + i * 1.1);
          return [
            <div key={k} style={{ fontFamily: MONO, fontSize: 30, letterSpacing: '0.05em', color: Y, opacity: o }}>{k}</div>,
            <div key={k + 'v'} style={{ fontSize: 88, fontWeight: 600, letterSpacing: '-0.025em', lineHeight: 0.9, color: WH, opacity: o }}>{v}</div>,
          ];
        })}
      </div>
      <div style={{ position: 'absolute', inset: 0, background: Y, opacity: yo }}>
        <img src="assets/key-mark.svg" alt="" style={{ position: 'absolute', right: 120, top: 110, height: 200, filter: 'brightness(0)' }} />
        <div style={{ position: 'absolute', left: 120, top: 360, fontFamily: MONO, fontSize: 24, letterSpacing: '0.05em', color: '#000' }}>MÅLET</div>
        <div style={{ position: 'absolute', left: 120, top: 420, fontSize: 132, fontWeight: 600, letterSpacing: '-0.025em', lineHeight: 0.9, color: '#000' }}>Every service is observable.</div>
        <div style={{ position: 'absolute', left: 120, top: 620, maxWidth: 1300, fontSize: 40, lineHeight: 1.2, color: '#000', textWrap: 'pretty' }}>Fånga tillräckligt för att förstå systemets tillstånd och förklara varför något händer.</div>
      </div>
    </div>
  );
}

function Film() {
  const { T, CUES: C } = W.useComposition();
  const cam = camera(T, C);
  const now = nowMin(T, C);
  const th = threadState(T, C);
  const dashOp = prog(T, C.Grafana - 0.5, C.Grafana + 1);
  return (
    <div data-screen-label={`t=${Math.floor(T)}s`} style={{ position: 'absolute', inset: 0, background: '#000', overflow: 'hidden', fontFamily: INTER, color: WH }}>
      <div style={{ position: 'absolute', left: 0, top: 0, width: 1920, height: 3200, transformOrigin: '0 0', transform: `translate(${960 - cam.cx * cam.s}px, ${540 - cam.cy * cam.s}px) scale(${cam.s})` }}>
        <div style={{ opacity: dashOp }}><Dashboard T={T} C={C} now={now} th={th} /></div>
        <Storage T={T} C={C} th={th} />
        <Collector T={T} C={C} th={th} />
        <Containers T={T} C={C} th={th} now={now} />
        <Dgx T={T} C={C} th={th} now={now} />
        <Overlay T={T} C={C} th={th} />
      </div>
      <OverviewLabels T={T} C={C} cam={cam} />
      <Chapter T={T} C={C} />
      <Legend T={T} C={C} />
      <CardinalityCard T={T} C={C} />
      <Caption T={T} C={C} cam={cam} />
      <EndCard T={T} C={C} />
    </div>
  );
}

function ObservabilityFilm() {
  return (
    <W.CompositionStage width={1920} height={1080} scenes={W.OM_SCENES} playback={W.OM_PLAYBACK} bg="#000">
      <Film />
    </W.CompositionStage>
  );
}
W.ObservabilityFilm = ObservabilityFilm;
})();
