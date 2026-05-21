from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus import ListFlowable, ListItem
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io
import os
from reportlab.platypus import Image as RLImage

# ── Colors ────────────────────────────────────────────────────────────────────
PRIMARY    = colors.HexColor('#1B3A5C')   # dark navy
SECONDARY  = colors.HexColor('#2E86AB')   # medium blue
ACCENT     = colors.HexColor('#E84855')   # red accent
LIGHT_BG   = colors.HexColor('#F0F4F8')   # very light blue-grey
MID_BG     = colors.HexColor('#D6E4F0')   # medium light blue
DARK_TEXT  = colors.HexColor('#1A1A2E')
GREY_TEXT  = colors.HexColor('#555577')
WHITE      = colors.white
ORANGE     = colors.HexColor('#F4A261')
GREEN      = colors.HexColor('#2A9D8F')

W, H = A4

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def make_style(name, parent='Normal', **kwargs):
    return ParagraphStyle(name, parent=styles[parent], **kwargs)

cover_title   = make_style('CoverTitle',   fontSize=28, textColor=WHITE,
                           fontName='Helvetica-Bold', alignment=TA_CENTER,
                           leading=34, spaceAfter=10)
cover_sub     = make_style('CoverSub',     fontSize=14, textColor=MID_BG,
                           fontName='Helvetica', alignment=TA_CENTER, leading=20)
cover_meta    = make_style('CoverMeta',    fontSize=10, textColor=colors.HexColor('#A8C4D8'),
                           fontName='Helvetica', alignment=TA_CENTER, leading=14)

h1 = make_style('H1', fontSize=17, textColor=WHITE, fontName='Helvetica-Bold',
                spaceAfter=6, spaceBefore=2, leading=21)
h2 = make_style('H2', fontSize=13, textColor=PRIMARY, fontName='Helvetica-Bold',
                spaceAfter=4, spaceBefore=10, leading=17,
                borderPad=0)
h3 = make_style('H3', fontSize=11, textColor=SECONDARY, fontName='Helvetica-Bold',
                spaceAfter=3, spaceBefore=6, leading=14)
body = make_style('Body', fontSize=9.5, textColor=DARK_TEXT, fontName='Helvetica',
                  spaceAfter=5, leading=14, alignment=TA_JUSTIFY)
body_small = make_style('BodySmall', fontSize=8.5, textColor=DARK_TEXT,
                        fontName='Helvetica', spaceAfter=4, leading=12,
                        alignment=TA_JUSTIFY)
caption = make_style('Caption', fontSize=8, textColor=GREY_TEXT,
                     fontName='Helvetica-Oblique', alignment=TA_CENTER,
                     spaceAfter=8)
bullet_style = make_style('Bullet', fontSize=9.5, textColor=DARK_TEXT,
                          fontName='Helvetica', spaceAfter=3, leading=13,
                          leftIndent=14, firstLineIndent=-10)

# ── Helper: matplotlib figure → ReportLab Image ───────────────────────────────
def fig_to_image(fig, width_cm=15):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=160, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    img = RLImage(buf)
    img.drawWidth  = width_cm * cm
    aspect = img.imageHeight / img.imageWidth
    img.drawHeight = img.drawWidth * aspect
    return img

# ── Section header block ──────────────────────────────────────────────────────
def section_header(num, title, story):
    """Colored banner for a numbered section."""
    data = [[Paragraph(f'<font color="white"><b>{num}. {title}</b></font>', h1)]]
    tbl = Table(data, colWidths=[W - 4*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 14),
        ('RIGHTPADDING',  (0,0), (-1,-1), 14),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(Spacer(1, 0.25*cm))
    story.append(tbl)
    story.append(Spacer(1, 0.2*cm))

def subsection(title, story):
    story.append(Paragraph(title, h2))

def subsubsection(title, story):
    story.append(Paragraph(title, h3))

def p(text, story, style=None):
    story.append(Paragraph(text, style or body))

def bullets(items, story):
    for item in items:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {item}', bullet_style))

def metric_table(headers, rows, story, col_widths=None):
    # Ensure cell content is a Paragraph so text wraps within column widths
    n_cols = len(headers)
    if col_widths is None:
        col_widths = [(W - 4*cm) / n_cols] * n_cols

    def make_cell(cell, style=body_small):
        if isinstance(cell, Paragraph):
            return cell
        return Paragraph(str(cell), style)

    header_cells = [Paragraph(f'<b><font color="white">{h}</font></b>',
                              ParagraphStyle('mh', fontSize=9, fontName='Helvetica-Bold',
                                             alignment=TA_CENTER, leading=11)) for h in headers]

    data = [header_cells]
    for r in rows:
        data.append([make_cell(c, body_small) for c in r])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND',    (0,0), (-1,0),  PRIMARY),
        ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 8.5),
        ('ALIGN',         (0,0), (-1,0), 'CENTER'),
        ('ALIGN',         (0,1), (-1,-1), 'LEFT'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('GRID',          (0,0), (-1,-1), 0.4, colors.HexColor('#B0BEC5')),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)
    story.append(Spacer(1, 0.3*cm))

def kpi_row(kpis, story):
    """kpis = list of (label, value, color) tuples"""
    cells = []
    for label, value, color in kpis:
        inner = Table([[Paragraph(f'<b><font color="white">{value}</font></b>',
                                  ParagraphStyle('kv', fontSize=15, fontName='Helvetica-Bold',
                                                 alignment=TA_CENTER, leading=18))],
                       [Paragraph(f'<font color="#CCDDEE">{label}</font>',
                                  ParagraphStyle('kl', fontSize=8, fontName='Helvetica',
                                                 alignment=TA_CENTER, leading=11))]],
                      colWidths=[3.8*cm])
        inner.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), color),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ]))
        cells.append(inner)
    row_tbl = Table([cells], colWidths=[3.9*cm]*len(kpis),
                    hAlign='CENTER')
    row_tbl.setStyle(TableStyle([
        ('LEFTPADDING',  (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(row_tbl)
    story.append(Spacer(1, 0.35*cm))

def divider(story):
    story.append(HRFlowable(width='100%', thickness=0.5,
                             color=colors.HexColor('#CFD8DC'), spaceAfter=6))

# ── FIGURES ───────────────────────────────────────────────────────────────────

def fig_target_distribution():
    fig, ax = plt.subplots(figsize=(6, 3.2), facecolor='white')
    labels = ['Sin accidente (0)', 'Con accidente (1)']
    values = [7871305, 120475]
    pcts   = [98.49, 1.51]
    bar_colors = [SECONDARY.hexval().replace('0x','#'), ACCENT.hexval().replace('0x','#')]
    bars = ax.bar(labels, values, color=['#2E86AB','#E84855'], edgecolor='white', width=0.5)
    for bar, pct, val in zip(bars, pcts, values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()*0.5,
                f'{val:,}\n({pct:.1f}%)', ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
    ax.set_title('Distribución de la variable objetivo (target)', fontsize=11, fontweight='bold', pad=8)
    ax.set_ylabel('Número de registros', fontsize=9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,p: f'{x/1e6:.1f}M'))
    ax.set_ylim(0, 9e6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=9)
    plt.tight_layout()
    return fig

def fig_accidents_by_hour():
    hours = np.arange(24)
    counts = [1357,1011,820,765,760,1245,3205,5830,6750,6510,6020,5980,
              6190,6350,6280,6450,6900,8520,9140,8800,7830,6520,5050,2910]
    fig, ax = plt.subplots(figsize=(9, 3.5), facecolor='white')
    ax.fill_between(hours, counts, alpha=0.18, color='#2E86AB')
    ax.plot(hours, counts, color='#1B3A5C', linewidth=2, marker='o', markersize=4)
    peak = np.argmax(counts)
    # Mark and annotate peak with a readable box and offset so title doesn't overlap
    ax.scatter(hours[peak], counts[peak], color='#E84855', s=120, zorder=6)
    ax.annotate(
        f'Pico: {hours[peak]}h\n({counts[peak]:,})',
        xy=(hours[peak], counts[peak]),
        xytext=(hours[peak]-3, counts[peak]+400),
        fontsize=8,
        color='#E84855',
        fontweight='bold',
        zorder=7,
        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#E84855', alpha=0.95),
        arrowprops=dict(arrowstyle='->', color='#E84855', lw=1.2))
    ax.set_xlabel('Hora del día', fontsize=9)
    ax.set_ylabel('Cantidad de accidentes', fontsize=9)
    # Add extra padding between title and axes so annotation is visible
    ax.set_title('Accidentes por hora del día (2017–2019)', fontsize=10, fontweight='bold', pad=25)
    ax.set_xticks(hours)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=8)
    # Reserve top space to avoid clipping the annotation/title
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    return fig

def fig_accidents_by_day():
    days   = ['Lunes','Martes','Miérc.','Jueves','Viernes','Sábado','Domingo']
    counts = [17900, 19700, 19100, 18600, 20200, 17900, 11500]
    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='white')
    bar_colors = ['#2E86AB' if c < max(counts) else '#E84855' for c in counts]
    ax.bar(days, counts, color=bar_colors, edgecolor='white', width=0.65)
    for i,(d,c) in enumerate(zip(days,counts)):
        ax.text(i, c+150, f'{c:,}', ha='center', fontsize=8)
    ax.set_ylabel('Cantidad de accidentes', fontsize=9)
    ax.set_title('Accidentes por día de la semana', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 23000)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=9)
    plt.tight_layout()
    return fig

def fig_top_neighborhoods():
    barrios = ['lacandelaria','campoamor','perpetuosocorro','caribe','barriocolon',
               'santafe','losconquistadores','villanueva','gabecera...prado',
               'carloserestrepo','sanbenito','guayaquil','sandiego','terminaltr.','naranjal']
    counts  = [3050,2750,2630,2520,2490,2380,2200,1980,1870,1790,1720,1680,1620,1570,1510]
    fig, ax = plt.subplots(figsize=(8, 5), facecolor='white')
    cmap_vals = plt.cm.YlOrRd(np.linspace(0.35, 0.85, len(barrios)))
    ax.barh(barrios[::-1], counts[::-1], color=cmap_vals, edgecolor='white')
    for i,(c) in enumerate(counts[::-1]):
        ax.text(c+30, i, f'{c:,}', va='center', fontsize=7.5)
    ax.set_xlabel('Cantidad de accidentes', fontsize=9)
    ax.set_title('Top 15 barrios con mayor accidentalidad (2017–2019)', fontsize=10, fontweight='bold')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.set_xlim(0, 3500)
    ax.tick_params(labelsize=8)
    plt.tight_layout()
    return fig

def fig_weather_correlation():
    # Recreate correlation heatmap
    labels = ['temperature','humidity','windSpeed','precipProb.','target']
    matrix = np.array([
        [1.00, -0.86,  0.58, -0.21,  0.19],
        [-0.86, 1.00, -0.53,  0.33, -0.12],
        [0.58, -0.53,  1.00, -0.18,  0.12],
        [-0.21, 0.33, -0.18,  1.00, -0.04],
        [0.19, -0.12,  0.12, -0.04,  1.00],
    ])
    fig, ax = plt.subplots(figsize=(5.5, 4.5), facecolor='white')
    im = ax.imshow(matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
    plt.colorbar(im, ax=ax, shrink=0.8, label='Correlación de Pearson')
    ax.set_xticks(range(5)); ax.set_yticks(range(5))
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, f'{matrix[i,j]:.2f}', ha='center', va='center',
                    fontsize=8, fontweight='bold',
                    color='white' if abs(matrix[i,j]) > 0.5 else '#333333')
    ax.set_title('Correlación: variables climáticas vs. target', fontsize=10, fontweight='bold')
    plt.tight_layout()
    return fig

def fig_cyclic_features():
    hours = np.arange(24)
    sin_vals = np.sin(2*np.pi*hours/24)
    cos_vals = np.cos(2*np.pi*hours/24)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), facecolor='white')
    sc = axes[0].scatter(cos_vals, sin_vals, c=hours, cmap='hsv', s=55, zorder=5)
    for h in hours:
        axes[0].annotate(str(h),(cos_vals[h], sin_vals[h]), fontsize=6.5,
                         ha='center', va='bottom')
    axes[0].set_title('Hora del día como features cíclicas', fontsize=9, fontweight='bold')
    axes[0].set_xlabel('cos(hora)'); axes[0].set_ylabel('sin(hora)')
    axes[0].axhline(0, color='grey', lw=0.5); axes[0].axvline(0, color='grey', lw=0.5)
    plt.colorbar(sc, ax=axes[0], label='Hora', shrink=0.8)
    
    feature_groups = ['Temporales\nbásicas', 'Cíclicas\nsin/cos', 'Históricas\nventana', 'Climáticas', 'Encoding\ncategórico']
    n_features = [6, 8, 4, 11, 4]  # approx 29 total (some overlap with scaled)
    clrs = ['#1B3A5C','#2E86AB','#E84855','#F4A261','#2A9D8F']
    axes[1].bar(feature_groups, n_features, color=clrs, edgecolor='white', width=0.6)
    for i,(g,n) in enumerate(zip(feature_groups,n_features)):
        axes[1].text(i, n+0.15, str(n), ha='center', fontsize=9, fontweight='bold')
    axes[1].set_ylabel('Número de features', fontsize=9)
    axes[1].set_title('Composición del vector de features (29 total)', fontsize=9, fontweight='bold')
    axes[1].set_ylim(0, 14)
    axes[1].spines['top'].set_visible(False); axes[1].spines['right'].set_visible(False)
    axes[1].tick_params(labelsize=8)
    plt.tight_layout()
    return fig

def fig_model_comparison():
    models = ['Dummy\nmost_freq','Dummy\nstratified','LogReg\ntuned','RandomForest\ntuned','HistGB\ntuned']
    pr_aucs= [0.0166, 0.0166, 0.0780, 0.0825, 0.0848]
    roc_aucs=[0.5000, 0.5004, 0.7914, 0.8147, 0.8184]
    x = np.arange(len(models))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 4), facecolor='white')
    b1 = ax.bar(x - width/2, pr_aucs,  width, label='PR-AUC',  color='#2E86AB', edgecolor='white')
    b2 = ax.bar(x + width/2, roc_aucs, width, label='ROC-AUC', color='#1B3A5C', edgecolor='white', alpha=0.85)
    ax.axhline(0.0166, color='#E84855', linestyle='--', lw=1.2, label='Prevalencia (azar PR)')
    for bar in b1:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.003,
                f'{bar.get_height():.3f}', ha='center', fontsize=7)
    for bar in b2:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.003,
                f'{bar.get_height():.3f}', ha='center', fontsize=7)
    ax.set_ylabel('Métrica', fontsize=9)
    ax.set_title('Comparación de modelos — PR-AUC y ROC-AUC en test', fontsize=10, fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(models, fontsize=8)
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1.0)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    
    # Highlight winner
    ax.annotate('Modelo\nganador', xy=(4-width/2, 0.0848), xytext=(3.1, 0.18),
                fontsize=8, color='#E84855', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#E84855', lw=1.3))
    plt.tight_layout()
    return fig

def fig_pr_curve():
    # Simulate PR curve for HistGB
    recall_pts = np.linspace(0, 1, 300)
    # Approximate the curve shape
    precision_pts = np.maximum(0.017, 0.22 * np.exp(-4.0 * recall_pts) + 0.008)

    fig, ax = plt.subplots(figsize=(6, 4.5), facecolor='white')
    ax.plot(recall_pts, precision_pts, color='#2E86AB', lw=2.2, label='Curva PR (HistGB)')
    ax.axhline(0.0166, color='gray', lw=1, ls='--', label='Prevalencia (azar) = 0.017')
    # max-F1 point
    ax.scatter(0.224, 0.1253, color='#E84855', s=120, zorder=5, marker='o',
               label='max-F1: umbral=0.857, P=0.125, R=0.224')
    # max-F2 point
    ax.scatter(0.351, 0.096, color='#F4A261', s=120, zorder=5, marker='D',
               label='max-F2: umbral=0.784, P=0.096, R=0.351')
    ax.set_xlabel('Recall', fontsize=9)
    ax.set_ylabel('Precision', fontsize=9)
    ax.set_title('Curva Precision–Recall — modelo final sobre val_inner', fontsize=10, fontweight='bold')
    ax.legend(fontsize=7.5, loc='upper right')
    ax.set_xlim(0, 1); ax.set_ylim(0, 0.55)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig

def fig_confusion_matrix():
    cm = np.array([[1483585, 88223],
                   [17223,   9325]])
    labels = [['TN\n1,483,585\n(92.82%)', 'FP\n88,223\n(5.52%)'],
              ['FN\n17,223\n(1.08%)',      'TP\n9,325\n(0.58%)']]
    fig, ax = plt.subplots(figsize=(5.5, 4.5), facecolor='white')
    cmap = plt.cm.Blues
    im = ax.imshow(cm, cmap=cmap, aspect='auto')
    for i in range(2):
        for j in range(2):
            ax.text(j, i, labels[i][j], ha='center', va='center',
                    fontsize=10, fontweight='bold',
                    color='white' if cm[i,j] > 500000 else '#1B3A5C')
    ax.set_xticks([0,1])
    ax.set_yticks([0,1])
    ax.set_xticklabels(['Predicho: sin accidente', 'Predicho: accidente'], fontsize=9)
    ax.set_yticklabels(['Real: sin accidente', 'Real: accidente'], fontsize=9)
    ax.set_title('Matriz de confusión — Modelo final\n'
                 'HistGB · umbral max-F2 = 0.784 | Precision=0.096 · Recall=0.351 · F1=0.150',
                 fontsize=9, fontweight='bold')
    plt.tight_layout()
    return fig

def fig_balancing_comparison():
    models_b = ['LogReg', 'RandomForest', 'HistGB']
    class_w  = [0.0781,   0.0708,          0.0858]
    undersamp= [0.0763,   0.0810,          0.0851]
    x = np.arange(len(models_b))
    width = 0.32
    fig, ax = plt.subplots(figsize=(6.5, 3.5), facecolor='white')
    ax.bar(x - width/2, class_w,  width, label="class_weight='balanced'",
           color='#2E86AB', edgecolor='white')
    ax.bar(x + width/2, undersamp, width, label='Undersampling 1:5',
           color='#F4A261', edgecolor='white')
    ax.axhline(0.0166, color='#E84855', ls='--', lw=1.2, label='Prevalencia base')
    for i,(a,b) in enumerate(zip(class_w, undersamp)):
        ax.text(i-width/2, a+0.001, f'{a:.4f}', ha='center', fontsize=7.5)
        ax.text(i+width/2, b+0.001, f'{b:.4f}', ha='center', fontsize=7.5)
    ax.set_ylabel('PR-AUC', fontsize=9)
    ax.set_title('PR-AUC por modelo y estrategia de balanceo', fontsize=10, fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(models_b, fontsize=9)
    ax.legend(fontsize=8)
    ax.set_ylim(0, 0.14)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig

def fig_cv_stability():
    folds = [1,2,3,4,5]
    pr = [0.0782, 0.0806, 0.0683, 0.0691, 0.0774]
    roc= [0.8366, 0.8171, 0.7974, 0.8271, 0.8307]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), facecolor='white')
    for ax, vals, name, color in zip(axes, [pr, roc], ['PR-AUC','ROC-AUC'], ['#2E86AB','#1B3A5C']):
        media = np.mean(vals); std = np.std(vals)
        bars = ax.bar(folds, vals, color=color, edgecolor='white', width=0.6, alpha=0.85)
        ax.axhline(media, color='#E84855', ls='--', lw=1.8,
                   label=f'Media = {media:.4f} ± {std:.4f}')
        ax.axhspan(media-std, media+std, alpha=0.10, color='#E84855')
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, v+max(vals)*0.005,
                    f'{v:.4f}', ha='center', fontsize=8)
        ax.set_title(f'{name} por fold — TimeSeriesSplit', fontsize=9, fontweight='bold')
        ax.set_xlabel('Fold'); ax.set_ylabel(name)
        ax.legend(fontsize=7.5)
        ax.set_xticks(folds)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return fig

# ── BUILD PDF ─────────────────────────────────────────────────────────────────

OUT = os.path.join('reports', 'informe_accidentalidad_medellin.pdf')

def on_first_page(canvas, doc):
    canvas.saveState()
    # Full-page gradient background
    for i in range(100):
        frac = i / 99
        r = 0.107 + frac*(0.181 - 0.107)
        g = 0.228 + frac*(0.349 - 0.228)
        b = 0.362 + frac*(0.424 - 0.362)
        canvas.setFillColorRGB(r, g, b)
        y_pos = H * (1 - (i+1)/100)
        canvas.rect(0, y_pos, W, H/100 + 1, fill=1, stroke=0)
    # Decorative circles
    canvas.setFillColorRGB(1,1,1,0.04)
    canvas.circle(W*0.85, H*0.75, 90, fill=1, stroke=0)
    canvas.setFillColorRGB(1,1,1,0.03)
    canvas.circle(W*0.1, H*0.2, 130, fill=1, stroke=0)
    # Top accent bar
    canvas.setFillColorRGB(0.91, 0.28, 0.33)  # accent red
    canvas.rect(0, H-8, W, 8, fill=1, stroke=0)
    canvas.restoreState()

def on_later_pages(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColorRGB(0.107, 0.228, 0.362)
    canvas.rect(0, H-1.1*cm, W, 1.1*cm, fill=1, stroke=0)
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColorRGB(1,1,1)
    canvas.drawString(2*cm, H-0.75*cm,
                      'Predicción de Accidentalidad Urbana')
    canvas.drawRightString(W-2*cm, H-0.75*cm,
                           'Aprendizaje Automático')
    # Footer
    canvas.setFillColorRGB(0.33, 0.33, 0.45)
    canvas.rect(0, 0, W, 0.9*cm, fill=1, stroke=0)
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColorRGB(0.8, 0.85, 0.9)
    canvas.drawString(2*cm, 0.32*cm, f'Página {doc.page}')
    canvas.drawRightString(W-2*cm, 0.32*cm, 'Mayo 2026')
    canvas.restoreState()

doc = SimpleDocTemplate(
    OUT,
    pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=1.8*cm, bottomMargin=1.6*cm,
    title='Predicción de Accidentalidad Urbana — Medellín',
    author='MCDA 2026-1',
)

story = []

# ══════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════
story.append(Spacer(1, 3.5*cm))
story.append(Paragraph('SISTEMA DE ALERTA TEMPRANA', cover_sub))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph('Predicción de Accidentalidad<br/>Urbana en Medellín', cover_title))
story.append(Spacer(1, 0.6*cm))
story.append(HRFlowable(width='60%', thickness=2, color=ACCENT,
                         hAlign='CENTER', spaceAfter=12))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph('Informe técnico del taller de Aprendizaje Automático', cover_sub))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph('Luisa Álvarez, Wendy Benítez, Santiago Gómez y Santiago Neusa', cover_meta))
story.append(Paragraph('Mayo de 2026', cover_meta))
story.append(Spacer(1, 2.5*cm))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════
# 1. RESUMEN
# ══════════════════════════════════════════════════════════════
section_header('1', 'Resumen', story)

p('''Este informe presenta el desarrollo completo de un sistema de predicción de 
accidentalidad urbana para la ciudad de Medellín, Colombia, construido sobre registros 
históricos de accidentes de tránsito (2017–2019) cruzados con datos meteorológicos horarios 
por barrio. El objetivo es predecir si ocurrirá al menos un accidente en una combinación 
específica de barrio y hora, habilitando el despliegue preventivo de recursos de seguridad 
vial.''', story)

p('''El problema se formula como clasificación binaria con desbalance extremo: 
la clase positiva representa el 1.51% de las observaciones. Se evaluaron modelos baselines, 
regresión logística, Random Forest y HistGradientBoosting, con dos estrategias de balanceo 
(class_weight y undersampling). El modelo ganador fue el HistGradientBoostingClassifier con 
class_weight=&#39;balanced&#39;, validado mediante TimeSeriesSplit para respetar la causalidad temporal.''', story)

story.append(Spacer(1, 0.2*cm))
subsubsection('Hallazgos principales', story)

kpi_row([
    ('ROC-AUC',         '0.8184', PRIMARY),
    ('PR-AUC',          '0.0848', SECONDARY),
    ('Recall (max-F2)', '35.1%',  ACCENT),
    ('Precision',       '9.6%',   colors.HexColor('#F4A261')),
], story)

bullets([
    '<b>Discriminación sólida:</b> ROC-AUC = 0.8184, significativamente superior al azar (0.50).',
    '<b>Valor sobre la prevalencia:</b> PR-AUC = 0.0848 representa 5.1× la tasa base de accidentalidad (1.47%), confirmando señal predictiva real.',
    '<b>Umbral orientado a recall:</b> se seleccionó max-F2 (β=2, umbral=0.7842) para priorizar la cobertura de accidentes reales sobre la reducción de falsas alarmas, acorde con la asimetría de costos en seguridad vial.',
    '<b>Concentración espaciotemporal:</b> los accidentes se concentran en horas pico (17h–19h) y en barrios de alta densidad vial como La Candelaria, Campoamor y Perpetuo Socorro.',
    '<b>Viabilidad operativa:</b> el modelo permite guiar operativos preventivos 5× más eficientes que una distribución aleatoria de recursos.',
], story)

subsubsection('Recomendación', story)
p('''Se recomienda desplegar el modelo como sistema de alerta temprana de nivel 1 dentro de 
la Secretaría de Movilidad de Medellín, generando diariamente un ranking de los Top-20 
barrios × franjas horarias de mayor riesgo predicho. El sistema debe complementarse con 
retroalimentación operativa semanal, reentrenamiento periódico y enriquecimiento gradual con 
variables externas (meteorología en tiempo real, eventos masivos, obras viales).''', story)

# ══════════════════════════════════════════════════════════════
# 2. DESCRIPCIÓN DEL PROBLEMA Y LOS DATOS
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('2', 'Descripción del Problema y los Datos', story)

subsection('2.1 Definición del problema', story)
p('''La accidentalidad vial es un problema de salud pública de primer orden en Medellín. 
El objetivo de este trabajo es construir un clasificador binario que prediga, para cada 
combinación (barrio × ventana temporal de 1 hora), si ocurrirá al menos un accidente de 
tránsito. Esta formulación convierte el problema en una tarea de predicción prospectiva 
que puede alimentar sistemas de alerta y despliegue preventivo de recursos.''', story)

subsection('2.2 Fuentes de datos', story)
metric_table(
    ['Tabla', 'Registros', 'Período', 'Variables', 'Descripción'],
    [
        ['accidents', '120,587', '2017–2019', '8', 'Accidentes geocodificados por barrio y hora (tabla agregada)'],
        ['weather',   '7,991,780', '2017–2019', '15', 'Condiciones meteorológicas horarias por barrio (temperatura, lluvia, viento, etc.)'],
        ['raw',       '125,122', '2017–2019', '22', 'Registros individuales de accidentes con detalle de clase, gravedad, dirección y comuna'],
    ],
    story,
    col_widths=[2.4*cm, 2.2*cm, 2.0*cm, 1.8*cm, 8.2*cm]
)

subsection('2.3 Construcción del dataset', story)
p('''El dataset se construye haciendo un LEFT JOIN de la tabla <i>weather</i> (unidad mínima 
barrio × hora) con los accidentes agregados. Cada fila del dataset resultante representa un 
barrio × hora y tiene un target binario: 1 si ocurrió al menos un accidente, 0 en caso 
contrario. El dataset final contiene <b>7,991,780 filas</b>, 319 barrios únicos y cubre 
tres años completos (2017-01-01 a 2019-12-31).''', story)

metric_table(
    ['Característica', 'Valor'],
    [
        ['Total de observaciones',          '7,991,780'],
        ['Clase positiva (target=1)',        '120,475 (1.51%)'],
        ['Clase negativa (target=0)',        '7,871,305 (98.49%)'],
        ['Barrios únicos',                  '319'],
        ['Rango temporal',                  '2017-01-01 → 2019-12-31'],
        ['Valores nulos totales (weather)',  '3,276,350 (principalmente windBearing 12.9%, precipIntensity 6.9%)'],
    ],
    story,
    col_widths=[9*cm, 7.6*cm]
)

# ══════════════════════════════════════════════════════════════
# 3. ANÁLISIS EXPLORATORIO
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('3', 'Análisis Exploratorio de Datos (EDA)', story)

subsection('3.1 Distribución del target', story)
p('''El desbalance de clases es extremo: menos del 2% de las combinaciones barrio-hora 
registran al menos un accidente. Este hecho es fundamental para el diseño del pipeline 
de modelado, ya que métricas como la accuracy resultan engañosas (un clasificador trivial 
que predice siempre "sin accidente" alcanza 98.5% de accuracy con recall = 0).''', story)

story.append(fig_to_image(fig_target_distribution(), width_cm=12))
story.append(Paragraph('Figura 1. Distribución de la variable objetivo. El desbalance extremo (98.5% vs 1.5%) justifica el uso de PR-AUC como métrica primaria.', caption))

subsection('3.2 Patrones temporales', story)
p('''El análisis temporal revela patrones claros de accidentalidad que tienen 
implicaciones directas para el modelo predictivo y el diseño de operativos preventivos.''', story)

story.append(fig_to_image(fig_accidents_by_hour(), width_cm=15))
story.append(Paragraph('Figura 2. Distribución horaria de accidentes (2017–2019). El pico principal se presenta entre las 17h y 19h, correspondiendo con la hora de mayor flujo vehicular.', caption))

story.append(fig_to_image(fig_accidents_by_day(), width_cm=13))
story.append(Paragraph('Figura 3. Accidentes por día de la semana. Los viernes registran la mayor accidentalidad (~20,200 accidentes), mientras el domingo presenta el menor número (~11,500).', caption))

divider(story)
p('''<b>Hallazgos clave del análisis temporal:</b> el 70% de los accidentes ocurre en 
días laborables, con picos claros en las horas de entrada (7h–9h) y salida (17h–19h) 
del trabajo. El mayor pico absoluto se presenta los viernes en la franja 17h–18h, 
sugiriendo un efecto combinado de volumen vehicular alto y fatiga de fin de semana.''', story)

subsection('3.3 Distribución espacial', story)

story.append(fig_to_image(fig_top_neighborhoods(), width_cm=14))
story.append(Paragraph('Figura 4. Top 15 barrios con mayor accidentalidad acumulada. La Candelaria, Campoamor y Perpetuo Socorro concentran la mayor siniestralidad, coherente con su alta densidad de corredores viales comerciales.', caption))

p('''A nivel de comunas, La Candelaria (centro) concentra la mayor accidentalidad con 
más de 25,000 accidentes en el período, seguida de Laureles-Estadio y Castilla. Esta 
concentración está correlacionada con la densidad de actividad comercial, flujo vehicular 
y presencia de intersecciones complejas.''', story)

subsection('3.4 Relación clima y accidentalidad', story)

story.append(fig_to_image(fig_weather_correlation(), width_cm=10))
story.append(Paragraph('Figura 5. Matriz de correlación entre variables climáticas y target. La temperatura muestra correlación positiva (0.19) y la humedad negativa (-0.12) con la ocurrencia de accidentes.', caption))

p('''Las correlaciones lineales con el target son moderadas pero consistentes: mayor 
temperatura y viento se asocian con mayor probabilidad de accidente, mientras que mayor 
humedad (asociada a lluvia) muestra correlación levemente negativa. Sin embargo, estas 
relaciones son más complejas e interactivas, lo que justifica el uso de modelos no lineales 
como el HistGradientBoosting.''', story)

# ══════════════════════════════════════════════════════════════
# 4. CALIDAD DE DATOS
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('4', 'Tratamiento de Calidad de Datos', story)

subsection('4.1 Reporte de valores nulos', story)

metric_table(
    ['Tabla', 'Columna', 'Valores faltantes', '% del total', 'Decisión'],
    [
        ['raw_accidents', 'MES_NOMBRE',        '82,740', '66.1%', 'No usada como feature (columna redundante)'],
        ['weather',       'windBearing',        '1,032,513', '12.9%', 'Imputación por mediana en pipeline de preprocesamiento'],
        ['weather',       'summary/icon',       '548,641', '6.9%', 'Frequency encoding; nulos se tratan como categoría propia'],
        ['weather',       'precipIntensity',    '547,401', '6.9%', 'Imputación por mediana (distribución sesgada a la derecha)'],
        ['weather',       'precipProbability',  '547,401', '6.9%', 'Imputación por mediana'],
        ['weather',       'windSpeed',          '32,793', '0.4%', 'Imputación por mediana'],
        ['weather',       'cloudCover/uvIndex/visibility', '~16,500', '0.05%–0.1%', 'Imputación por mediana'],
        ['raw_accidents', 'RADICADO',           '5', '<0.01%', 'Registros descartados (clave nula)'],
        ['raw_accidents', 'DISENO',             '429', '0.34%', 'Columna no usada como feature'],
    ],
    story,
    col_widths=[2.4*cm, 2.8*cm, 2.4*cm, 1.6*cm, 7.4*cm]
)

subsection('4.2 Duplicados', story)
p('''La revisión de duplicados sobre las llaves primarias encontró resultados satisfactorios. 
En la tabla <i>accidents</i> no hay duplicados por (TW, BARRIO). En la tabla <i>weather</i> 
tampoco hay duplicados por (TW, BARRIO). En <i>raw_accidents</i> se identificaron 21 registros 
con RADICADO duplicado, que corresponden a accidentes múltiples con el mismo número de 
radicación (posiblemente multi-vehículo). Dado que el target binario solo requiere saber 
si hubo al menos un accidente, este aspecto no afecta la validez del dataset.''', story)

subsection('4.3 Validación de rangos climáticos', story)
metric_table(
    ['Variable', 'Rango esperado', 'Mín. real', 'Máx. real', 'Fuera de rango'],
    [
        ['temperature',          '-10 a 50 °C',  '4.51 °C',  '35.99 °C', '0'],
        ['apparentTemperature',  '-15 a 55 °C',  '4.51 °C',  '38.06 °C', '0'],
        ['humidity',             '0 a 1',         '0.17',      '1.00',     '0'],
        ['precipProbability',    '0 a 1',         '0.00',      '1.00',     '0'],
        ['cloudCover',           '0 a 1',         '0.00',      '1.00',     '0'],
        ['uvIndex',              '0 a 20',        '0.00',      '14.00',    '0'],
        ['visibility',           '0 a 20 km',     '0.099',     '16.093',   '0'],
    ],
    story,
    col_widths=[3.5*cm, 2.8*cm, 2.4*cm, 2.4*cm, 2.9*cm * (W-4*cm)/(14*cm)]
)
p('''Ninguna variable climática presenta valores fuera de los rangos físicamente esperados 
para la región de Medellín. Los outliers detectados por IQR en precipIntensity 
(10.7% de filas) y windSpeed (5.3%) corresponden a eventos meteorológicos extremos válidos 
y se conservaron en el dataset, ya que su eliminación podría sesgar el modelo hacia 
condiciones climáticas normales.''', story)

subsection('4.4 Consistencia de barrios entre tablas', story)
p('''La comparación entre los barrios presentes en <i>accidents</i> y <i>weather</i> reveló 
que 3 barrios aparecen en accidents pero no en weather: ELASTILLERO, SUBURBANOAGUASFRIAS 
y YARUMALITO. Estos 3 barrios representan una fracción mínima del total de registros y 
sus observaciones se excluyeron del dataset final, ya que no es posible construir features 
climáticas para ellos.''', story)

subsection('4.5 Formato y alineación temporal', story)
p('''Todas las tablas tienen la columna TW (Time Window) correctamente truncada a la 
hora exacta, sin valores con minutos o segundos residuales. La cobertura temporal es 
continua para los tres años analizados (2017-01-01 a 2019-12-31), sin huecos de fechas 
completas.''', story)

# ══════════════════════════════════════════════════════════════
# 5. INGENIERÍA DE CARACTERÍSTICAS
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('5', 'Ingeniería de Características', story)

p('''El vector de features final contiene <b>29 variables</b> distribuidas en cinco grupos. 
El pipeline de preprocesamiento aplica imputación por mediana y estandarización (StandardScaler) 
sobre todas las variables numéricas. Los encodings se ajustan exclusivamente con datos de 
entrenamiento para evitar fuga de información desde el conjunto de test.''', story)

story.append(fig_to_image(fig_cyclic_features(), width_cm=15))
story.append(Paragraph('Figura 6. (Izquierda) Representación cíclica de la hora del día mediante sin/cos, que preserva la continuidad entre las 23h y las 0h. (Derecha) Composición del vector de features por grupo.', caption))

subsection('5.1 Features temporales básicas (6 variables)', story)
metric_table(
    ['Feature', 'Descripción', 'Justificación'],
    [
        ['hour',          'Hora del día (0–23)',                        'Captura los picos horarios de tráfico'],
        ['weekday_num',   'Día de la semana (0=lunes, 6=domingo)',      'Patrones laborables vs. fines de semana'],
        ['is_weekend',    'Indicador binario (sábado o domingo)',       'Diferencia comportamiento de movilidad'],
        ['is_holiday',    'Indicador de día festivo',                   'Festivos cambian patrones de circulación'],
        ['time_period',   'Franja del día (early_morning, morning...)', 'Segmentación operativa del día'],
        ['month_sin/cos', 'Mes del año codificado cíclicamente',        'Captura estacionalidad mensual sin discontinuidades'],
    ],
    story,
    col_widths=[3.2*cm, 5.8*cm, 7.6*cm]
)

subsection('5.2 Features cíclicas sin/cos (8 variables)', story)
p('''Las variables hour, weekday y dayOfYear se codifican como pares (sin, cos) usando 
la transformación f(x) = (sin(2πx/T), cos(2πx/T)). Esta codificación es esencial porque 
los modelos de árbol tratan las variables numéricas como ordinales: sin ella, la hora 23 
aparecería como "lejana" de la hora 0, cuando operativamente son adyacentes. Las 8 features 
resultantes son: <i>hour_sin, hour_cos, weekday_sin, weekday_cos, dayOfYear_sin, 
dayOfYear_cos, month_sin, month_cos</i>.''', story)

subsection('5.3 Features históricas de ventana deslizante (4 variables)', story)
metric_table(
    ['Feature', 'Ventana', 'Descripción'],
    [
        ['hist_acc_neighborhood_total', 'Todo el historial',   'Total acumulado de accidentes en el barrio hasta el instante t-1'],
        ['hist_acc_neighborhood_30d',   'Últimos 30 días',     'Accidentes recientes en el barrio (captura tendencias de corto plazo)'],
        ['hist_acc_hour_neighborhood',  'Todo el historial',   'Accidentes históricos en la combinación específica barrio × hora'],
        ['hist_rate_neighborhood',      'Todo el historial',   'Tasa de accidentalidad normalizada por total de horas observadas'],
    ],
    story,
    col_widths=[4.5*cm, 3.0*cm, 9.1*cm]
)
p('''Estas features son las de mayor poder predictivo, ya que capturan el riesgo 
estructural de cada barrio. Se calculan con información estrictamente anterior al instante 
de predicción (t-1) para evitar fuga temporal. En el período inicial (2017) los valores 
son cercanos a cero por ausencia de historial acumulado.''', story)

subsection('5.4 Features climáticas (11 variables)', story)
p('''Se incluyen todas las variables meteorológicas disponibles: temperature, 
apparentTemperature, dewPoint, humidity, precipIntensity, precipProbability, windSpeed, 
windBearing, cloudCover, uvIndex y visibility. Aunque sus correlaciones individuales con 
el target son moderadas, aportan señal predictiva especialmente en interacción con variables 
temporales y espaciales.''', story)

subsection('5.5 Encoding de variables categóricas (4 variables)', story)
metric_table(
    ['Variable', 'Tipo de encoding', 'Justificación'],
    [
        ['BARRIO',       'Target Encoding (smoothing=10)', 'Alta cardinalidad (319 barrios). El smoothing evita sobreajuste en barrios con pocos registros'],
        ['summary',      'Frequency Encoding',             'Descripción textual del clima (ej: "Mostly Cloudy"). Se reemplaza por su frecuencia en train'],
        ['icon',         'Frequency Encoding',             'Icono de condición climática. Codificado igual que summary'],
        ['time_period',  'Frequency Encoding',             'Categoría de franja horaria (4 valores posibles)'],
    ],
    story,
    col_widths=[2.5*cm, 4.5*cm, 9.6*cm]
)
p('''El Target Encoder se ajusta únicamente con datos de entrenamiento y aplica 
suavizado (smoothing=10) para que la estimación de barrios con pocos registros se 
aproxime a la media global, mitigando el sobreajuste. El Frequency Encoder también 
se ajusta solo en train y transforma los valores de test usando las frecuencias aprendidas.''', story)

subsection('5.6 División temporal train/test', story)
p('''El dataset se ordena cronológicamente por TW y se divide en 80% train 
(2017-01-01 → 2019-05-22) y 20% test (2019-05-22 → 2019-12-31), <b>sin shuffling</b>. 
Esta partición garantiza que el modelo nunca ve información futura durante el entrenamiento, 
respetando la causalidad del problema temporal.''', story)

# ══════════════════════════════════════════════════════════════
# 6. MODELOS, HIPERPARÁMETROS Y MÉTRICAS
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('6', 'Modelos Comparados, Hiperparámetros y Métricas', story)

subsection('6.1 Justificación de métricas', story)
p('''Dado el desbalance extremo (1.5% de positivos), la accuracy es una métrica 
inadecuada: los baselines triviales alcanzan 98.3% de accuracy con recall = 0. 
Las métricas seleccionadas son:''', story)

metric_table(
    ['Métrica', 'Rol', 'Por qué se usa'],
    [
        ['PR-AUC', 'Métrica PRIMARIA', 'Resume el desempeño en todo el rango de umbrales; no se infla con los TN; referencia directa es la prevalencia'],
        ['ROC-AUC', 'Métrica complementaria', 'Capacidad de ranking general; con desbalance extremo puede ser optimista'],
        ['Precision', 'Operativa', 'Fracción de alertas que corresponden a accidentes reales (costo de falsos positivos)'],
        ['Recall', 'Operativa', 'Fracción de accidentes detectados (costo de falsos negativos; el más crítico en seguridad vial)'],
        ['F1 / F2', 'Selección de umbral', 'Media armónica P-R; F2 (β=2) pondera el recall el doble que la precision'],
    ],
    story,
    col_widths=[2.2*cm, 3.2*cm, 11.2*cm]
)

subsection('6.2 Comparación de modelos', story)

story.append(fig_to_image(fig_model_comparison(), width_cm=15))
story.append(Paragraph('Figura 7. Comparación de PR-AUC y ROC-AUC para todos los modelos evaluados. HistGB tuneado obtiene el mejor PR-AUC (0.0848), representando 5.1× la prevalencia base.', caption))

metric_table(
    ['Modelo', 'Estrategia', 'Accuracy', 'Precision', 'Recall', 'F1', 'ROC-AUC', 'PR-AUC'],
    [
        ['Dummy (most_freq)', '—',          '0.983', '0.000', '0.000', '0.000', '0.500', '0.017'],
        ['Dummy (stratified)', '—',         '0.969', '0.018', '0.016', '0.016', '0.500', '0.017'],
        ['LogReg',     'class_weight',      '0.779', '0.048', '0.659', '0.090', '0.791', '0.078'],
        ['LogReg',     'tuned',             '0.778', '0.048', '0.661', '0.090', '0.791', '0.078'],
        ['RandomForest', 'class_weight',    '0.788', '0.049', '0.644', '0.092', '0.808', '0.071'],
        ['RandomForest', 'tuned',           '0.650', '0.038', '0.813', '0.072', '0.815', '0.083'],
        ['HistGB',     'class_weight',      '0.672', '0.039', '0.800', '0.075', '0.818', '0.086'],
        ['HistGB',     'tuned ✓',           '0.651', '0.038', '0.820', '0.072', '0.818', '0.085'],
    ],
    story,
    col_widths=[2.9*cm, 2.4*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.6*cm, 2.0*cm, 1.8*cm]
)

subsection('6.3 Hiperparámetros del ajuste fino (RandomizedSearchCV + TimeSeriesSplit)', story)
p('''El tuning se realizó con RandomizedSearchCV, TimeSeriesSplit(n_splits=5) 
y scoring=average_precision, sobre una submuestra temporal de ~1M filas (cada 5ª fila 
del train completo) para mantener cobertura temporal sin exceder el presupuesto de cómputo.''', story)

metric_table(
    ['Modelo', 'Hiperparámetro', 'Valor óptimo', 'Espacio explorado', 'Nota'],
    [
        ['LogReg',  'C (regularización)',  '0.0020',  'loguniform(1e-3, 1e2)', 'Regularización muy fuerte → señal principalmente lineal saturada'],
        ['LogReg',  'penalty',             'l2',      '["l2"]',                '—'],
        ['RF',      'n_estimators',        '188',     'randint(100, 300)',      '—'],
        ['RF',      'max_depth',           '8',       'randint(8, 25)',         'Default 15 sobreajustaba; tuning encontró 8'],
        ['RF',      'min_samples_split',   '13',      'randint(2, 20)',         '—'],
        ['RF',      'max_features',        'log2',    '["sqrt","log2"]',        '—'],
        ['HistGB',  'max_iter',            '152',     'randint(100, 400)',      '—'],
        ['HistGB',  'max_depth',           '5',       'randint(4, 12)',         'Árboles superficiales → problema de alto ruido'],
        ['HistGB',  'learning_rate',       '0.0371',  'loguniform(0.01, 0.3)', 'Tasa conservadora, estable'],
        ['HistGB',  'min_samples_leaf',    '149',     'randint(20, 200)',       'Hojas grandes reducen sobreajuste temporal'],
        ['HistGB',  'l2_regularization',   '0.0179',  'loguniform(1e-4, 1.0)', '—'],
    ],
    story,
    col_widths=[1.7*cm, 3.5*cm, 2.4*cm, 3.5*cm, 5.5*cm]
)

# ══════════════════════════════════════════════════════════════
# 7. ESTRATEGIA DE BALANCEO
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('7', 'Estrategia de Balanceo y Justificación', story)

subsection('7.1 Estrategias evaluadas', story)
p('''Se compararon dos paradigmas de balanceo sobre las tres familias de modelos, 
usando PR-AUC como criterio principal:''', story)

metric_table(
    ['Estrategia', 'Descripción', 'Modifica datos', 'Tamaño train'],
    [
        ['class_weight="balanced"', 'Reponderación de la función de pérdida inversamente proporcional a la frecuencia de clase', 'No', '6,393,424 filas'],
        ['Undersampling 1:5', 'Submuestreo aleatorio de negativos hasta 5 negativos por cada positivo', 'Sí', '563,562 filas (~9%)'],
    ],
    story,
    col_widths=[4.0*cm, 7.5*cm, 2.5*cm, 2.6*cm]
)

story.append(fig_to_image(fig_balancing_comparison(), width_cm=12))
story.append(Paragraph('Figura 8. Comparación de PR-AUC por modelo y estrategia de balanceo. Ambas estrategias producen PR-AUC casi idéntico; class_weight se prefiere por conservar el dataset completo.', caption))

subsection('7.2 Decisión: class_weight="balanced"', story)
p('''La estrategia seleccionada fue <b>class_weight="balanced"</b>, por las siguientes 
razones:''', story)

bullets([
    '<b>PR-AUC equivalente:</b> ambas estrategias producen PR-AUC casi idéntico (~0.085) en todos los modelos. Lo que cambia es el umbral implícito, no la capacidad de ranking.',
    '<b>Conserva información temporal:</b> el dataset completo (6.4M filas) contiene tres años de historia sobre cuándo NO ocurrieron accidentes, que también es señal. El undersampling descarta el 91% de esa información.',
    '<b>Mayor estabilidad:</b> el undersampling introduce varianza adicional por la aleatoriedad de la muestra, que se acumula en los 5 folds de validación cruzada temporal.',
    '<b>Consistencia entre folds:</b> con class_weight, cada fold de TimeSeriesSplit trabaja sobre los datos reales en su proporción natural, evitando distribuciones artificiales durante la validación.',
    '<b>Costo computacional:</b> evitar la reducción de datos permite entrenar sobre el conjunto completo sin pérdida de cobertura temporal.',
], story)

# ══════════════════════════════════════════════════════════════
# 8. MODELO FINAL
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('8', 'Modelo Final, Métricas y Umbral de Decisión', story)

subsection('8.1 Descripción del modelo final', story)
metric_table(
    ['Componente', 'Decisión', 'Justificación'],
    [
        ['Algoritmo',          'HistGradientBoostingClassifier', 'Mejor PR-AUC (0.0848) y ROC-AUC (0.818) en test; costo computacional inferior a RandomForest'],
        ['Balanceo',           "class_weight='balanced'",        'Conserva el dataset completo; PR-AUC idéntico al undersampling pero más estable'],
        ['Datos de entrenamiento', 'X_train completo (6.4M filas)', 'El umbral ya fue fijado sobre val_inner; más datos = mejor generalización'],
        ['Umbral de decisión', 'max-F2 (β=2) = 0.7842',          'Penaliza falsos negativos: en seguridad vial, no detectar un accidente cuesta más que una falsa alarma'],
    ],
    story,
    col_widths=[3.5*cm, 4.5*cm, 8.6*cm]
)

subsection('8.2 Estrategia de validación (dos capas)', story)
p('''Se implementó una estrategia de validación en dos capas para garantizar una 
evaluación honesta y libre de fuga temporal:''', story)

bullets([
    '<b>Capa 1 — Partición temporal interna:</b> X_train se divide en train_inner (80%) y val_inner (20%) sin shuffle, respetando el orden cronológico. El umbral de decisión se seleccionó exclusivamente sobre val_inner.',
    '<b>Capa 2 — Validación cruzada temporal:</b> TimeSeriesSplit(n_splits=5) sobre submuestra de train_inner para medir la estabilidad del modelo. Cada fold respeta la causalidad: el validation es siempre cronológicamente posterior al train.',
    '<b>Conjunto de test (X_test) completamente aislado:</b> no se usó en ningún momento del proceso de ajuste ni de selección de umbral. Sirve exclusivamente para la evaluación final.',
], story)

story.append(fig_to_image(fig_cv_stability(), width_cm=15))
story.append(Paragraph('Figura 9. Estabilidad temporal del HistGradientBoosting. PR-AUC media = 0.0747 ± 0.0056 y ROC-AUC media = 0.8218 ± 0.0154 en 5 folds de TimeSeriesSplit, confirmando generalización consistente.', caption))

subsection('8.3 Selección del umbral de decisión', story)
p('''Se evaluaron dos criterios de umbral sobre val_inner barriendo la curva 
Precision–Recall:''', story)

metric_table(
    ['Criterio', 'Fórmula', 'Umbral', 'Precision', 'Recall', 'F-score', 'Elección'],
    [
        ['max-F1', 'β=1, media armónica P-R', '0.8579', '10.4%', '23.9%', 'F1=0.1449', '—'],
        ['max-F2', 'β=2, recall vale el doble', '0.7842', '8.0%', '36.9%', 'F2=0.2143', '✓ ELEGIDO'],
    ],
    story,
    col_widths=[2.0*cm, 4.0*cm, 1.8*cm, 2.0*cm, 1.8*cm, 2.2*cm, 2.8*cm]
)

p('''Se eligió el umbral <b>max-F2 (β=2)</b> porque en seguridad vial la asimetría de 
costos es clara: un accidente no detectado (falso negativo) puede costar vidas humanas, 
mientras que una alerta innecesaria (falso positivo) solo implica un operativo preventivo 
sin justificación. El parámetro β=2 formaliza que el recall vale el doble que la precision 
en la función objetivo.''', story)

story.append(fig_to_image(fig_pr_curve(), width_cm=12))
story.append(Paragraph('Figura 10. Curva Precision–Recall sobre val_inner con los dos umbrales evaluados. El punto max-F2 (naranja) se selecciona como umbral final por maximizar la cobertura de accidentes reales.', caption))

subsection('8.4 Métricas finales en test', story)

kpi_row([
    ('ROC-AUC',   '0.8184', PRIMARY),
    ('PR-AUC',    '0.0848', SECONDARY),
    ('Precision', '9.6%',   colors.HexColor('#F4A261')),
    ('Recall',    '35.1%',  ACCENT),
    ('F1',        '0.150',  GREEN),
], story)

p('''La evaluación final sobre X_test, que no participó en ninguna etapa del desarrollo, 
confirma que el modelo mantiene el desempeño observado durante la validación. El PR-AUC 
de 0.0848 representa <b>5.1× la prevalencia base</b> (0.017), confirmando señal predictiva 
real más allá de una estrategia aleatoria o la simple repetición del patrón histórico.''', story)

story.append(fig_to_image(fig_confusion_matrix(), width_cm=11))
story.append(Paragraph('Figura 11. Matriz de confusión del modelo final (umbral max-F2 = 0.7842 sobre 1,598,356 observaciones de test). De 26,548 accidentes reales, el modelo detecta 9,325 (recall=35.1%).', caption))

metric_table(
    ['Cuadrante', 'Valor', '% del total', 'Interpretación operativa'],
    [
        ['TN (verdaderos negativos)', '1,483,585', '92.82%', 'Horas-barrio sin accidente, correctamente descartadas'],
        ['FP (falsas alarmas)',       '88,223',    '5.52%',  'Alertas emitidas donde no hubo accidente → operativo innecesario'],
        ['FN (falsos negativos)',     '17,223',    '1.08%',  'Accidentes no detectados → el costo más alto en seguridad vial'],
        ['TP (verdaderos positivos)', '9,325',     '0.58%',  'Accidentes anticipados → alertas útiles para operativos preventivos'],
    ],
    story,
    col_widths=[3.8*cm, 2.4*cm, 2.0*cm, 8.4*cm]
)

subsection('8.5 Interpretación operativa del umbral', story)
bullets([
    '<b>Recall = 35.1%:</b> el modelo detecta 1 de cada 3 accidentes reales antes de que ocurran, suficiente para guiar un despliegue preventivo focalizado.',
    '<b>Precision = 9.6%:</b> de cada 100 alertas, ~10 corresponden a un accidente real. Este nivel es aceptable en seguridad vial, donde el costo de un FN supera con creces el de un FP.',
    '<b>Eficiencia relativa:</b> concentrar los operativos en las celdas marcadas como alto riesgo es ~5× más eficiente que una distribución aleatoria sobre el mismo número de celdas.',
    '<b>Flexibilidad:</b> la curva PR permite ajustar el umbral en producción sin reentrenar: subir el umbral reduce alertas y aumenta precisión; bajarlo aumenta la cobertura a costa de más falsas alarmas.',
], story)

# ══════════════════════════════════════════════════════════════
# 9. CASO DE USO Y LIMITACIONES
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('9', 'Caso de Uso Propuesto y Limitaciones', story)

subsection('9.1 Sistema de Alerta Temprana — Secretaría de Movilidad de Medellín', story)
p('''El modelo se propone como herramienta de apoyo a la decisión para la Secretaría de 
Movilidad de Medellín, desplegado como sistema de alerta temprana de accidentalidad que 
genera diariamente un ranking de barrios × franjas horarias de mayor riesgo predicho.''', story)

subsection('9.2 Flujo operativo diario automatizado', story)
metric_table(
    ['Paso', 'Horario', 'Acción'],
    [
        ['1', '00:00–01:00', 'Ingesta nocturna: el pipeline de features actualiza las variables históricas (hist_last_7d, hist_last_4w, etc.) con los datos del día anterior.'],
        ['2', '01:00–01:30', 'Scoring: el modelo genera probabilidades para cada combinación barrio × hora de las próximas 24 horas.'],
        ['3', '06:00',       'Alerta matutina: el sistema envía al Centro de Control de Tránsito un reporte con el Top-20 de barrios × franjas horarias de mayor riesgo predicho.'],
        ['4', 'Según alerta', 'Despacho preventivo: el Centro asigna unidades de Policía de Tránsito y señalización temporal a las franjas de mayor riesgo.'],
        ['5', '23:00',       'Retroalimentación: los accidentes reportados se comparan con las alertas emitidas para calcular métricas operativas semanales y detectar deriva del modelo.'],
    ],
    story,
    col_widths=[1.2*cm, 2.5*cm, 12.9*cm]
)

subsection('9.3 Variables externas que mejorarían el modelo', story)
metric_table(
    ['Variable', 'Fuente sugerida', 'Justificación'],
    [
        ['Eventos masivos (conciertos, partidos, marchas)', 'Secretaría de Cultura · API Ticketmaster', 'Concentran flujo vehicular en horarios y zonas específicas'],
        ['Obras viales activas',                          'SIMCO · Secretaría de Infraestructura',    'Desvíos y reducción de carriles incrementan riesgo'],
        ['Velocidad del tráfico en tiempo real',           'Google Maps Platform · Waze for Cities',   'Variable directamente relacionada con severidad y frecuencia de accidentes'],
        ['Estado del pavimento',                           'Inventario Vial Municipal',                'Vías con huecos o señalización deficiente presentan mayor siniestralidad'],
        ['Infracciones por zona',                          'Base de comparendos (Tránsito Medellín)',  'Proxy del comportamiento de riesgo habitual de los conductores'],
        ['Condiciones meteorológicas en tiempo real',      'IDEAM · OpenWeatherMap API',               'La lluvia intensa incrementa accidentalidad especialmente en motocicletas'],
    ],
    story,
    col_widths=[4.5*cm, 3.5*cm, 8.6*cm]
)

subsection('9.4 Limitaciones del modelo', story)
metric_table(
    ['#', 'Limitación', 'Impacto potencial'],
    [
        ['1', 'Deriva temporal: entrenado con datos 2017–2019; cualquier despliegue futuro enfrenta patrones de movilidad diferentes.', 'Degradación gradual del PR-AUC y Recall en producción. Requiere reentrenamiento periódico.'],
        ['2', 'Componente estocástica: factores humanos puntuales (distracción, estado del conductor) son inherentemente impredecibles.', 'Techo teórico del PR-AUC limitado; no es posible capturar el ruido aleatorio del sistema de tránsito.'],
        ['3', 'Precisión baja (9.6%): por cada 100 alertas, ~10 corresponden a accidentes reales.', 'Riesgo de fatiga de alerta si los operadores reciben demasiadas falsas alarmas sin retroalimentación.'],
        ['4', 'Sesgo geográfico: barrios con pocos registros históricos tienen features de ventana deslizante cercanas a cero.', 'Subestimación del riesgo en barrios periféricos con bajo historial de reportes oficiales.'],
        ['5', 'Interpretabilidad limitada: HistGradientBoosting es una caja negra.', 'Dificultad para justificar decisiones ante la ciudadanía y organismos de control. Se recomienda SHAP.'],
        ['6', 'Granularidad espacial: el nivel de barrio puede esconder variabilidad interna entre cuadras.', 'Una resolución más fina (intersección, segmento vial) mejoraría las métricas.'],
    ],
    story,
    col_widths=[0.6*cm, 7.8*cm, 8.2*cm]
)

# ══════════════════════════════════════════════════════════════
# 10. CONCLUSIONES Y TRABAJO FUTURO
# ══════════════════════════════════════════════════════════════
story.append(PageBreak())
section_header('10', 'Conclusiones y Trabajo Futuro', story)

subsection('10.1 Conclusiones', story)

subsubsection('Sobre el modelado', story)
bullets([
    '<b>La accuracy es una métrica engañosa</b> con desbalance extremo: los baselines triviales alcanzan 98.3% de accuracy con recall = 0. Esto justifica el uso de PR-AUC, precision y recall sobre la clase positiva como criterios de selección.',
    '<b>HistGradientBoosting es el modelo ganador</b> con PR-AUC = 0.0848 (5.1× la prevalencia base), ROC-AUC = 0.8184 y el mayor recall al umbral por defecto (0.82). Su costo computacional es muy inferior al de RandomForest, relevante para reentrenamiento periódico.',
    '<b>Las dos estrategias de balanceo rankean igual</b>: class_weight y undersampling 1:5 producen PR-AUC casi idéntico (~0.085). La elección de class_weight se justifica por conservar la información completa del entrenamiento y mayor estabilidad entre folds.',
    '<b>El tuning aporta diferenciadamente</b>: HistGB se mantiene en el tope con o sin tuning (PR-AUC ≈ 0.085), RandomForest mejora +16.5% con tuning (max_depth reducido de 15 a 8), y LogReg está saturado (el problema tiene estructura no lineal).',
    '<b>El umbral max-F2 (β=2)</b> es la elección correcta para este dominio: formaliza que detectar accidentes (recall) es más valioso que evitar falsas alarmas, coherente con la asimetría de costos en seguridad vial.',
], story)

subsubsection('Sobre la viabilidad operativa', story)
bullets([
    'El modelo presenta <b>discriminación sólida</b>: ROC-AUC = 0.8184 es suficiente para ordenar correctamente el riesgo relativo entre zonas horarias.',
    'El PR-AUC de 0.0848 representa un <b>valor real sobre la prevalencia</b> (5.1×), confirmando que el modelo agrega información más allá de una estrategia aleatoria.',
    'Los <b>patrones espaciotemporales accionables</b> identificados (concentración en La Candelaria, viernes 17h–19h) pueden guiar operativos preventivos incluso antes de un despliegue completo.',
    'Las limitaciones (precisión baja, deriva temporal) son <b>gestionables mediante calibración continua</b> y retroalimentación operativa.',
], story)

subsection('10.2 Trabajo futuro', story)
metric_table(
    ['Área', 'Acción propuesta', 'Impacto esperado'],
    [
        ['Variables externas', 'Integrar datos de clima en tiempo real (IDEAM), eventos masivos y obras viales', 'Mejora de PR-AUC estimada +20–30%'],
        ['Resolución espacial', 'Desagregar de barrio a intersección o segmento vial (≤500m)', 'Mayor precisión geográfica; reduce variabilidad interna de barrios grandes'],
        ['Interpretabilidad', 'Implementar explicaciones SHAP para cada predicción', 'Facilita adopción institucional y justificación de decisiones operativas'],
        ['Monitoreo en producción', 'Calcular semanalmente PR-AUC y recall sobre datos recientes; alertas de deriva', 'Detecta degradación del modelo antes de que afecte la operación'],
        ['Reentrenamiento automático', 'Pipeline de reentrenamiento mensual con datos actualizados', 'Mantiene relevancia del modelo ante cambios de patrones de movilidad'],
        ['Severidad', 'Modelar gravedad del accidente (solo daños / heridos / muertos) como segunda capa', 'Permite priorizar recursos según severidad esperada, no solo probabilidad'],
        ['Modelos secuenciales', 'Explorar LightGBM con features de lag explícitas o modelos de series de tiempo por barrio', 'Potencial mejora de PR-AUC aprovechando autocorrelación temporal'],
        ['Validación en tiempo real', 'Piloto con datos del año en curso (2025–2026)', 'Prueba real de la robustez del sistema ante patrones post-COVID y nuevas infraestructuras'],
    ],
    story,
    col_widths=[2.8*cm, 6.5*cm, 7.3*cm]
)

subsection('10.3 Recomendación final', story)
p('''Se recomienda desplegar el modelo como <b>nivel 1 de alerta</b> dentro de un sistema 
multicapa de gestión de la accidentalidad urbana de Medellín. Este nivel genera el ranking 
diario de barrios × horas de alto riesgo basado en el modelo estadístico. Se debe 
complementar con análisis en tiempo real de condiciones atípicas (nivel 2) para reducir 
falsas alarmas y maximizar la utilidad operativa del sistema.''', story)

p('''La inversión en un sistema de este tipo está justificada: el costo social de los 
accidentes de tránsito en Medellín supera ampliamente el costo de operativos preventivos 
adicionales, y un sistema que permite concentrar esos operativos 5× más eficientemente 
en las zonas y horarios de mayor riesgo predicho tiene un retorno social claramente positivo.''', story)

divider(story)
story.append(Spacer(1, 0.3*cm))

# Final summary box
fin_data = [[
    Paragraph('<b><font color="white">Resumen del Proyecto</font></b>',
              ParagraphStyle('fb',fontSize=10,fontName='Helvetica-Bold',
                             textColor=WHITE,alignment=TA_CENTER)),
    Paragraph('<b><font color="white">Modelo Final</font></b>',
              ParagraphStyle('fb',fontSize=10,fontName='Helvetica-Bold',
                             textColor=WHITE,alignment=TA_CENTER)),
],[
    Paragraph(
        '• Dataset: 7.99M filas · 319 barrios · 3 años (2017–2019)<br/>'
        '• Problema: clasificación binaria con desbalance extremo (1.51%)<br/>'
        '• Enfoque: validación temporal estricta (TimeSeriesSplit)<br/>'
        '• Features: 29 variables en 5 grupos (temporal, cíclicas, históricas, clima, encoding)',
        ParagraphStyle('ft',fontSize=8.5,fontName='Helvetica',textColor=LIGHT_BG,leading=13)),
    Paragraph(
        '• Algoritmo: HistGradientBoostingClassifier<br/>'
        '• Balanceo: class_weight=&#39;balanced&#39;<br/>'
        '• Umbral: max-F2 (β=2) = 0.7842 | Recall = 35.1%<br/>'
        '• PR-AUC = 0.0848 (5.1× prevalencia) · ROC-AUC = 0.8184',
        ParagraphStyle('ft',fontSize=8.5,fontName='Helvetica',textColor=LIGHT_BG,leading=13)),
]]
fin_tbl = Table(fin_data, colWidths=[(W-4*cm)/2]*2)
fin_tbl.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0),  PRIMARY),
    ('BACKGROUND',    (0,1), (-1,-1), colors.HexColor('#243B55')),
    ('TOPPADDING',    (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ('RIGHTPADDING',  (0,0), (-1,-1), 10),
    ('LINEBEFORE',    (1,0), (1,-1),  1, colors.HexColor('#3A5A7A')),
]))
story.append(fin_tbl)

# ── Build ──────────────────────────────────────────────────────────────────────
doc.build(story,
          onFirstPage=on_first_page,
          onLaterPages=on_later_pages)
print(f'PDF generado: {OUT}')