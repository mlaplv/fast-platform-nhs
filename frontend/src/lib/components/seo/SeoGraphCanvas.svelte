<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import {
		graphData,
		selectedNodeId,
		filterGroup,
		overrideEdge,
		isSidebarOpen,
		deleteEdge,
		deleteNode,
		type GraphNode,
		type GraphLink,
	} from "$lib/stores/seoGraph.svelte";

	/** force-graph không ship @types — khai báo facade tối thiểu */
	interface ForceGraphInstance {
		width(w: number): ForceGraphInstance;
		height(h: number): ForceGraphInstance;
		backgroundColor(c: string): ForceGraphInstance;
		nodeId(k: string): ForceGraphInstance;
		nodeVal(k: string): ForceGraphInstance;
		nodeColor(k: string): ForceGraphInstance;
		onNodeHover(
			cb: (node: SimNode | null, prev: SimNode | null) => void,
		): ForceGraphInstance;
		onEngineTick(cb: () => void): ForceGraphInstance;
		nodeCanvasObject(
			cb: (
				node: SimNode,
				ctx: CanvasRenderingContext2D,
				globalScale: number,
			) => void,
		): ForceGraphInstance;
		nodeCanvasObjectMode(cb: () => string): ForceGraphInstance;
		linkColor(k: string): ForceGraphInstance;
		linkWidth(cb: (link: SimLink) => number): ForceGraphInstance;
		linkLineDash(cb: (link: SimLink) => number[]): ForceGraphInstance;
		linkCurvature(k: string): ForceGraphInstance;
		linkDirectionalArrowLength(v: number): ForceGraphInstance;
		linkDirectionalArrowRelPos(v: number): ForceGraphInstance;
		linkDirectionalParticles(
			cb: (link: SimLink) => number,
		): ForceGraphInstance;
		linkDirectionalParticleSpeed(v: number): ForceGraphInstance;
		onNodeClick(cb: (node: SimNode) => void): ForceGraphInstance;
		onBackgroundClick(cb: () => void): ForceGraphInstance;
		d3AlphaDecay(v: number): ForceGraphInstance;
		warmupTicks(v: number): ForceGraphInstance;
		cooldownTicks(v: number): ForceGraphInstance;
		graphData(data?: {
			nodes: GraphNode[];
			links: GraphLink[];
		}): { nodes: SimNode[]; links: SimLink[] };
		d3Force(
			name: string,
		): { strength(v: number): void; distance(v: number): void } | null;
		centerAt(x: number, y: number, ms: number): void;
		zoom(k: number, ms: number): void;
		graph2ScreenCoords(x: number, y: number): { x: number; y: number };
		_destructor?(): void;
	}

	/** Node sau khi D3 simulation gán x/y */
	interface SimNode extends GraphNode {
		x?: number;
		y?: number;
	}

	/** Link sau khi D3 hydrate source/target thành object */
	interface SimLink extends GraphLink {
		source: string | SimNode;
		target: string | SimNode;
	}

	let { apiBase }: { apiBase: string } = $props();

	let canvasEl: HTMLDivElement;
	let graph: ForceGraphInstance | null = null;

	// Hover Tooltip state
	let hoveredNode = $state<SimNode | null>(null);
	let tooltipX = $state(0);
	let tooltipY = $state(0);
	let isHoveringTooltip = $state(false);
	let hoverTimeout: ReturnType<typeof setTimeout> | null = null;

	function updateTooltipPosition() {
		if (graph && hoveredNode) {
			const coords = graph.graph2ScreenCoords(
				hoveredNode.x,
				hoveredNode.y,
			);
			if (coords) {
				tooltipX = coords.x;
				tooltipY = coords.y - 12;
			}
		}
	}

	function handleNodeHover(node: SimNode | null) {
		if (hoverTimeout) clearTimeout(hoverTimeout);

		if (node) {
			hoveredNode = node;
			updateTooltipPosition();
		} else {
			hoverTimeout = setTimeout(() => {
				if (!isHoveringTooltip) {
					hoveredNode = null;
				}
			}, 300);
		}
	}

	async function handleUnlinkHoveredNode(e: MouseEvent) {
		e.stopPropagation();
		if (!hoveredNode) return;
		const activeId = hoveredNode.id;
		const link = graphData.links.find((l) => {
			const srcId =
				typeof l.source === "object"
					? (l.source as SimNode).id
					: l.source;
			const tgtId =
				typeof l.target === "object"
					? (l.target as SimNode).id
					: l.target;
			return srcId === activeId || tgtId === activeId;
		});
		if (link) {
			const success = await deleteEdge(apiBase, link.id);
			if (success) {
				hoveredNode = null;
				selectedNodeId.value = null;
			}
		}
	}

	async function handleDeleteHoveredNode(e: MouseEvent) {
		e.stopPropagation();
		if (!hoveredNode) return;
		if (
			confirm(
				`Bạn có chắc muốn xóa node "${hoveredNode.label}" khỏi đồ thị SEO không? (Điều này không ảnh hưởng đến nội dung bài viết gốc trên trang web)`,
			)
		) {
			const success = await deleteNode(apiBase, hoveredNode.id);
			if (success) {
				hoveredNode = null;
				selectedNodeId.value = null;
			}
		}
	}

	// Reactive derived state for filtering nodes and links to keep simulation robust
	const filteredNodes = $derived.by(() => {
		if (filterGroup.value === "all") {
			return graphData.nodes;
		}
		if (filterGroup.value === "ai_suggested") {
			const aiSuggestedLinkNodeIds = new Set<string>();
			for (const l of graphData.links) {
				if (!l.is_confirmed) {
					const sourceId =
						typeof l.source === "object"
							? (l.source as SimNode).id
							: l.source;
					const targetId =
						typeof l.target === "object"
							? (l.target as SimNode).id
							: l.target;
					aiSuggestedLinkNodeIds.add(sourceId);
					aiSuggestedLinkNodeIds.add(targetId);
				}
			}
			return graphData.nodes.filter((n) =>
				aiSuggestedLinkNodeIds.has(n.id),
			);
		}
		return graphData.nodes.filter((n) => n.group === filterGroup.value);
	});

	const filteredLinks = $derived.by(() => {
		if (filterGroup.value === "all") {
			return graphData.links;
		}
		if (filterGroup.value === "ai_suggested") {
			return graphData.links.filter((l) => !l.is_confirmed);
		}
		return graphData.links.filter((l) => {
			const sourceId =
				typeof l.source === "object"
					? (l.source as SimNode).id
					: l.source;
			const targetId =
				typeof l.target === "object"
					? (l.target as SimNode).id
					: l.target;
			return (
				filteredNodes.some((n) => n.id === sourceId) &&
				filteredNodes.some((n) => n.id === targetId)
			);
		});
	});

	// Reactive: rebuild graph khi graphData hoặc bộ lọc thay đổi
	$effect(() => {
		const nodes = filteredNodes;
		const links = filteredLinks;
		if (graph && nodes.length > 0) {
			graph.graphData({ nodes: [...nodes], links: [...links] });
		} else if (graph) {
			graph.graphData({ nodes: [], links: [] });
		}
	});

	// Reactive: Zoom & center on selected node
	$effect(() => {
		const nodeId = selectedNodeId.value;
		if (graph && nodeId) {
			let attempts = 0;
			const checkAndCenter = () => {
				if (!graph || selectedNodeId.value !== nodeId) return;
				const simulatedNodes = graph.graphData().nodes;
				const node = simulatedNodes.find(
					(n: SimNode) => n.id === nodeId,
				);
				if (node) {
					if (
						node.x !== undefined &&
						node.y !== undefined &&
						!isNaN(node.x) &&
						!isNaN(node.y)
					) {
						graph.centerAt(node.x, node.y, 800);
						graph.zoom(2.5, 800);
					} else if (attempts < 30) {
						attempts++;
						setTimeout(checkAndCenter, 50);
					}
				}
			};
			setTimeout(checkAndCenter, 50);
		}
	});

	onMount(async () => {
		// Dynamic import — force-graph cần browser environment
		const ForceGraph = (await import("force-graph")).default;

		if (!canvasEl) return;

		graph = ForceGraph()(canvasEl)
			.width(canvasEl.offsetWidth)
			.height(canvasEl.offsetHeight)
			.backgroundColor("#0f0f17")
			// Node rendering
			.nodeId("id")
			.nodeVal("val")
			.nodeColor("color")
			.onNodeHover(handleNodeHover)
			.onEngineTick(updateTooltipPosition)
			.nodeCanvasObject(
				(
					node: SimNode,
					ctx: CanvasRenderingContext2D,
					globalScale: number,
				) => {
					if (
						node.x === undefined ||
						node.y === undefined ||
						isNaN(node.x) ||
						isNaN(node.y)
					)
						return;
					const radius = node.val ?? 6;
					// Glow effect cho pillar nodes
					if (node.is_pillar) {
						ctx.beginPath();
						ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI);
						const grd = ctx.createRadialGradient(
							node.x,
							node.y,
							0,
							node.x,
							node.y,
							radius + 4,
						);
						grd.addColorStop(0, "rgba(99,102,241,0.4)");
						grd.addColorStop(1, "rgba(99,102,241,0)");
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
						ctx.strokeStyle = "#ffffff";
						ctx.lineWidth = 2;
						ctx.stroke();
					}
					// Label nếu zoom đủ gần
					if (globalScale >= 1.5 || node.is_pillar) {
						const label =
							node.label.length > 20
								? node.label.slice(0, 20) + "…"
								: node.label;
						ctx.font = `${node.is_pillar ? "bold " : ""}${Math.max(10, 12 / globalScale)}px Inter,sans-serif`;
						ctx.fillStyle = node.is_pillar ? "#a5b4fc" : "#94a3b8";
						ctx.textAlign = "center";
						ctx.fillText(label, node.x, node.y + radius + 10);
					}
				},
			)
			.nodeCanvasObjectMode(() => "replace")
			// Edge rendering
			.linkColor("color")
			.linkWidth((link: SimLink) => (link.is_confirmed ? 1.5 : 0.8))
			.linkLineDash((link: SimLink) => (link.is_confirmed ? [] : [4, 3])) // Dashed = AI suggested
			.linkCurvature("curvature")
			.linkDirectionalArrowLength(4)
			.linkDirectionalArrowRelPos(1)
			.linkDirectionalParticles((link: SimLink) =>
				link.is_confirmed ? 0 : 2,
			)
			.linkDirectionalParticleSpeed(0.004)
			// Interactions
			.onNodeClick((node: SimNode) => {
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
			.d3AlphaDecay(0.02)
			.warmupTicks(100)
			.cooldownTicks(200);

		// Tối ưu hóa lực đẩy d3 để các node phân bổ đều, giãn cách đẹp mắt, không dính chùm
		const chargeForce = graph.d3Force("charge");
		if (chargeForce) {
			chargeForce.strength(-180);
		}
		const linkForce = graph.d3Force("link");
		if (linkForce) {
			linkForce.distance(90);
		}

		// Initial data
		graph.graphData({
			nodes: [...filteredNodes],
			links: [...filteredLinks],
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

<div class="canvas-container">
	<div class="graph-canvas" bind:this={canvasEl}></div>

	<!-- Custom HTML Tooltip -->
	{#if hoveredNode}
		<div
			class="custom-tooltip"
			style="left: {tooltipX}px; top: {tooltipY}px;"
			onmouseenter={() => {
				isHoveringTooltip = true;
				if (hoverTimeout) clearTimeout(hoverTimeout);
			}}
			onmouseleave={() => {
				isHoveringTooltip = false;
				hoverTimeout = setTimeout(() => {
					hoveredNode = null;
				}, 200);
			}}
			role="tooltip"
		>
			<div class="tooltip-header">
				<span class="tooltip-title"
					>{hoveredNode.is_pillar
						? "⭐ "
						: ""}{hoveredNode.label}</span
				>
			</div>
			<div class="tooltip-meta">
				<span class="meta-tag">{hoveredNode.entity_type}</span>
				<span class="meta-group {hoveredNode.group}"
					>{hoveredNode.group}</span
				>
			</div>
			{#if hoveredNode.ai_confidence}
				<div class="tooltip-conf">
					🤖 Độ tin cậy AI: <strong
						>{Math.round(hoveredNode.ai_confidence * 100)}%</strong
					>
				</div>
			{/if}

			<!-- Interactive Actions inside Tooltip -->
			<div class="tooltip-actions">
				{#if hoveredNode.group === "cluster"}
					<button
						class="tooltip-btn unlink"
						onclick={handleUnlinkHoveredNode}
						title="Gỡ khỏi Pillar"
					>
						✕ Gỡ Cluster
					</button>
				{/if}
				<button
					class="tooltip-btn delete"
					onclick={handleDeleteHoveredNode}
					title="Xóa khỏi đồ thị"
				>
					🗑 Xóa Node
				</button>
			</div>
		</div>
	{/if}
</div>

<!-- Legend -->
<div class="graph-legend">
	<div class="legend-item">
		<span class="dot" style="background:#6366f1;box-shadow:0 0 6px #6366f1"
		></span>
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
	.graph-canvas:active {
		cursor: grabbing;
	}

	.canvas-container {
		position: relative;
		width: 100%;
		height: 100%;
	}

	/* Interactive glassmorphic tooltip */
	.custom-tooltip {
		position: absolute;
		z-index: 1000;
		transform: translate(-50%, -100%);
		background: rgba(15, 15, 27, 0.95);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid rgba(99, 102, 241, 0.3);
		border-radius: 10px;
		padding: 0.75rem 0.9rem;
		width: 240px;
		box-shadow:
			0 10px 30px rgba(0, 0, 0, 0.6),
			inset 0 1px 0 rgba(255, 255, 255, 0.05);
		font-family: "Inter", sans-serif;
		pointer-events: auto;
		transition: opacity 0.15s ease;
	}

	.tooltip-header {
		margin-bottom: 0.35rem;
	}

	.tooltip-title {
		font-weight: 700;
		font-size: 0.8rem;
		color: #f1f5f9;
		line-height: 1.4;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.tooltip-meta {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.68rem;
		margin-top: 0.35rem;
	}

	.meta-tag {
		padding: 1px 4px;
		background: rgba(255, 255, 255, 0.08);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		text-transform: uppercase;
		font-size: 0.6rem;
		font-weight: 600;
		color: #cbd5e1;
	}

	.meta-group {
		font-weight: 500;
	}
	.meta-group.pillar {
		color: #818cf8;
	}
	.meta-group.cluster {
		color: #c7d2fe;
	}
	.meta-group.unclassified {
		color: #fbbf24;
	}

	.tooltip-conf {
		font-size: 0.68rem;
		color: #fb923c;
		margin-top: 0.5rem;
	}

	.tooltip-actions {
		display: flex;
		gap: 0.4rem;
		margin-top: 0.75rem;
		border-top: 1px solid rgba(255, 255, 255, 0.06);
		padding-top: 0.6rem;
	}

	.tooltip-btn {
		flex: 1;
		padding: 0.35rem 0.5rem;
		font-size: 0.68rem;
		font-weight: 600;
		border-radius: 6px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.25rem;
		transition: all 0.2s ease;
		border: 1px solid transparent;
	}

	.tooltip-btn.unlink {
		background: rgba(249, 115, 22, 0.1);
		border-color: rgba(249, 115, 22, 0.25);
		color: #ffedd5;
	}
	.tooltip-btn.unlink:hover {
		background: rgba(249, 115, 22, 0.2);
		border-color: rgba(249, 115, 22, 0.4);
	}

	.tooltip-btn.delete {
		background: rgba(239, 68, 68, 0.1);
		border-color: rgba(239, 68, 68, 0.25);
		color: #fee2e2;
	}
	.tooltip-btn.delete:hover {
		background: rgba(239, 68, 68, 0.2);
		border-color: rgba(239, 68, 68, 0.5);
	}

	.graph-legend {
		position: absolute;
		bottom: 1rem;
		left: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		background: rgba(15, 15, 23, 0.85);
		backdrop-filter: blur(8px);
		border: 1px solid rgba(99, 102, 241, 0.2);
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
	.line.dashed {
		border-top-style: dashed;
	}
</style>
