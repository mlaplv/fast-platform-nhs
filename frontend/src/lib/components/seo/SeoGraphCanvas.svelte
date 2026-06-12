<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { graphData, selectedNodeId, filterGroup, overrideEdge, isSidebarOpen } from '$lib/stores/seoGraph.svelte';

	let { apiBase }: { apiBase: string } = $props();

	let canvasEl: HTMLDivElement;
	let graph: any = null;

	// Reactive: rebuild graph khi graphData thay đổi
	$effect(() => {
		const nodes = graphData.nodes;
		const links = graphData.links;
		if (graph && nodes.length > 0) {
			graph.graphData({ nodes: [...nodes], links: [...links] });
		}
	});

	// Reactive: Zoom & center on selected node
	$effect(() => {
		const nodeId = selectedNodeId.value;
		if (graph && nodeId) {
			const simulatedNodes = graph.graphData().nodes;
			const node = simulatedNodes.find((n: any) => n.id === nodeId);
			if (node) {
				setTimeout(() => {
					if (node.x !== undefined && node.y !== undefined) {
						graph.centerAt(node.x, node.y, 800);
						graph.zoom(2.5, 800);
					}
				}, 50);
			}
		}
	});

	onMount(async () => {
		// Dynamic import — force-graph cần browser environment
		const ForceGraph = (await import('force-graph')).default;

		if (!canvasEl) return;

		graph = ForceGraph()(canvasEl)
			.width(canvasEl.offsetWidth)
			.height(canvasEl.offsetHeight)
			.backgroundColor('#0f0f17')
			// Node rendering
			.nodeId('id')
			.nodeVal('val')
			.nodeColor('color')
			.nodeLabel((node: any) => `
				<div style="background:#1e1e3a;border:1px solid rgba(99,102,241,0.4);border-radius:8px;padding:8px 12px;max-width:240px;font-family:Inter,sans-serif">
					<div style="font-weight:700;font-size:13px;color:${node.is_pillar ? '#a5b4fc' : '#e2e8f0'};margin-bottom:4px">
						${node.is_pillar ? '⭐ ' : ''}${node.label}
					</div>
					<div style="font-size:11px;color:#64748b">${node.entity_type} • ${node.group}</div>
					${node.ai_confidence ? `<div style="font-size:11px;color:#f97316;margin-top:2px">AI: ${Math.round(node.ai_confidence * 100)}%</div>` : ''}
				</div>
			`)
			.nodeCanvasObject((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
				if (node.x === undefined || node.y === undefined || isNaN(node.x) || isNaN(node.y)) return;
				const radius = node.val ?? 6;
				// Glow effect cho pillar nodes
				if (node.is_pillar) {
					ctx.beginPath();
					ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI);
					const grd = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, radius + 4);
					grd.addColorStop(0, 'rgba(99,102,241,0.4)');
					grd.addColorStop(1, 'rgba(99,102,241,0)');
					ctx.fillStyle = grd;
					ctx.fill();
				}
				// Node circle
				ctx.beginPath();
				ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
				ctx.fillStyle = node.color;
				ctx.fill();
				// Highlight selected
				if (node.id === selectedNodeId.value) {
					ctx.beginPath();
					ctx.arc(node.x, node.y, radius + 2, 0, 2 * Math.PI);
					ctx.strokeStyle = '#ffffff';
					ctx.lineWidth = 2;
					ctx.stroke();
				}
				// Label nếu zoom đủ gần
				if (globalScale >= 1.5 || node.is_pillar) {
					const label = node.label.length > 20 ? node.label.slice(0, 20) + '…' : node.label;
					ctx.font = `${node.is_pillar ? 'bold ' : ''}${Math.max(10, 12 / globalScale)}px Inter,sans-serif`;
					ctx.fillStyle = node.is_pillar ? '#a5b4fc' : '#94a3b8';
					ctx.textAlign = 'center';
					ctx.fillText(label, node.x, node.y + radius + 10);
				}
			})
			.nodeCanvasObjectMode(() => 'replace')
			// Edge rendering
			.linkColor('color')
			.linkWidth((link: any) => link.is_confirmed ? 1.5 : 0.8)
			.linkLineDash((link: any) => link.is_confirmed ? [] : [4, 3])  // Dashed = AI suggested
			.linkCurvature('curvature')
			.linkDirectionalArrowLength(4)
			.linkDirectionalArrowRelPos(1)
			.linkDirectionalParticles((link: any) => link.is_confirmed ? 0 : 2)
			.linkDirectionalParticleSpeed(0.004)
			// Interactions
			.onNodeClick((node: any) => {
				if (node.id === selectedNodeId.value) {
					selectedNodeId.value = null;
				} else {
					selectedNodeId.value = node.id;
					isSidebarOpen.value = true;
				}
			})
			.onBackgroundClick(() => {
				selectedNodeId.value = null;
			})
			.d3Force('charge', null)
			.d3AlphaDecay(0.02)
			.warmupTicks(100)
			.cooldownTicks(200);

		// Initial data
		graph.graphData({
			nodes: [...graphData.nodes],
			links: [...graphData.links]
		});

		// Handle resize
		const ro = new ResizeObserver(() => {
			if (graph && canvasEl) {
				graph.width(canvasEl.offsetWidth).height(canvasEl.offsetHeight);
			}
		});
		ro.observe(canvasEl);

		return () => ro.disconnect();
	});

	onDestroy(() => {
		if (graph) {
			graph._destructor?.();
			graph = null;
		}
	});
</script>

<div class="graph-canvas" bind:this={canvasEl}></div>

<!-- Legend -->
<div class="graph-legend">
	<div class="legend-item">
		<span class="dot" style="background:#6366f1;box-shadow:0 0 6px #6366f1"></span>
		Pillar Page
	</div>
	<div class="legend-item">
		<span class="dot" style="background:#a5b4fc"></span>
		Cluster (xác nhận)
	</div>
	<div class="legend-item">
		<span class="dot" style="background:#f59e0b"></span>
		Chưa phân loại
	</div>
	<div class="legend-item">
		<span class="line dashed" style="border-color:#f97316"></span>
		AI đề xuất
	</div>
	<div class="legend-item">
		<span class="line" style="border-color:#6366f1"></span>
		Đã xác nhận
	</div>
</div>

<style>
	.graph-canvas {
		width: 100%;
		height: 100%;
		cursor: grab;
	}
	.graph-canvas:active { cursor: grabbing; }

	.graph-legend {
		position: absolute;
		bottom: 1rem;
		left: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		background: rgba(15,15,23,0.85);
		backdrop-filter: blur(8px);
		border: 1px solid rgba(99,102,241,0.2);
		border-radius: 10px;
		padding: 0.75rem 1rem;
		pointer-events: none;
	}
	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.72rem;
		color: #94a3b8;
	}
	.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.line {
		width: 20px;
		height: 0;
		border-top: 2px solid;
		flex-shrink: 0;
	}
	.line.dashed { border-top-style: dashed; }
</style>
