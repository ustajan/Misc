#!/usr/bin/env bash
#
# combine_panels.sh — combine several PDF panels into one figure with
#                     bold panel labels (a, b, c, ...) at the top-left.
#
# Builds a standalone LaTeX document (TikZ) and compiles it with pdflatex.
# Labels are set in Helvetica (via the helvet package) so the output keeps
# fully editable, embedded TrueType/Type 1 text — no outlining.
#
# USAGE
#   ./combine_panels.sh -d v|h [options] panel1.pdf panel2.pdf [panel3.pdf ...]
#
# OPTIONS
#   -d, --direction v|h   Stack panels vertically (v) or horizontally (h). Required.
#   -o, --output FILE     Output PDF name.            (default: combined.pdf)
#   -s, --size DIM        Panel size: this is the WIDTH of each panel when
#                         stacking vertically, or the HEIGHT when horizontal.
#                         (default: 13cm for v, 6.5cm for h)
#   -g, --gap DIM         Gap between panels.         (default: 6pt)
#   -c, --crop            Tight-crop each input panel with Ghostscript first
#                         (removes surrounding whitespace). Requires `gs`.
#   -n, --no-labels       Do not draw a/b/c labels.
#       --start LETTER    First label letter.         (default: a)
#   -k, --keep            Keep the temporary build directory (for debugging).
#   -h, --help            Show this help.
#
# EXAMPLES
#   ./combine_panels.sh -d v -o Figure1.pdf  p1.pdf p2.pdf p3.pdf
#   ./combine_panels.sh -d h -o Figure3.pdf -s 6.5cm -c  left.pdf right.pdf
#
set -euo pipefail

# ----------------------------------------------------------------------------
# defaults
direction=""
output="combined.pdf"
size=""
gap="6pt"
crop=0
labels=1
start="a"
keep=0

usage() { sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

# ----------------------------------------------------------------------------
# parse arguments
inputs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--direction) direction="$2"; shift 2;;
    -o|--output)    output="$2";    shift 2;;
    -s|--size)      size="$2";      shift 2;;
    -g|--gap)       gap="$2";       shift 2;;
    -c|--crop)      crop=1;         shift;;
    -n|--no-labels) labels=0;       shift;;
    --start)        start="$2";     shift 2;;
    -k|--keep)      keep=1;         shift;;
    -h|--help)      usage 0;;
    --)             shift; while [[ $# -gt 0 ]]; do inputs+=("$1"); shift; done;;
    -*)             echo "Unknown option: $1" >&2; usage 1;;
    *)              inputs+=("$1"); shift;;
  esac
done

# ----------------------------------------------------------------------------
# validate
case "$direction" in
  v|vertical)   direction=v;;
  h|horizontal) direction=h;;
  "") echo "Error: direction is required (-d v|h)." >&2; usage 1;;
  *)  echo "Error: direction must be 'v' or 'h' (got '$direction')." >&2; exit 1;;
esac

if [[ ${#inputs[@]} -lt 1 ]]; then
  echo "Error: need at least one input PDF." >&2; usage 1
fi
for f in "${inputs[@]}"; do
  [[ -f "$f" ]] || { echo "Error: input not found: $f" >&2; exit 1; }
done

command -v pdflatex >/dev/null || { echo "Error: pdflatex not found." >&2; exit 1; }
if [[ $crop -eq 1 ]]; then
  command -v gs >/dev/null || { echo "Error: -c/--crop needs Ghostscript (gs)." >&2; exit 1; }
fi

# default size depends on direction
if [[ -z "$size" ]]; then
  [[ "$direction" == v ]] && size="13cm" || size="6.5cm"
fi
[[ "$direction" == v ]] && sizekey="width" || sizekey="height"

# label sequence a..z, starting at $start
alphabet=(a b c d e f g h i j k l m n o p q r s t u v w x y z)
startidx=0
for i in "${!alphabet[@]}"; do [[ "${alphabet[$i]}" == "$start" ]] && startidx=$i && break; done
if [[ ${#inputs[@]} -gt $((26 - startidx)) ]]; then
  echo "Error: too many panels for single-letter labels starting at '$start'." >&2; exit 1
fi

# ----------------------------------------------------------------------------
# build in a temp directory (sanitized filenames avoid spaces/path issues)
workdir="$(mktemp -d "${TMPDIR:-/tmp}/combine_panels.XXXXXX")"
cleanup() { [[ $keep -eq 0 ]] && rm -rf "$workdir" || echo "Kept build dir: $workdir"; }
trap cleanup EXIT

texfiles=()
for i in "${!inputs[@]}"; do
  src="${inputs[$i]}"
  dst="$workdir/in_${i}.pdf"
  if [[ $crop -eq 1 ]]; then
    # tight bounding box, then rewrite CropBox (preserves embedded fonts)
    bbox="$(gs -dQUIET -dBATCH -dNOPAUSE -sDEVICE=bbox "$src" 2>&1 \
            | sed -n 's/^%%HiResBoundingBox: //p' | head -1)"
    if [[ -n "$bbox" ]]; then
      read -r x0 y0 x1 y1 <<<"$bbox"
      m=2
      box="[$(awk "BEGIN{print $x0-$m}") $(awk "BEGIN{print $y0-$m}") $(awk "BEGIN{print $x1+$m}") $(awk "BEGIN{print $y1+$m}")]"
      gs -dQUIET -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -o"$dst" \
         -c "[/CropBox $box /PAGES pdfmark" -f "$src"
    else
      echo "Warning: could not crop $src; using as-is." >&2
      cp "$src" "$dst"
    fi
  else
    cp "$src" "$dst"
  fi
  texfiles+=("in_${i}.pdf")
done

# ----------------------------------------------------------------------------
# assemble the panel cells
panel_cmd='\panel'
[[ $labels -eq 0 ]] && panel_cmd='\panelnolabel'

body=""
if [[ "$direction" == v ]]; then
  colspec='@{}c@{}'
  for i in "${!texfiles[@]}"; do
    L="${alphabet[$((startidx + i))]}"
    if [[ $labels -eq 1 ]]; then
      body+="\\panel{$L}{$sizekey=$size}{${texfiles[$i]}}"
    else
      body+="\\panelnolabel{$sizekey=$size}{${texfiles[$i]}}"
    fi
    if [[ $i -lt $((${#texfiles[@]} - 1)) ]]; then
      body+=$'\\\\\n\\noalign{\\vskip '"$gap"$'}\n'
    fi
  done
else
  # horizontal: n columns separated by \hspace{gap}
  colspec='@{}c'
  for ((i=1; i<${#texfiles[@]}; i++)); do colspec+="@{\\hspace{$gap}}c"; done
  colspec+='@{}'
  for i in "${!texfiles[@]}"; do
    L="${alphabet[$((startidx + i))]}"
    if [[ $labels -eq 1 ]]; then
      body+="\\panel{$L}{$sizekey=$size}{${texfiles[$i]}}"
    else
      body+="\\panelnolabel{$sizekey=$size}{${texfiles[$i]}}"
    fi
    [[ $i -lt $((${#texfiles[@]} - 1)) ]] && body+=$' &\n'
  done
fi

# ----------------------------------------------------------------------------
# write the standalone LaTeX document
cat > "$workdir/combined.tex" <<EOF
\\documentclass[border=4pt]{standalone}
\\usepackage{graphicx}
\\usepackage{helvet}   % panel labels in Helvetica (editable, embedded)
\\usepackage{tikz}
% \\panel{label}{graphicx-opts}{file} : image with a bold label at top-left
\\newcommand{\\panel}[3]{%
  \\begin{tikzpicture}
    \\node[anchor=north west,inner sep=0] (img) {\\includegraphics[#2]{#3}};
    \\node[anchor=south west,font=\\sffamily\\bfseries\\large,text=black,inner sep=0]
      at ([yshift=2.5pt]img.north west) {#1};
  \\end{tikzpicture}}
\\newcommand{\\panelnolabel}[2]{\\includegraphics[#1]{#2}}
\\begin{document}
\\begin{tabular}{$colspec}
$body
\\end{tabular}
\\end{document}
EOF

# ----------------------------------------------------------------------------
# compile
( cd "$workdir" && pdflatex -interaction=nonstopmode -halt-on-error combined.tex >combined.build.log 2>&1 ) || {
  echo "Error: pdflatex failed. Log:" >&2
  sed -n '/^!/,+5p' "$workdir/combined.build.log" >&2
  keep=1
  exit 1
}

cp "$workdir/combined.pdf" "$output"
echo "Wrote $output  (${#inputs[@]} panels, $( [[ $direction == v ]] && echo vertical || echo horizontal ))"
