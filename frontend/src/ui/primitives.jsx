// Pixel-art primitives for BYTE WARS — adapted from design handoff to ES modules.

const PALETTE = {
  ".": "transparent",
  "0": "#0a0a12",
  "1": "#1a1a2a",
  "k": "#000000",
  "w": "#e8e8f5",
  "s": "#9a9ab5",
  "a": "#b6ff3c", "A": "#1d3300",
  "m": "#ff3cd0", "M": "#4d0036",
  "c": "#3cf0ff", "C": "#003a40",
  "y": "#ffd23c", "Y": "#4d3a00",
  "r": "#ff3c5c", "R": "#4d0010",
  "p": "#9b3cff", "P": "#28004d",
  "o": "#ff8c3c", "O": "#4d2200",
  "b": "#3c5cff", "B": "#0a0a3a",
  "n": "#ff9ec0", "N": "#7a3a55",
  "g": "#3cffa0", "G": "#003a22",
};

export const SPRITES = {
  tank: [
    "................",
    ".....kkkkkk.....",
    "....kssssssk....",
    "...kswwwwsssk...",
    "...kswkwwksws...",
    "...kssssssssk...",
    "....kkssssk.....",
    "...kssaaaask....",
    "..kkaakaaakak...",
    "..kakaaaakkak...",
    "..kakaaaaakk....",
    "..kakaaaaak.....",
    "...kkaaaak......",
    "....kskskk......",
    "....ks.ks.......",
    "....kk..kk......",
  ],
  assassin: [
    "................",
    "....kkkkkk......",
    "...kpppppk......",
    "..kpppmmmpk.....",
    "..kpmwkmkpk.....",
    "..kpmmmmmpk.....",
    "...kpmmmpk......",
    "...kpppppk......",
    "..kkpkkkpkk.....",
    ".kpkkpppkkpk....",
    ".kpkpppppkpk....",
    "..kkppmppkk.....",
    "...kpppppk......",
    "....kpkkpk......",
    "....kk.kk.......",
    "................",
  ],
  mage: [
    ".......kk.......",
    "......kbkk......",
    ".....kbbbk......",
    "....kbbcbbk.....",
    "...kbcccccbk....",
    "...kkbcwcbkk....",
    "....kssssssk....",
    "...kswkwksws....",
    "...ksskssssk....",
    "..kkccsssccck...",
    ".kcckccccckck...",
    ".kckcccccckck...",
    ".kckkcccckkck...",
    "..kkkccckkk.....",
    "....kkkkkk......",
    "....kk..kk......",
  ],
  ranger: [
    "................",
    ".....kgggk......",
    "....kggggggk....",
    "...kgyyyggsg....",
    "...kgykykgsgs...",
    "...kggggggggk...",
    "....kssssssk....",
    "...kssgggsk.....",
    "..kksskggsskk...",
    ".kgkksgggskgk...",
    ".kgkggggggkgk...",
    "..kkggsgsggk....",
    "...kgsgsgsk.....",
    "....kskskk......",
    "....kk.kk.......",
    "................",
  ],
  support: [
    "................",
    ".....kyyyk......",
    "....kyywyyk.....",
    "...kywwkwwyk....",
    "...kywkwkwyk....",
    "...kyywwwwyk....",
    "....kkyyyk......",
    "...kkmmmmmkk....",
    "..kmkmmmmmkmk...",
    ".kmkmymmmmkmk...",
    ".kmkmmmmmmkmk...",
    "..kmmmmmmmmk....",
    "...kkmymmkk.....",
    "....kskskk......",
    "....ks.ks.......",
    "....kk..kk......",
  ],
  knight: [
    "................",
    "......kkkk......",
    ".....kssssk.....",
    "....ksskssk.....",
    "....kskwksk.....",
    "....kssssssk....",
    "....ksss.ssk....",
    "...kssccccss....",
    "..kkckcccckkk...",
    ".kckkccccckck...",
    ".kckcccccckck...",
    "..kkccrcccckk...",
    "...kcccccck.....",
    "....kskkskk.....",
    "....ks..ks......",
    "....kk..kk......",
  ],
};

// Map archetype names from API to sprite names.
export function archetypeSprite(arch) {
  if (!arch) return "tank";
  const a = String(arch).toLowerCase();
  if (a in SPRITES) return a;
  if (a.includes("tank") || a.includes("warrior") || a.includes("brawler")) return "tank";
  if (a.includes("assassin") || a.includes("rogue")) return "assassin";
  if (a.includes("mage") || a.includes("wizard") || a.includes("sorcerer")) return "mage";
  if (a.includes("ranger") || a.includes("hunter") || a.includes("archer")) return "ranger";
  if (a.includes("support") || a.includes("healer") || a.includes("cleric")) return "support";
  return "tank";
}

export function Sprite({
  kind = "tank",
  scale = 6,
  style = {},
  glow = null,
  className = "",
  decorative = false,
  label,
}) {
  const map = SPRITES[kind] || SPRITES.tank;
  const w = map[0].length;
  const h = map.length;
  // Sprites are rendered as <span>-mosaics, so screen readers see no
  // semantic content. Default presentational sprites to aria-hidden;
  // when a sprite is the *only* identifier for a champion, callers
  // pass `label="champion name"` (or the kind) to make it accessible.
  const ariaProps = decorative
    ? { "aria-hidden": "true" }
    : { role: "img", "aria-label": label || `${kind} champion sprite` };
  return (
    <div
      className={`pixelated ${className}`}
      {...ariaProps}
      style={{
        width: w * scale,
        height: h * scale,
        position: "relative",
        filter: glow ? `drop-shadow(0 0 ${scale}px ${glow})` : "none",
        ...style,
      }}
    >
      {map.map((row, y) =>
        [...row].map((ch, x) => {
          const c = PALETTE[ch];
          if (!c || c === "transparent") return null;
          return (
            <span
              key={`${x}-${y}`}
              style={{
                position: "absolute",
                left: x * scale,
                top: y * scale,
                width: scale,
                height: scale,
                background: c,
              }}
            />
          );
        })
      )}
    </div>
  );
}

export const ITEMS = {
  sword: [
    "....k.......",
    "...ksk......",
    "..kssk......",
    "..ksskk.....",
    "..kkss......",
    "...kkssk....",
    "....kkssk...",
    ".....kkssk..",
    "....yykkss..",
    "...kyyykk...",
    "....kyk.....",
    "............",
  ],
  shield: [
    "...kkkkkk...",
    "..ksaaaask..",
    "..kakaaak...",
    "..kaaaaaak..",
    "..kaaakaak..",
    "..kkaaaak...",
    "...kkaak....",
    "....kkk.....",
    "............",
    "............",
    "............",
    "............",
  ],
  staff: [
    ".....km.....",
    "....kmmk....",
    ".....km.....",
    "....kbk.....",
    "...kbbk.....",
    "...kbk......",
    "..kbk.......",
    "..kk........",
    ".kk.........",
    "kk..........",
    "k...........",
    "............",
  ],
  potion: [
    "...kkkk.....",
    "...ksssk....",
    "..kkrrrkk...",
    "..krrrrrk...",
    "..krrwrrk...",
    "..krrrrrk...",
    "..kkrrrkk...",
    "...kkkk.....",
    "............",
    "............",
    "............",
    "............",
  ],
  bow: [
    "....kk......",
    "...kak......",
    "...ka.k.....",
    "..ka..k.....",
    "..ka..k.....",
    "..ka.kk.....",
    "..ka.k......",
    "..ka.k......",
    "...kak......",
    "....kk......",
    "............",
    "............",
  ],
  crown: [
    "..k...k...k.",
    ".kyk.kyk.kyk",
    ".kyykyyykyy.",
    "..kyyyyyyyk.",
    "..kyymymyk..",
    "..kkkkkkk...",
    "............",
    "............",
    "............",
    "............",
    "............",
    "............",
  ],
  chest: [
    "..kkkkkkkk..",
    ".kyyyyyyyk..",
    ".kyykyykyk..",
    ".kykkkkkkk..",
    ".kyooooooyk.",
    ".kyokyykoyk.",
    ".kyooooooyk.",
    ".kkkkkkkkk..",
    "............",
    "............",
    "............",
    "............",
  ],
  coin: [
    "...kkkk.....",
    "..kyyyyk....",
    ".kyykyykk...",
    ".kykwkwykk..",
    ".kykkkkkyk..",
    ".kywwwwwyk..",
    ".kykwkwkyk..",
    "..kyyyyyk...",
    "...kkkkk....",
    "............",
    "............",
    "............",
  ],
  skull: [
    "...kkkkk....",
    "..kwwwwwk...",
    ".kwwkwkwwk..",
    ".kwkwwwkwk..",
    ".kwkwkwkwk..",
    ".kwwwwwwwk..",
    "..kwkwkwk...",
    "...kkkkk....",
    "............",
    "............",
    "............",
    "............",
  ],
  scroll: [
    ".kkkkkkkk...",
    ".kyywwwwyk..",
    ".kykkkkkyk..",
    ".kywkwkwyk..",
    ".kykkkkkyk..",
    ".kywkwkwyk..",
    ".kykkkkkyk..",
    ".kywwwwwyk..",
    ".kkkkkkkk...",
    "............",
    "............",
    "............",
  ],
};

export function ItemIcon({ kind = "sword", scale = 4, style = {}, decorative = false, label }) {
  const map = ITEMS[kind] || ITEMS.sword;
  const w = (map[0] || "............").length;
  const h = map.length;
  const ariaProps = decorative
    ? { "aria-hidden": "true" }
    : { role: "img", "aria-label": label || `${kind} item icon` };
  return (
    <div className="pixelated" {...ariaProps} style={{ width: w * scale, height: h * scale, position: "relative", ...style }}>
      {map.map((row, y) =>
        [...row].map((ch, x) => {
          const c = PALETTE[ch];
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

export function HPBar({ value = 1, segments = 20, mode = "auto" }) {
  const filled = Math.max(0, Math.min(segments, Math.round(value * segments)));
  const cls = mode === "auto"
    ? value > 0.5 ? "" : value > 0.25 ? "hp-mid" : "hp-dmg"
    : mode;
  return (
    <div className={`hpbar ${cls}`}>
      {Array.from({ length: segments }).map((_, i) => (
        <i key={i} className={i < filled ? "" : "off"} />
      ))}
    </div>
  );
}

export function APBar({ value = 3, max = 3 }) {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {Array.from({ length: max }).map((_, i) => (
        <span key={i} className={`ap-pip ${i < value ? "" : "off"}`} />
      ))}
    </div>
  );
}

export function Pill({ children, color = "var(--bw-line)", textColor, style }) {
  return (
    <span style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      padding: "4px 8px",
      fontFamily: "var(--font-pixel)",
      fontSize: 8,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      background: color,
      color: textColor || "#0a0a12",
      boxShadow: "inset -1px -1px 0 0 #000, inset 1px 1px 0 0 rgba(255,255,255,0.3)",
      ...style,
    }}>{children}</span>
  );
}

export function PixelButton({
  variant = "default", children, onClick, type = "button",
  style, full = false, disabled = false, title,
  "aria-label": ariaLabel,
}) {
  const cls = "pxbtn" + (variant !== "default" ? " pxbtn-" + variant : "");
  return (
    <button
      type={type}
      className={cls}
      onClick={onClick}
      disabled={disabled}
      title={title}
      aria-label={ariaLabel}
      style={{
        width: full ? "100%" : undefined,
        opacity: disabled ? 0.4 : 1,
        ...style,
      }}
    >{children}</button>
  );
}

export function Stat({ label, value, color = "var(--bw-acid)" }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 11 }}>
      <span style={{ color: "var(--bw-ink-dim)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</span>
      <span style={{ color, fontWeight: 800 }}>{value}</span>
    </div>
  );
}

export function Slot({ filled, children, style, onClick, label }) {
  return (
    <div
      onClick={onClick}
      style={{
        width: 56, height: 56,
        background: filled ? "var(--bw-bg-3)" : "transparent",
        backgroundImage: filled ? undefined : "repeating-linear-gradient(45deg, #1a1a2a 0 4px, #11111c 4px 8px)",
        boxShadow: filled
          ? "inset -2px -2px 0 0 #000, inset 2px 2px 0 0 var(--bw-line-2)"
          : "inset 0 0 0 2px var(--bw-line)",
        display: "flex", alignItems: "center", justifyContent: "center",
        cursor: onClick ? "pointer" : "default",
        position: "relative",
        ...style,
      }}
    >
      {children}
      {label && (
        <div style={{
          position: "absolute", bottom: -16, left: 0, right: 0, textAlign: "center",
          fontFamily: "var(--font-pixel)", fontSize: 7, color: "var(--bw-ink-low)",
          textTransform: "uppercase", letterSpacing: "0.1em",
        }}>{label}</div>
      )}
    </div>
  );
}

export function rarityColor(r) {
  return ({
    common: "var(--bw-rarity-common)",
    uncommon: "var(--bw-rarity-uncommon)",
    rare: "var(--bw-rarity-rare)",
    epic: "var(--bw-rarity-epic)",
    legendary: "var(--bw-rarity-legendary)",
  })[r] || "var(--bw-line)";
}

export function Divider({ color = "var(--bw-line)", style }) {
  return <div style={{ height: 2, background: color, boxShadow: "0 2px 0 0 #000", margin: "8px 0", ...style }} />;
}

export function Ticker({ items = [] }) {
  const repeated = [...items, ...items];
  return (
    <div style={{
      overflow: "hidden",
      background: "#000",
      borderTop: "2px solid var(--bw-line)",
      borderBottom: "2px solid var(--bw-line)",
      padding: "6px 0",
    }}>
      <div className="marquee" style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--bw-acid)" }}>
        {repeated.map((it, i) => (
          <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
            <span style={{ color: "var(--bw-magenta)" }}>◆</span>
            {it}
          </span>
        ))}
      </div>
    </div>
  );
}

export function Panel({ children, sunken = false, style, className = "" }) {
  return (
    <div className={`${sunken ? "panel-sunken" : "panel"} ${className}`} style={{ padding: 14, ...style }}>
      {children}
    </div>
  );
}

export function GlowText({ color = "acid", children, style }) {
  return <span className={`glow-${color}`} style={{ fontFamily: "var(--font-pixel)", ...style }}>{children}</span>;
}

// SOL / coin diamond
export function SolDiamond({ color = "var(--bw-yellow)", size = 8 }) {
  return <span style={{ display: "inline-block", width: size, height: size, transform: "rotate(45deg)", background: color, boxShadow: "inset 0 0 0 1px #000" }} />;
}
