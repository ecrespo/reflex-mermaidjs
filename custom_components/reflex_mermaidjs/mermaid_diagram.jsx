/**
 * React wrapper around mermaid-js used by the `reflex-mermaidjs` custom component.
 *
 * Responsibilities:
 * - Lazily load mermaid (browser only) and its optional plugins
 *   (tidy-tree layout, ZenUML diagram, iconify icon packs, Font Awesome CSS).
 * - Serialize renders through a global queue, because `mermaid.initialize`
 *   and `mermaid.render` share global state and are not re-entrant.
 * - Render the diagram text into SVG, bind interactive functions
 *   (`click` directives), and report results/errors back to Reflex.
 * - Provide pan & zoom, a floating toolbar, and an imperative API
 *   (`window.__reflexMermaid[id]`) used by the Python action helpers
 *   (zoom, fit, export SVG/PNG, copy SVG, ...).
 */
import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Module level: mermaid loading, plugin registration and the render queue.
// ---------------------------------------------------------------------------

let mermaidPromise = null;
const registered = { tidyTree: false, zenuml: false, iconPacks: new Set(), fontAwesome: false, katex: false };
let renderQueue = Promise.resolve();
let idCounter = 0;

const STYLE_ID = "reflex-mermaid-styles";
const ensureStyles = () => {
  if (typeof document === "undefined" || document.getElementById(STYLE_ID)) return;
  const el = document.createElement("style");
  el.id = STYLE_ID;
  el.textContent = `
.reflex-mermaid[data-pan-zoom="true"] .reflex-mermaid-canvas > svg { width: 100% !important; height: 100% !important; max-width: none !important; display: block; }
.reflex-mermaid-controls button:hover { background: rgba(127,127,127,0.25) !important; }
.reflex-mermaid:fullscreen { background: var(--mermaid-fullscreen-bg, Canvas); }
`;
  document.head.appendChild(el);
};

/** Well-known iconify packs that can be referenced by name. */
const ICONIFY_CDN = "https://cdn.jsdelivr.net/npm/@iconify-json";

const loadMermaid = () => {
  if (!mermaidPromise) {
    mermaidPromise = import("mermaid").then((mod) => {
      const mermaid = mod.default ?? mod;
      // Never let mermaid scan the page on its own: every render is explicit.
      mermaid.initialize({ startOnLoad: false });
      return mermaid;
    });
  }
  return mermaidPromise;
};

const ensurePlugins = async (mermaid, { tidyTree, zenuml, iconPacks, fontAwesome, math }) => {
  if (tidyTree && !registered.tidyTree) {
    const mod = await import("@mermaid-js/layout-tidy-tree");
    mermaid.registerLayoutLoaders(mod.default ?? mod);
    registered.tidyTree = true;
  }
  if (zenuml && !registered.zenuml) {
    const mod = await import("@mermaid-js/mermaid-zenuml");
    await mermaid.registerExternalDiagrams([mod.default ?? mod]);
    registered.zenuml = true;
  }
  if (fontAwesome && !registered.fontAwesome) {
    try {
      await import("@fortawesome/fontawesome-free/css/all.min.css");
    } catch (err) {
      console.warn("[reflex-mermaidjs] Could not load Font Awesome CSS", err);
    }
    registered.fontAwesome = true;
  }
  if (math && !registered.katex) {
    try {
      await import("katex/dist/katex.min.css");
    } catch (err) {
      console.warn("[reflex-mermaidjs] Could not load KaTeX CSS", err);
    }
    registered.katex = true;
  }
  const packs = normalizeIconPacks(iconPacks).filter((p) => !registered.iconPacks.has(p.name));
  if (packs.length) {
    mermaid.registerIconPacks(
      packs.map((p) => ({
        name: p.name,
        loader: () =>
          loadIconPack(p)
            .catch((err) => {
              console.warn(`[reflex-mermaidjs] Icon pack "${p.name}" failed to load`, err);
              return { prefix: p.name, icons: {} };
            }),
      }))
    );
    packs.forEach((p) => registered.iconPacks.add(p.name));
  }
};

/** Packs bundled as npm dependencies: loaded from the app bundle, no network needed. */
const BUNDLED_ICON_PACKS = {
  logos: () => import("@iconify-json/logos/icons.json"),
  mdi: () => import("@iconify-json/mdi/icons.json"),
};

const loadIconPack = async (pack) => {
  if (pack.bundled) {
    const mod = await BUNDLED_ICON_PACKS[pack.name]();
    return mod.default ?? mod;
  }
  const res = await fetch(pack.url);
  return res.json();
};

const normalizeIconPacks = (iconPacks) => {
  if (!iconPacks) return [];
  return iconPacks
    .map((pack) => {
      if (typeof pack === "string") {
        if (BUNDLED_ICON_PACKS[pack]) return { name: pack, bundled: true };
        return { name: pack, url: `${ICONIFY_CDN}/${pack}@1/icons.json` };
      }
      if (pack && pack.name) {
        return {
          name: pack.name,
          url: pack.url ?? `${ICONIFY_CDN}/${pack.pack ?? pack.name}@1/icons.json`,
        };
      }
      return null;
    })
    .filter(Boolean);
};

/**
 * Some diagram renderers (e.g. block) eagerly `JSON.stringify` d3 selections that
 * reference `<html>`. React attaches circular fiber properties to elements it
 * manages, which makes that call throw. While a render runs, retry circular
 * stringify calls with a replacer that drops DOM nodes and cycles. Calls that
 * succeed normally are untouched.
 */
const nativeStringify = JSON.stringify;
const safeReplacer = (replacer) => {
  const seen = new WeakSet();
  return function (key, value) {
    if (typeof key === "string" && key.startsWith("__react")) return undefined;
    if (typeof Node !== "undefined" && value instanceof Node) return undefined;
    if (value && typeof value === "object") {
      if (seen.has(value)) return "[Circular]";
      seen.add(value);
    }
    return typeof replacer === "function" ? replacer.call(this, key, value) : value;
  };
};
const tolerantStringify = function (value, replacer, space) {
  try {
    return nativeStringify(value, replacer, space);
  } catch (err) {
    if (err instanceof TypeError && /circular/i.test(err.message)) {
      return nativeStringify(value, safeReplacer(replacer), space);
    }
    throw err;
  }
};
const withTolerantStringify = async (fn) => {
  JSON.stringify = tolerantStringify;
  try {
    return await fn();
  } finally {
    JSON.stringify = nativeStringify;
  }
};

/** Run `task` after every previously queued render has settled. */
const enqueue = (task) => {
  const run = renderQueue.then(task, task);
  renderQueue = run.catch(() => undefined);
  return run;
};

// Diagram ids (as reported by mermaid.parse) whose config section is named differently.
const CONFIG_SECTION_ALIASES = {
  classDiagram: "class",
  "flowchart-elk": "flowchart",
  "flowchart-v2": "flowchart",
  railroadAbnf: "railroad",
  railroadEbnf: "railroad",
  railroadPeg: "railroad",
  stateDiagram: "state",
  xychart: "xyChart",
};

/** Mermaid's default theme for a diagram type (its config section's, else the global one). */
const defaultThemeFor = (mermaid, diagramType) => {
  const defaults = mermaid.mermaidAPI?.defaultConfig ?? {};
  const section = defaults[CONFIG_SECTION_ALIASES[diagramType] ?? diagramType];
  return (section && typeof section.theme === "string" && section.theme) || defaults.theme || "default";
};

/** Dark counterpart of a theme: redux themes have -dark variants, anything else uses `dark`. */
const darkVariantOf = (theme) => {
  if (theme.includes("dark")) return theme;
  return theme.startsWith("redux") ? theme.replace("redux", "redux-dark") : "dark";
};

/** True when the diagram front matter or an init directive already sets a theme. */
const textSetsTheme = (text) => /(^|\n)\s*theme\s*:|%%\{\s*init[^}]*theme/.test(text);

const stripUndefined = (obj) =>
  Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== ""));

/** Best-effort extraction of the diagram-level node id from an SVG element id. */
const nodeIdFromElement = (el, svgId) => {
  const dataId = el.getAttribute("data-id");
  if (dataId) return dataId;
  let raw = el.id || "";
  if (svgId && raw.startsWith(`${svgId}-`)) raw = raw.slice(svgId.length + 1);
  const match = raw.match(/^(?:flowchart|state|classId|entity|node|swimlane|agentflow)-(.+?)-\d+$/);
  if (match) return match[1];
  return raw;
};

const NODE_SELECTOR = [
  "g.node",
  "g.cluster",
  "g.classGroup",
  "g.actor",
  "rect.actor",
  "g.statediagram-state",
  "g.er.entityBox",
  "g.mindmap-node",
  "g.architecture-service",
  "g.task",
  "g.commit",
  "g.pieCircle",
  "path.pieCircle",
  "g.kanban-item",
].join(",");

const downloadHref = (filename, href) => {
  const a = document.createElement("a");
  a.download = filename;
  a.href = href;
  document.body.appendChild(a);
  a.click();
  a.remove();
};

const svgToString = (svgEl, { width, height, background } = {}) => {
  const clone = svgEl.cloneNode(true);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
  clone.removeAttribute("style");
  if (width) clone.setAttribute("width", `${width}`);
  if (height) clone.setAttribute("height", `${height}`);
  if (background) clone.style.backgroundColor = background;
  return clone.outerHTML
    .replaceAll("<br>", "<br/>")
    .replaceAll(/<img([^>]*?)\/?>/g, (m, g) => `<img${g}/>`);
};

const toBase64 = (text) => {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary);
};

const naturalSize = (svgEl) => {
  const vb = svgEl.viewBox?.baseVal;
  if (vb && vb.width && vb.height) return { width: vb.width, height: vb.height };
  const box = svgEl.getBBox?.();
  return { width: box?.width || 300, height: box?.height || 150 };
};

// ---------------------------------------------------------------------------
// Toolbar icons (inline SVG, no extra dependency).
// ---------------------------------------------------------------------------

const Icon = ({ d }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {d.map((p, i) => <path key={i} d={p} />)}
  </svg>
);
const ICONS = {
  zoomIn: ["M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14", "M21 21l-4.3-4.3", "M11 8v6", "M8 11h6"],
  zoomOut: ["M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14", "M21 21l-4.3-4.3", "M8 11h6"],
  fit: ["M3 8V5a2 2 0 0 1 2-2h3", "M16 3h3a2 2 0 0 1 2 2v3", "M21 16v3a2 2 0 0 1-2 2h-3", "M8 21H5a2 2 0 0 1-2-2v-3"],
  reset: ["M3 12a9 9 0 1 0 3-6.7", "M3 4v5h5"],
  fullscreen: ["M15 3h6v6", "M9 21H3v-6", "M21 3l-7 7", "M3 21l7-7"],
};

// ---------------------------------------------------------------------------
// The component.
// ---------------------------------------------------------------------------

export function MermaidDiagram({
  id,
  className,
  style,
  chart = "",
  config,
  theme,
  look,
  layout,
  securityLevel,
  fontFamily,
  fontSize,
  handDrawnSeed,
  darkMode,
  htmlLabels,
  maxTextSize,
  maxEdges,
  wrap,
  deterministicIds,
  logLevel,
  themeVariables,
  themeCss,
  appearance = "light",
  debounce = 0,
  tidyTree = true,
  zenuml = false,
  fontAwesome = true,
  iconPacks = ["logos", "mdi"],
  panZoom = false,
  showControls,
  controlsPosition = "top-right",
  minZoom = 0.1,
  maxZoom = 10,
  zoomStep = 0.2,
  fitOnRender = "auto",
  maxFitZoom = 1,
  grid = false,
  errorMode = "inline",
  clickCallbacks,
  nodeClick = false,
  center = true,
  onRender,
  onError,
  onNodeClick,
  onZoomChange,
}) {
  const instanceId = useMemo(() => {
    idCounter += 1;
    const base = (id || "mermaid").toString().replace(/[^a-zA-Z0-9_-]/g, "_");
    return `${base}-svg-${idCounter}`;
  }, [id]);
  const rootRef = useRef(null);
  const viewportRef = useRef(null);
  const canvasRef = useRef(null);
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const dragRef = useRef(null);
  const renderSeq = useRef(0);
  const lastFit = useRef(null);
  const zoomTimer = useRef(null);
  const callbacksRef = useRef({ onRender, onError, onNodeClick, onZoomChange });
  callbacksRef.current = { onRender, onError, onNodeClick, onZoomChange };

  const [svg, setSvg] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const [debouncedChart, setDebouncedChart] = useState(chart);
  const [svgVersion, setSvgVersion] = useState(0);
  const pendingRef = useRef(null);
  const [svgSize, setSvgSize] = useState(null);

  // Debounce the diagram text for live-editing scenarios.
  useEffect(() => {
    if (!debounce) {
      setDebouncedChart(chart);
      return undefined;
    }
    const handle = setTimeout(() => setDebouncedChart(chart), debounce);
    return () => clearTimeout(handle);
  }, [chart, debounce]);

  const mermaidConfig = useMemo(
    () => ({
      ...(config || {}),
      ...stripUndefined({
        suppressErrorRendering: true,
        theme,
        look,
        layout,
        securityLevel,
        fontFamily,
        fontSize,
        handDrawnSeed,
        darkMode,
        htmlLabels,
        maxTextSize,
        maxEdges,
        wrap,
        deterministicIds,
        logLevel,
        themeVariables:
          themeVariables || config?.themeVariables
            ? { ...(config?.themeVariables || {}), ...(themeVariables || {}) }
            : undefined,
        themeCSS: themeCss,
      }),
      startOnLoad: false,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(config), theme, look, layout, securityLevel, fontFamily, fontSize,
      handDrawnSeed, darkMode, htmlLabels, maxTextSize, maxEdges, wrap, deterministicIds,
      logLevel, JSON.stringify(themeVariables), themeCss]
  );
  const iconPacksKey = JSON.stringify(iconPacks || []);

  // --- Pan & zoom helpers ---------------------------------------------------
  const applyTransform = useCallback((next) => {
    const k = Math.min(maxZoom, Math.max(minZoom, next.k));
    const t = { x: next.x, y: next.y, k };
    transformRef.current = t;
    setTransform(t);
    if (callbacksRef.current.onZoomChange) {
      // Debounced so wheel/drag gestures do not flood the backend with events.
      clearTimeout(zoomTimer.current);
      zoomTimer.current = setTimeout(() => {
        callbacksRef.current.onZoomChange?.({ zoom: Math.round(k * 1000) / 1000, x: Math.round(t.x), y: Math.round(t.y) });
      }, 150);
    }
  }, [minZoom, maxZoom]);

  const svgElement = () => canvasRef.current?.querySelector("svg") ?? null;

  const fit = useCallback((padding = 24) => {
    const viewport = viewportRef.current;
    const svgEl = svgElement();
    if (!viewport || !svgEl) return;
    const { width, height } = naturalSize(svgEl);
    const vw = viewport.clientWidth;
    const vh = viewport.clientHeight;
    if (!vw || !vh) return;
    const k = Math.min((vw - padding * 2) / width, (vh - padding * 2) / height, maxFitZoom);
    applyTransform({ k, x: (vw - width * k) / 2, y: (vh - height * k) / 2 });
  }, [applyTransform, maxFitZoom]);

  const zoomBy = useCallback((factor, cx, cy) => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const { x, y, k } = transformRef.current;
    const px = cx ?? viewport.clientWidth / 2;
    const py = cy ?? viewport.clientHeight / 2;
    const nk = Math.min(maxZoom, Math.max(minZoom, k * factor));
    const ratio = nk / k;
    applyTransform({ k: nk, x: px - (px - x) * ratio, y: py - (py - y) * ratio });
  }, [applyTransform, minZoom, maxZoom]);

  const reset = useCallback(() => {
    const viewport = viewportRef.current;
    const svgEl = svgElement();
    if (!viewport || !svgEl) return;
    const { width, height } = naturalSize(svgEl);
    applyTransform({ k: 1, x: (viewport.clientWidth - width) / 2, y: (viewport.clientHeight - height) / 2 });
  }, [applyTransform]);

  // --- Rendering ------------------------------------------------------------
  useEffect(() => {
    ensureStyles();
    let cancelled = false;
    const seq = ++renderSeq.current;
    const text = (debouncedChart || "").trim();
    if (!text) {
      setSvg("");
      setError(null);
      setLoading(false);
      return undefined;
    }
    setLoading(true);
    const started = performance.now();
    enqueue(async () => {
      const mermaid = await loadMermaid();
      await ensurePlugins(mermaid, {
        tidyTree,
        zenuml: zenuml || /^\s*(---[\s\S]*?---\s*)?zenuml/.test(text),
        iconPacks,
        fontAwesome,
        math: /\$\$/.test(text),
      });
      if (cancelled || seq !== renderSeq.current) return null;
      let effectiveConfig = mermaidConfig;
      if (appearance === "dark" && !mermaidConfig.theme && !textSetsTheme(text)) {
        // Like mermaid.live: use the dark variant of the diagram type's default theme.
        mermaid.initialize(mermaidConfig);
        const parsed = await mermaid.parse(text);
        if (parsed && parsed.diagramType) {
          effectiveConfig = { ...mermaidConfig, theme: darkVariantOf(defaultThemeFor(mermaid, parsed.diagramType)) };
        }
      }
      mermaid.initialize(effectiveConfig);
      const renderId = `${instanceId}-${seq}`;
      const result = await withTolerantStringify(() => mermaid.render(renderId, text));
      return { ...result, renderId };
    })
      .then((result) => {
        if (!result || cancelled || seq !== renderSeq.current) return;
        pendingRef.current = { ...result, started };
        setSvg(result.svg);
        setError(null);
        setLoading(false);
        setSvgVersion((v) => v + 1);
      })
      .catch((err) => {
        if (cancelled || seq !== renderSeq.current) return;
        const message = (err && (err.message || err.str)) || String(err);
        // mermaid may leave a temporary element behind on failure.
        document.getElementById(`d${instanceId}-${seq}`)?.remove();
        setError(message);
        setLoading(false);
        if (errorMode !== "keep-last") setSvg("");
        callbacksRef.current.onError?.({
          message,
          line: err?.hash?.loc?.first_line ?? err?.hash?.line ?? null,
          expected: err?.hash?.expected ?? null,
        });
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedChart, mermaidConfig, appearance, tidyTree, zenuml, fontAwesome, iconPacksKey, instanceId, panZoom]);

  // Post-process the SVG once React has committed it to the DOM.
  useLayoutEffect(() => {
    const result = pendingRef.current;
    const container = canvasRef.current;
    if (!result || !container) return;
    pendingRef.current = null;
    result.bindFunctions?.(container);
    const svgEl = container.querySelector("svg");
    if (svgEl && panZoom) {
      const { width, height } = naturalSize(svgEl);
      setSvgSize({ width, height });
      const last = lastFit.current;
      const changedType = last && last.type !== result.diagramType;
      const resized =
        last &&
        (Math.abs(width - last.width) / Math.max(last.width, 1) > 0.4 ||
          Math.abs(height - last.height) / Math.max(last.height, 1) > 0.4);
      const shouldFit =
        fitOnRender === true ||
        !last ||
        (fitOnRender === "auto" && (changedType || resized));
      if (shouldFit) {
        // Wait for the canvas size to be committed before measuring.
        requestAnimationFrame(() => fit());
        lastFit.current = { type: result.diagramType, width, height };
      }
    }
    callbacksRef.current.onRender?.({
      svg: result.svg,
      diagram_type: result.diagramType,
      render_id: result.renderId,
      render_ms: Math.round(performance.now() - result.started),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [svgVersion]);

  // --- `click nodeId callback` directives ------------------------------------
  const callbacksKey = JSON.stringify(clickCallbacks || []);
  useEffect(() => {
    const names = clickCallbacks || [];
    const previous = {};
    names.forEach((name) => {
      previous[name] = window[name];
      window[name] = (nodeId, ...args) => {
        callbacksRef.current.onNodeClick?.({ node_id: nodeId, callback: name, label: null, args });
      };
    });
    return () => {
      names.forEach((name) => {
        if (previous[name] === undefined) delete window[name];
        else window[name] = previous[name];
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callbacksKey]);

  // --- Generic node clicks ----------------------------------------------------
  const handleCanvasClick = useCallback((event) => {
    if (!nodeClick || dragRef.current?.moved) return;
    const target = event.target.closest?.(NODE_SELECTOR);
    if (!target || !canvasRef.current?.contains(target)) return;
    const svgEl = svgElement();
    callbacksRef.current.onNodeClick?.({
      node_id: nodeIdFromElement(target, svgEl?.id),
      callback: null,
      label: (target.textContent || "").trim(),
      args: [],
    });
  }, [nodeClick]);

  // --- Pointer interactions for pan & zoom -------------------------------------
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport || !panZoom) return undefined;
    const onWheel = (event) => {
      event.preventDefault();
      const rect = viewport.getBoundingClientRect();
      const factor = Math.exp(-event.deltaY * 0.0015);
      zoomBy(factor, event.clientX - rect.left, event.clientY - rect.top);
    };
    viewport.addEventListener("wheel", onWheel, { passive: false });
    return () => viewport.removeEventListener("wheel", onWheel);
  }, [panZoom, zoomBy]);

  const onPointerDown = (event) => {
    if (!panZoom || event.button !== 0) return;
    dragRef.current = {
      startX: event.clientX,
      startY: event.clientY,
      origin: { ...transformRef.current },
      moved: false,
      pointerId: event.pointerId,
    };
  };
  const onPointerMove = (event) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    if (!drag.moved && Math.hypot(dx, dy) > 3) {
      drag.moved = true;
      event.currentTarget.setPointerCapture?.(event.pointerId);
    }
    if (drag.moved) applyTransform({ ...drag.origin, x: drag.origin.x + dx, y: drag.origin.y + dy });
  };
  const onPointerUp = (event) => {
    const drag = dragRef.current;
    if (!drag) return;
    event.currentTarget.releasePointerCapture?.(event.pointerId);
    // Keep `moved` visible to the click handler fired right after pointerup.
    setTimeout(() => {
      dragRef.current = null;
    }, 0);
  };

  // Refit when the viewport is resized.
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport || !panZoom || typeof ResizeObserver === "undefined") return undefined;
    let first = true;
    const observer = new ResizeObserver(() => {
      if (first) {
        first = false;
        return;
      }
      if (fitOnRender) fit();
    });
    observer.observe(viewport);
    return () => observer.disconnect();
  }, [panZoom, fit, fitOnRender]);

  // --- Imperative API -----------------------------------------------------------
  const exportPng = useCallback(async (filename = "diagram.png", scale = 2, background = "white") => {
    const svgEl = svgElement();
    if (!svgEl) return null;
    const { width, height } = naturalSize(svgEl);
    const canvas = document.createElement("canvas");
    canvas.width = Math.ceil(width * scale);
    canvas.height = Math.ceil(height * scale);
    const ctx = canvas.getContext("2d");
    if (background && background !== "transparent") {
      ctx.fillStyle = background;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    const image = new Image();
    image.crossOrigin = "anonymous";
    const src = `data:image/svg+xml;base64,${toBase64(svgToString(svgEl, { width: canvas.width, height: canvas.height }))}`;
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = reject;
      image.src = src;
    });
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/png");
    if (filename) downloadHref(filename, dataUrl);
    return dataUrl;
  }, []);

  useEffect(() => {
    if (!id) return undefined;
    window.__reflexMermaid = window.__reflexMermaid || {};
    const api = {
      zoomIn: () => zoomBy(1 + zoomStep),
      zoomOut: () => zoomBy(1 / (1 + zoomStep)),
      setZoom: (k) => zoomBy(k / transformRef.current.k),
      fit: () => fit(),
      reset: () => reset(),
      getSvg: () => {
        const svgEl = svgElement();
        return svgEl ? svgToString(svgEl) : null;
      },
      exportSvg: (filename = "diagram.svg", background) => {
        const svgEl = svgElement();
        if (!svgEl) return null;
        const text = svgToString(svgEl, { background });
        downloadHref(filename, `data:image/svg+xml;base64,${toBase64(text)}`);
        return text;
      },
      exportPng,
      copySvg: async () => {
        const svgEl = svgElement();
        if (!svgEl) return false;
        await navigator.clipboard.writeText(svgToString(svgEl));
        return true;
      },
      fullscreen: () => rootRef.current?.requestFullscreen?.(),
    };
    window.__reflexMermaid[id] = api;
    return () => {
      if (window.__reflexMermaid?.[id] === api) delete window.__reflexMermaid[id];
    };
  }, [id, zoomBy, zoomStep, fit, reset, exportPng]);

  // --- Markup ---------------------------------------------------------------------
  const controlsVisible = showControls ?? panZoom;
  const [vertical, horizontal] = controlsPosition.split("-");
  const gridStyle = grid
    ? {
        backgroundImage: "radial-gradient(circle, var(--mermaid-grid-color, rgba(128,128,128,0.35)) 1px, transparent 1px)",
        backgroundSize: `${20 * (panZoom ? transform.k : 1)}px ${20 * (panZoom ? transform.k : 1)}px`,
        backgroundPosition: panZoom ? `${transform.x}px ${transform.y}px` : "0 0",
      }
    : {};

  const buttonStyle = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: 30,
    height: 30,
    border: "none",
    borderRadius: 6,
    background: "transparent",
    color: "inherit",
    cursor: "pointer",
  };

  return (
    <div
      id={id}
      ref={rootRef}
      className={["reflex-mermaid", className].filter(Boolean).join(" ")}
      data-state={error ? "error" : loading ? "loading" : "ready"}
      data-pan-zoom={panZoom ? "true" : "false"}
      style={{ position: "relative", width: "100%", ...(style || {}) }}
    >
      <div
        ref={viewportRef}
        className="reflex-mermaid-viewport"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={panZoom ? () => fit() : undefined}
        style={{
          position: panZoom ? "absolute" : "relative",
          inset: panZoom ? 0 : undefined,
          overflow: panZoom ? "hidden" : "visible",
          cursor: panZoom ? (dragRef.current?.moved ? "grabbing" : "grab") : undefined,
          touchAction: panZoom ? "none" : undefined,
          ...gridStyle,
        }}
      >
        <div
          ref={canvasRef}
          className="reflex-mermaid-canvas"
          onClick={handleCanvasClick}
          style={
            panZoom
              ? {
                  position: "absolute",
                  left: 0,
                  top: 0,
                  transformOrigin: "0 0",
                  width: svgSize ? `${svgSize.width}px` : undefined,
                  height: svgSize ? `${svgSize.height}px` : undefined,
                  transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.k})`,
                }
              : { display: "flex", justifyContent: center ? "center" : "flex-start" }
          }
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      </div>

      {error && errorMode !== "none" && (
        <div
          className="reflex-mermaid-error"
          role="alert"
          style={{
            position: panZoom ? "absolute" : "relative",
            left: panZoom ? 12 : undefined,
            right: panZoom ? 12 : undefined,
            bottom: panZoom ? 12 : undefined,
            margin: panZoom ? 0 : "8px 0",
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid rgba(229, 72, 77, 0.5)",
            background: "rgba(229, 72, 77, 0.12)",
            color: "#e5484d",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            fontSize: 12,
            whiteSpace: "pre-wrap",
            maxHeight: 180,
            overflow: "auto",
            zIndex: 2,
          }}
        >
          {error}
        </div>
      )}

      {controlsVisible && (
        <div
          className="reflex-mermaid-controls"
          style={{
            position: "absolute",
            [vertical === "bottom" ? "bottom" : "top"]: 12,
            [horizontal === "left" ? "left" : "right"]: 12,
            display: "flex",
            gap: 2,
            padding: 4,
            borderRadius: 10,
            background: "var(--mermaid-controls-bg, rgba(127,127,127,0.18))",
            backdropFilter: "blur(6px)",
            zIndex: 3,
          }}
        >
          <button type="button" title="Fit to view" style={buttonStyle} onClick={() => fit()}><Icon d={ICONS.fit} /></button>
          <button type="button" title="Zoom out" style={buttonStyle} onClick={() => zoomBy(1 / (1 + zoomStep))}><Icon d={ICONS.zoomOut} /></button>
          <button type="button" title="Zoom in" style={buttonStyle} onClick={() => zoomBy(1 + zoomStep)}><Icon d={ICONS.zoomIn} /></button>
          <button type="button" title="Actual size" style={buttonStyle} onClick={() => reset()}><Icon d={ICONS.reset} /></button>
          <button type="button" title="Fullscreen" style={buttonStyle} onClick={() => rootRef.current?.requestFullscreen?.()}><Icon d={ICONS.fullscreen} /></button>
        </div>
      )}
    </div>
  );
}

export default MermaidDiagram;
