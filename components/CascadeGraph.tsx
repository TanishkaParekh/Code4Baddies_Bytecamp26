"use client";
// app/components/CascadeGraph.tsx

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

interface GraphNode { id: string; fx?: number; fy?: number; x?: number; y?: number; }
interface GraphLink { source: string; target: string; severity?: string; cascade?: boolean; }
export interface GraphData { nodes: GraphNode[]; links: GraphLink[]; }
interface Props {
  graphData: GraphData;
  cascadeInvolvedDrugs: string[];
  onNodeClick?: (drugName: string) => void;
}

export function buildPositionedGraph(
  rawGraph: { nodes: { id: string }[]; links: { source: string; target: string; severity?: string; cascade?: boolean }[] },
  cascadePaths: { inhibitors: string[]; substrates: string[]; inducers?: string[] }[]
): GraphData {
  const inhibitorSet = new Set(cascadePaths.flatMap(c => c.inhibitors));
  const substrateSet = new Set(cascadePaths.flatMap(c => c.substrates.filter(s => !inhibitorSet.has(s))));
  const cascadeSet = new Set([...inhibitorSet, ...substrateSet]);
  const inhibitors = rawGraph.nodes.filter(n => inhibitorSet.has(n.id));
  const substrates = rawGraph.nodes.filter(n => substrateSet.has(n.id));
  const safe = rawGraph.nodes.filter(n => !cascadeSet.has(n.id));
  const CY = 130;
  const positioned: GraphNode[] = [
    ...inhibitors.map((n, i) => ({ ...n, fx: 150, fy: CY + (i - (inhibitors.length - 1) / 2) * 90 })),
    ...substrates.map((n, i) => ({ ...n, fx: 400, fy: CY + (i - (substrates.length - 1) / 2) * 90 })),
    ...safe.map((n, i) => ({ ...n, fx: 570, fy: 80 + i * 80 })),
  ];
  const cascadeLinkKeys = new Set(cascadePaths.flatMap(c =>
    c.inhibitors.flatMap(inh => c.substrates.map(sub => `${inh}|${sub}`))
  ));
  const links = rawGraph.links.map(l => ({
    ...l,
    cascade: l.cascade ?? cascadeLinkKeys.has(`${l.source}|${l.target}`),
  }));
  return { nodes: positioned, links };
}

// Pulse ring animation tick
let tick = 0;

export default function CascadeGraph({ graphData, cascadeInvolvedDrugs, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(600);
  const [draggable, setDraggable] = useState(true);
  const frameRef = useRef<number>(0);
  const [, forceUpdate] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;
    setWidth(containerRef.current.offsetWidth);
    const ro = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    ro.observe(containerRef.current);
    // Drive pulse animation
    const animate = () => {
      tick = (tick + 0.04) % (Math.PI * 2);
      forceUpdate(t => t + 1);
      frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => {
      ro.disconnect();
      cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return (
    <div style={{
      background: "linear-gradient(135deg, #0a0a14 0%, #140a0a 60%, #0a0e14 100%)",
      borderRadius: 16,
      overflow: "hidden",
      border: "1px solid rgba(226,75,74,0.2)",
      boxShadow: "0 0 40px rgba(226,75,74,0.05), inset 0 1px 0 rgba(255,255,255,0.04)",
    }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px 8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            width: 8, height: 8, borderRadius: "50%", background: "#E24B4A",
            boxShadow: "0 0 8px rgba(226,75,74,0.9), 0 0 16px rgba(226,75,74,0.4)",
            display: "inline-block",
          }} />
          <span style={{ color: "#f0f0f0", fontSize: 13, fontWeight: 600, letterSpacing: "0.03em" }}>
            Cascade Fingerprint™
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ color: "rgba(255,255,255,0.25)", fontSize: 11 }}>enzyme interaction network</span>
          <button
            onClick={() => setDraggable(d => !d)}
            style={{
              fontSize: 10, padding: "2px 8px", borderRadius: 10, cursor: "pointer", border: "none",
              background: draggable ? "rgba(46,125,138,0.3)" : "rgba(255,255,255,0.08)",
              color: draggable ? "#5DCAA5" : "rgba(255,255,255,0.35)",
              fontFamily: "inherit", transition: "all 0.2s",
            }}
          >
            {draggable ? "⠿ drag on" : "⠿ drag off"}
          </button>
        </div>
      </div>

      {/* Graph canvas */}
      <div ref={containerRef} style={{ height: 300 }}>
        <ForceGraph2D
          graphData={graphData}
          backgroundColor="transparent"
          nodeLabel="id"
          width={width}
          height={300}
          // Allow physics when drag is on so nodes settle naturally after drag
          cooldownTicks={draggable ? 60 : 0}
          enableNodeDrag={draggable}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          onNodeDragEnd={(node: GraphNode) => {
            // Pin node after drag so it stays where placed
            node.fx = node.x;
            node.fy = node.y;
          }}
          linkColor={(link: GraphLink) =>
            link.cascade ? `rgba(226,75,74,${0.6 + Math.sin(tick) * 0.2})` : "rgba(255,255,255,0.1)"
          }
          linkWidth={(link: GraphLink) => link.cascade ? 2.5 : 1}
          linkDirectionalParticles={(link: GraphLink) => link.cascade ? 5 : 0}
          linkDirectionalParticleWidth={3}
          linkDirectionalParticleColor={() => "#ff6b6b"}
          linkDirectionalParticleSpeed={0.007}
          onNodeClick={(node: GraphNode) => onNodeClick?.(node.id)}
          nodeCanvasObject={(node: GraphNode & { x: number; y: number }, ctx: CanvasRenderingContext2D, globalScale: number) => {
            const isCascade = cascadeInvolvedDrugs.includes(node.id);
            const pulse = Math.abs(Math.sin(tick * 1.5));

            if (isCascade) {
              // Outer animated pulse ring
              const ringR = 18 + pulse * 6;
              ctx.beginPath();
              ctx.arc(node.x, node.y, ringR, 0, 2 * Math.PI);
              ctx.fillStyle = `rgba(226,75,74,${0.04 + pulse * 0.06})`;
              ctx.fill();

              // Mid glow
              ctx.beginPath();
              ctx.arc(node.x, node.y, 13, 0, 2 * Math.PI);
              ctx.fillStyle = `rgba(226,75,74,${0.12 + pulse * 0.08})`;
              ctx.fill();
            } else {
              ctx.beginPath();
              ctx.arc(node.x, node.y, 12, 0, 2 * Math.PI);
              ctx.fillStyle = "rgba(29,158,117,0.1)";
              ctx.fill();
            }

            // Main dot
            ctx.beginPath();
            ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);
            ctx.fillStyle = isCascade ? "#E24B4A" : "#1D9E75";
            ctx.fill();

            // Inner highlight
            ctx.beginPath();
            ctx.arc(node.x - 2.5, node.y - 2.5, 3, 0, 2 * Math.PI);
            ctx.fillStyle = isCascade ? "rgba(255,210,210,0.5)" : "rgba(160,255,220,0.45)";
            ctx.fill();

            // Label pill
            const label = node.id;
            const fontSize = Math.max(11 / globalScale, 4);
            ctx.font = `600 ${fontSize}px DM Sans, Sans-Serif`;
            const tw = ctx.measureText(label).width;
            const px = 6, py = 3;
            const rx = node.x - tw / 2 - px;
            const ry = node.y + 12;
            ctx.fillStyle = isCascade ? "rgba(40,10,10,0.75)" : "rgba(0,20,15,0.7)";
            ctx.beginPath();
            ctx.rect(rx, ry, tw + px * 2, fontSize + py * 2);
            ctx.fill();
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            ctx.fillStyle = isCascade ? "#ffb3b3" : "#a7f3d0";
            ctx.fillText(label, node.x, ry + py);
          }}
        />
      </div>

      {/* Legend */}
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "6px 16px 13px", flexWrap: "wrap" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "rgba(255,255,255,0.35)" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#E24B4A", display: "inline-block", boxShadow: "0 0 5px rgba(226,75,74,0.7)" }} />
          Cascade drug
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "rgba(255,255,255,0.35)" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#1D9E75", display: "inline-block" }} />
          Safe drug
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "rgba(255,255,255,0.35)" }}>
          <span style={{ width: 16, height: 2, background: "#E24B4A", display: "inline-block", borderRadius: 1 }} />
          Cascade path
        </span>
        <span style={{ fontSize: 10, color: "rgba(255,255,255,0.18)", marginLeft: "auto" }}>
          drag nodes · scroll to zoom
        </span>
      </div>
    </div>
  );
}
