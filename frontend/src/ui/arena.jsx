// Arena landmarks + battle FX — adapted from design handoff to ES modules.

const PAL = {
  ".": "transparent", "k": "#000000",
  "g": "#3cffa0", "G": "#1a6b3a", "H": "#0a3a22",
  "s": "#9a9ab5", "S": "#5a5a7a",
  "w": "#e8e8f5", "W": "#9ed7ff",
  "b": "#3c5cff", "B": "#0a1a4d",
  "c": "#3cf0ff", "C": "#0a3a4d",
  "y": "#ffd23c", "Y": "#7a5500",
  "o": "#ff8c3c", "O": "#7a3300",
  "r": "#ff3c5c", "R": "#7a0010",
  "p": "#9b3cff", "P": "#3a0066",
  "m": "#ff3cd0", "M": "#660036",
  "n": "#a06b3a", "N": "#3a1a00",
  "t": "#5a3a1a", "T": "#2a1a00",
  "a": "#b6ff3c", "A": "#1a3a00",
  "1": "#1a1a2a", "2": "#2a2a3a",
};

function PxSprite({ map, scale = 3, style = {} }) {
  const w = (map[0] || "").length;
  const h = map.length;
  return (
    <div className="pixelated" style={{ width: w * scale, height: h * scale, position: "absolute", ...style }}>
      {map.map((row, y) =>
        [...row].map((ch, x) => {
          const c = PAL[ch];
          if (!c || c === "transparent") return null;
          return (
            <span key={`${x}-${y}`} style={{
              position: "absolute", left: x * scale, top: y * scale,
              width: scale, height: scale, background: c,
            }} />
          );
        })
      )}
    </div>
  );
}

const LM = {
  tree: [
    "....kkkkk.....",
    "...kggggGk....",
    "..kgggggGGk...",
    ".kggGgGgggGk..",
    ".kgggGGgGggk..",
    "..kgggGgggGk..",
    "...kggGgGGk...",
    "....kgggGk....",
    ".....kntk.....",
    ".....kntk.....",
    "....kntntk....",
    "....kkkkkk....",
  ],
  pineTree: [
    ".....kk.....",
    "....kggk....",
    "...kgGGgk...",
    "..kgGgGGgk..",
    "...kggGgk...",
    "..kgGGgGgk..",
    ".kgGgGGgGgk.",
    "..kgggGgGk..",
    "...kkntkk...",
    "....kntk....",
    "....kkk.....",
    "............",
  ],
  boulder: [
    "...kkkk....",
    "..ksssSk...",
    ".ksSsssSk..",
    ".ksssSssSk.",
    "kssSsssSssk",
    "kSssSssSssk",
    ".kssSssSk..",
    "..kkkkkk...",
    "...........",
    "...........",
    "...........",
    "...........",
  ],
  pillar: [
    ".kssssk.",
    "ksSSSSSk",
    "ksSwSwSk",
    ".kSSSSk.",
    ".kSwSwk.",
    ".kSSSSk.",
    ".kSwSwk.",
    ".kSSSSk.",
    "ksSSSSSk",
    "kssssssk",
    "ksSSSSSk",
    ".kkkkkk.",
  ],
  tombstone: [
    "...kkkk...",
    "..kssssk..",
    ".ksSsSsSk.",
    "kssSSSSssk",
    "ksSwwwwSsk",
    "ksSwSwSSsk",
    "ksSSSSSSsk",
    "ksSwSwSSsk",
    "kssSSSSssk",
    "kssssssssk",
    "kkkkkkkkkk",
    "..........",
  ],
  campfire: [
    "...koook...",
    "..koyoyok..",
    ".koyrrryok.",
    ".koyryyrok.",
    "..koyyok...",
    "...kook....",
    ".kntkkntk..",
    "kntntkntntk",
    ".kntkkntk..",
    "...........",
    "...........",
    "...........",
  ],
  crystal: [
    "....kk....",
    "...kmck...",
    "..kmccmk..",
    ".kmcccmck.",
    ".kmcmccmk.",
    "..kmcmcmk.",
    "...kmcmk..",
    "....kmk...",
    ".....k....",
    "..........",
    "..........",
    "..........",
  ],
  skull: [
    "..kkkkkkk..",
    ".kwwwwwwwk.",
    "kwwkwwkwwwk",
    "kwwkwwkwwwk",
    "kwwwwwwwwwk",
    ".kwkwkwkwk.",
    "..kwwwwwk..",
    "...kkkkk...",
    "...........",
    "...........",
    "...........",
    "...........",
  ],
  iceShard: [
    "....kk....",
    "...kWWk...",
    "..kWcWWk..",
    "..kWcccWk.",
    "..kWccWk..",
    "...kcWk...",
    "....kk....",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
  ],
};

export function Landmark({ kind, scale = 3, ...rest }) {
  const m = LM[kind] || LM.tree;
  return <PxSprite map={m} scale={scale} {...rest} />;
}

export function Slash({ size = 36, color = "#ff3c5c" }) {
  return (
    <svg width={size} height={size} style={{ position: "absolute" }} viewBox="0 0 16 16">
      <g shapeRendering="crispEdges">
        {[[2,7],[3,6],[4,5],[5,4],[6,3],[7,2],[3,7],[4,6],[5,5],[6,4],[7,3],
          [9,8],[10,9],[11,10],[12,11],[13,12],[14,13],[10,8],[11,9],[12,10],[13,11]].map(([x,y],i) =>
          <rect key={i} x={x} y={y} width="1" height="1" fill={color} />
        )}
      </g>
    </svg>
  );
}

export function Impact({ size = 30, color = "#ffd23c" }) {
  return (
    <svg width={size} height={size} style={{ position: "absolute" }} viewBox="0 0 16 16">
      <g shapeRendering="crispEdges" fill={color}>
        <rect x="7" y="2" width="2" height="3" />
        <rect x="7" y="11" width="2" height="3" />
        <rect x="2" y="7" width="3" height="2" />
        <rect x="11" y="7" width="3" height="2" />
        <rect x="3" y="3" width="2" height="2" />
        <rect x="11" y="11" width="2" height="2" />
        <rect x="11" y="3" width="2" height="2" />
        <rect x="3" y="11" width="2" height="2" />
        <rect x="6" y="6" width="4" height="4" fill="#fff" />
      </g>
    </svg>
  );
}

export function Fireball({ direction = 1 }) {
  return (
    <svg width="28" height="16" style={{ position: "absolute", transform: direction === -1 ? "scaleX(-1)" : "none" }} viewBox="0 0 28 16">
      <g shapeRendering="crispEdges">
        <rect x="0" y="6" width="3" height="1" fill="#ffd23c" />
        <rect x="0" y="9" width="3" height="1" fill="#ffd23c" />
        <rect x="3" y="5" width="3" height="6" fill="#ff8c3c" />
        <rect x="6" y="3" width="6" height="10" fill="#ff3c5c" />
        <rect x="12" y="2" width="10" height="12" fill="#ff8c3c" />
        <rect x="14" y="4" width="6" height="8" fill="#ffd23c" />
        <rect x="16" y="6" width="2" height="4" fill="#fff" />
        <rect x="22" y="3" width="2" height="10" fill="#ff3c5c" />
        <rect x="24" y="5" width="2" height="6" fill="#ff8c3c" />
      </g>
    </svg>
  );
}

export function ArenaBg({ theme = "forest" }) {
  if (theme === "forest") {
    return (
      <>
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, #1a3a4a 0%, #0a2a1a 50%, #0a1a05 100%)" }} />
        <svg viewBox="0 0 200 50" preserveAspectRatio="none" width="100%" height="50%" style={{ position: "absolute", top: "10%", opacity: 0.7 }}>
          <polygon points="0,50 30,15 50,25 80,5 110,20 140,10 170,22 200,18 200,50" fill="#1a2a3a" stroke="#000" strokeWidth="0.5" />
          <polygon points="0,50 25,30 60,35 90,22 120,32 160,28 200,33 200,50" fill="#0a1a2a" />
        </svg>
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "30%", background: "repeating-linear-gradient(90deg, #0a3a1a 0 12px, #1a4a22 12px 24px)", borderTop: "3px solid #3cffa0" }} />
      </>
    );
  }
  if (theme === "ruins") {
    return (
      <>
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, #4a2a4a 0%, #2a1a3a 50%, #1a0a22 100%)" }} />
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "30%", background: "repeating-linear-gradient(45deg, #3a2a1a 0 8px, #2a1a0a 8px 16px)", borderTop: "3px solid #ff8c3c" }} />
      </>
    );
  }
  if (theme === "ice") {
    return (
      <>
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, #0a3a4a 0%, #0a2a4a 60%, #1a4a6a 100%)" }} />
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "30%", background: "repeating-linear-gradient(90deg, #9ed7ff 0 12px, #c0e8ff 12px 24px)", borderTop: "3px solid #3cf0ff" }} />
      </>
    );
  }
  return null;
}

export const ARENA_LANDMARKS = {
  forest: [
    { kind: "tree", left: "5%", bottom: 95, scale: 3 },
    { kind: "pineTree", left: "85%", bottom: 105, scale: 3 },
    { kind: "boulder", left: "78%", bottom: 50, scale: 2.5 },
    { kind: "tree", left: "60%", bottom: 145, scale: 2 },
    { kind: "campfire", left: "12%", bottom: 50, scale: 2.5 },
  ],
  ruins: [
    { kind: "pillar", left: "8%", bottom: 70, scale: 3.5 },
    { kind: "pillar", left: "82%", bottom: 70, scale: 3.5 },
    { kind: "tombstone", left: "30%", bottom: 50, scale: 2 },
    { kind: "skull", left: "55%", bottom: 50, scale: 2 },
    { kind: "campfire", left: "70%", bottom: 50, scale: 2 },
  ],
  ice: [
    { kind: "iceShard", left: "10%", bottom: 60, scale: 3 },
    { kind: "iceShard", left: "85%", bottom: 60, scale: 3 },
    { kind: "crystal", left: "30%", bottom: 50, scale: 2.5 },
    { kind: "crystal", left: "62%", bottom: 50, scale: 3 },
    { kind: "boulder", left: "75%", bottom: 95, scale: 2 },
  ],
};
