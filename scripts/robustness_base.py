import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Color palette (Modern Soft UI) - matching CU01-CU05
COLORS = {
    'bg': '#F8FAFC',
    'actor_fill': '#EDE9FE',
    'actor_edge': '#7C3AED',
    'boundary_fill': '#E0F2FE',
    'boundary_edge': '#0284C7',
    'controller_fill': '#DCFCE7',
    'controller_edge': '#16A34A',
    'entity_fill': '#FEF3C7',
    'entity_edge': '#D97706',
    'text': '#0F172A',
    'subtext': '#475569',
    'line': '#64748B',
    'arrow_crud': '#B45309',
    'arrow_call': '#0369A1',
    'label_bg': '#FFFFFF',
    'label_edge': '#CBD5E1',
}

def setup_canvas(title, subtitle, width=15, height=9):
    fig, ax = plt.subplots(figsize=(width, height), dpi=300)
    fig.patch.set_facecolor(COLORS['bg'])
    ax.set_facecolor(COLORS['bg'])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Header
    ax.text(0.5, 0.965, title, fontsize=15.5, fontweight='bold', ha='center', va='top', color=COLORS['text'])
    ax.text(0.5, 0.93, subtitle, fontsize=9.5, ha='center', va='top', color=COLORS['subtext'])
    
    # Legend
    legend_items = [
        ('Actor (Rol)', COLORS['actor_fill'], COLORS['actor_edge']),
        ('Boundary (Vista / UI)', COLORS['boundary_fill'], COLORS['boundary_edge']),
        ('Controller (Servicio / Lógica)', COLORS['controller_fill'], COLORS['controller_edge']),
        ('Entity (Tabla / Modelo BD)', COLORS['entity_fill'], COLORS['entity_edge']),
    ]
    x_leg = 0.12
    for label, fill, edge in legend_items:
        patch = patches.FancyBboxPatch(
            (x_leg, 0.025), 0.16, 0.035,
            boxstyle="round,pad=0.01,rounding_size=0.015",
            facecolor=fill, edgecolor=edge, linewidth=1.5
        )
        ax.add_patch(patch)
        ax.text(x_leg + 0.08, 0.0425, label, fontsize=8.5, ha='center', va='center', fontweight='bold', color=COLORS['text'])
        x_leg += 0.20
        
    return fig, ax

def draw_actor(ax, x, y, name, sub=""):
    w, h = 0.13, 0.08
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=COLORS['actor_fill'], edgecolor=COLORS['actor_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.018, "[ACTOR]", fontsize=8.5, fontweight='bold', ha='center', va='center', color=COLORS['actor_edge'], zorder=4)
    ax.text(x, y - 0.005, name, fontsize=9.5, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.025, sub, fontsize=7.8, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_boundary(ax, x, y, name, sub=""):
    w, h = 0.16, 0.085
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=COLORS['boundary_fill'], edgecolor=COLORS['boundary_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.022, "«boundary»", fontsize=8.5, fontweight='bold', ha='center', va='center', color=COLORS['boundary_edge'], zorder=4)
    ax.text(x, y + 0.002, name, fontsize=9.0, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.022, sub, fontsize=7.6, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_controller(ax, x, y, name, sub=""):
    w, h = 0.16, 0.085
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor=COLORS['controller_fill'], edgecolor=COLORS['controller_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.022, "«control»", fontsize=8.5, fontweight='bold', ha='center', va='center', color=COLORS['controller_edge'], zorder=4)
    ax.text(x, y + 0.002, name, fontsize=9.0, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.022, sub, fontsize=7.6, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_entity(ax, x, y, name, sub=""):
    w, h = 0.14, 0.075
    rect = patches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.015",
        facecolor=COLORS['entity_fill'], edgecolor=COLORS['entity_edge'], linewidth=2, zorder=3
    )
    ax.add_patch(rect)
    ax.text(x, y + 0.018, "«entity»", fontsize=8.2, fontweight='bold', ha='center', va='center', color=COLORS['entity_edge'], zorder=4)
    ax.text(x, y - 0.002, name, fontsize=9.0, fontweight='bold', ha='center', va='center', color=COLORS['text'], zorder=4)
    if sub:
        ax.text(x, y - 0.022, sub, fontsize=7.4, ha='center', va='center', color=COLORS['subtext'], zorder=4)

def draw_actor_link(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color='#64748B', linewidth=2.0, linestyle='-', zorder=2)

def draw_call_arrow(ax, x1, y1, x2, y2, label, offset_y=0.025, rad=0.0):
    connectionstyle = f"arc3,rad={rad}" if rad != 0 else "arc3,rad=0"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.32,head_length=0.42",
            color=COLORS['arrow_call'],
            lw=1.7,
            connectionstyle=connectionstyle
        ),
        zorder=2
    )
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + offset_y
    ax.text(
        mx, my, label, fontsize=7.8, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.22", fc=COLORS['label_bg'], ec=COLORS['boundary_edge'], lw=1, alpha=0.95),
        color=COLORS['arrow_call'], fontweight='bold', zorder=5
    )

def draw_crud_arrow(ax, x1, y1, x2, y2, crud_verb, detail="", rad=0.0, offset_y=0.02, offset_x=0.0):
    connectionstyle = f"arc3,rad={rad}" if rad != 0 else "arc3,rad=0"
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->,head_width=0.32,head_length=0.42",
            color=COLORS['arrow_crud'],
            lw=1.7,
            connectionstyle=connectionstyle
        ),
        zorder=2
    )
    mx = (x1 + x2) / 2 + offset_x
    my = (y1 + y2) / 2 + offset_y
    label = f"{crud_verb}: {detail}" if detail else crud_verb
    ax.text(
        mx, my, label, fontsize=7.5, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.20", fc=COLORS['label_bg'], ec=COLORS['entity_edge'], lw=1, alpha=0.95),
        color=COLORS['arrow_crud'], fontweight='bold', zorder=5
    )

def save_and_close(fig, output_dir, name):
    png_path = os.path.join(output_dir, f"{name}.png")
    svg_path = os.path.join(output_dir, f"{name}.svg")
    fig.savefig(png_path, bbox_inches='tight')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {name}.png and .svg")

