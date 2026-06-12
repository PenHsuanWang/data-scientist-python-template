# Comprehensive Guide: Architecture Diagrams & Slides with LaTeX

This repository contains a modern, highly customized LaTeX framework designed specifically for Software Engineers and Data Scientists. It allows you to write your architecture diagrams, design documents, and presentation slides as pure, version-controllable code.

## Why Use LaTeX for Design Documents?
1. **Plain Text:** Your diagrams and slides are just text. You can track changes in Git, review diffs in PRs, and avoid binary merge conflicts that happen with Visio or Draw.io files.
2. **Infinite Scaling:** Diagrams are drawn using pure vector graphics via TikZ. They will never pixelate, regardless of zoom level.
3. **Consistency:** A single source of truth for colors (Tailwind-inspired) and typography (Inter/Helvetica) guarantees brand consistency across all artifacts.
4. **No External Dependencies:** No need for web-based tools or proprietary software. Everything compiles locally via standard LaTeX distributions.

---

## 1. Portability: How to Reuse This Framework in Other Projects

To use this framework in an entirely different project, you only need to copy the styling packages (`.sty`) and class files (`.cls`) into that project's directory.

### Required Files to Copy:
*   **For C4 Architecture Diagrams:**
    *   `modern-c4-style.sty` (Core styles and TikZ definitions)
    *   `modern-c4.cls` (Optional: If you want A4 documents)
*   **For Time Sequence Diagrams:**
    *   `modern-seq-style.sty` (Core macros and styles)
    *   `modern-seq.cls` (Optional)
*   **For UML Class Diagrams:**
    *   `modern-uml-style.sty` (Core macros and styles)
    *   `modern-uml.cls` (Optional)
*   **For 16:9 Presentations:**
    *   `modern-slide-style.sty`

### System Prerequisites
You must have a standard LaTeX distribution installed on your machine.
*   **macOS:** Install MacTeX via Homebrew: `brew install --cask mactex`
*   **Linux:** `sudo apt-get install texlive-full`
*   **Windows:** Install MiKTeX.

*(Note: The framework attempts to load the modern "Inter" font if compiled with `lualatex`, but gracefully falls back to Helvetica if compiled with `pdflatex` or `xelatex`.)*

---

## 2. API Reference & Diagram Implementation

To draw a diagram as a perfectly cropped standalone image (ideal for embedding in Markdown or wikis), wrap your code in the `standalone` class:

```latex
\documentclass[margin=15pt]{standalone}
\usepackage{<STYLE_PACKAGE_HERE>}
\begin{document}
\begin{tikzpicture}
    % ... diagram logic ...
\end{tikzpicture}
\end{document}
```

### A. C4 Architecture Diagrams (`modern-c4-style.sty`)

This package provides native TikZ representations of the C4 Model (Context, Containers, Components).

**Available Node Styles:**
*   `c4_person`: Vibrant Blue filled rectangle. Used for actors/users.
*   `c4_system`: Light Blue filled rectangle. Used for internal systems.
*   `c4_container`: White filled, dashed border. Used for apps, microservices.
*   `c4_external`: Slate Gray filled rectangle. Used for third-party systems.
*   `c4_database`: Emerald Green cylinder shape. Used for data stores.

**Available Path/Arrow Styles:**
*   `c4_rel`: A thick, standard relationship arrow.

**Example Usage:**
```latex
\documentclass[margin=15pt]{standalone}
\usepackage{modern-c4-style}
\begin{document}
\begin{tikzpicture}[node distance=2.5cm, auto]
    \node[c4_person] (user) {
        Customer \\ \normalfont\scriptsize End user of the app
    };
    \node[c4_system, right=of user] (api) {
        API Gateway \\ \normalfont\scriptsize Routes traffic
    };
    \node[c4_database, below=of api] (db) {
        Database \\ \normalfont\scriptsize PostgreSQL
    };

    \draw[c4_rel] (user) -- node {HTTPS REST} (api);
    \draw[c4_rel] (api) -- node {Reads/Writes} (db);
\end{tikzpicture}
\end{document}
```

### B. Time Sequence Diagrams (`modern-seq-style.sty`)

Instead of complex TikZ coordinate math, this package provides easy-to-use LaTeX macros to construct vertical lifelines and horizontal messages.

**Available Macros:**
*   `\def\seqheight{10}`: Set the total vertical length of the dashed lifelines.
*   `\seqactor{id}{Label}{x_position}`: Creates the actor block at the top and draws its downward lifeline.
*   `\seqactivate{id}{start_y}{end_y}`: Draws a light blue activation box on an actor's lifeline between two Y coordinates.
*   `\seqmessage{from_id}{to_id}{Label}{y_level}`: Draws a solid request arrow from one lifeline to another at a specific Y depth.
*   `\seqreturn{from_id}{to_id}{Label}{y_level}`: Draws a dashed response arrow.

**Example Usage:**
```latex
\documentclass[margin=15pt]{standalone}
\usepackage{modern-seq-style}
\begin{document}
\begin{tikzpicture}
    \def\seqheight{6} % Set lifelines to 6 units tall

    % Place actors at X=0 and X=5
    \seqactor{client}{Mobile App}{0}
    \seqactor{server}{Backend API}{5}

    % Add processing block on server from Y=1 to Y=3
    \seqactivate{server}{1}{3}

    % Draw messages
    \seqmessage{client}{server}{1. Authenticate}{1}
    \seqreturn{server}{client}{2. JWT Token}{3}
\end{tikzpicture}
\end{document}
```

### C. UML Class Diagrams (`modern-uml-style.sty`)

This package utilizes the `shapes.multipart` library to draw standard three-tier UML class boxes (Title, Fields, Methods).

**Available Node Styles:**
*   `uml_class`: Standard blue class header.
*   `uml_interface`: Green interface header.
*   `uml_abstract`: Gray abstract class header.
*(Use `\nodepart{two}` to list variables and `\nodepart{three}` for functions.)*

**Available Relationship Arrows:**
*   `uml_inherit`: Solid line, empty triangle (Subclass to Superclass).
*   `uml_realize`: Dashed line, empty triangle (Class to Interface).
*   `uml_compose`: Solid line, filled diamond (Part to Whole).
*   `uml_aggregate`: Solid line, empty diamond (Part to Whole).
*   `uml_assoc`: Solid line, standard arrow (Directed Association).
*   `uml_depend`: Dashed line, standard arrow (Dependency).

**Example Usage:**
```latex
\documentclass[margin=15pt]{standalone}
\usepackage{modern-uml-style}
\begin{document}
\begin{tikzpicture}[node distance=2cm, auto]
    \node[uml_class] (Order) {
        \textbf{Order}
        \nodepart{two}
        - orderId: String \\
        - amount: float
        \nodepart{three}
        + calculateTotal(): float
    };

    \node[uml_class, right=3cm of Order] (Item) {
        \textbf{OrderItem}
        \nodepart{two}
        - sku: String
        \nodepart{three}
        + getPrice(): float
    };

    % Composition: An Order is composed of OrderItems
    \draw[uml_compose] (Order) -- node[above] {1..*} (Item);
\end{tikzpicture}
\end{document}
```

---

## 3. Creating Modern 16:9 Presentations (Slides)

LaTeX uses the `beamer` class for slides. The `modern-slide-style.sty` package overrides Beamer's dated defaults to provide a clean, widescreen experience matching modern PowerPoint or Google Slides templates.

**Key Concepts:**
1.  **Aspect Ratio:** You must pass `[aspectratio=169]` to the `\documentclass` to enable widescreen.
2.  **Embedding Diagrams:** You can load `modern-c4-style`, `modern-seq-style`, or `modern-uml-style` simultaneously. This allows you to write `\begin{tikzpicture}` blocks *directly* inside your slides without having to export them to PNG/PDF first.
3.  **Resizing:** Use `\resizebox{0.9\textwidth}{!}{ ... }` around your TikZ picture to ensure it scales down gracefully if it's too large for the slide.

**Example Usage (`slides.tex`):**
```latex
\documentclass[aspectratio=169]{beamer}

\usepackage{modern-slide-style}
\usepackage{modern-c4-style} % Load our custom diagram definitions

\title{\textbf{Q3 Architecture Review}}
\author{Engineering Team}
\date{\today}

\begin{document}

\begin{frame}
    \titlepage
\end{frame}

\begin{frame}{Target Architecture}
    \centering
    \resizebox{0.7\textwidth}{!}{
        \begin{tikzpicture}[node distance=3cm, auto]
            \node[c4_system] (api) {API Gateway};
            \node[c4_database, right=of api] (db) {Database};
            \draw[c4_rel] (api) -- node {SQL} (db);
        \end{tikzpicture}
    }
\end{frame}

\end{document}
```

---

## 4. Compilation & Troubleshooting

### How to Build
Always compile using a command-line TeX engine. The easiest is `pdflatex`:

```bash
pdflatex -interaction=nonstopmode your_document.tex
```

If your document includes Table of Contents, References, or complex hyperlink anchors, you may need to run the command **twice** to allow LaTeX to resolve the references.

### Common Errors
*   **`File 'modern-XYZ-style.sty' not found.`**
    *   *Fix:* Ensure the `.sty` file is in the exact same directory as the `.tex` file you are trying to compile, or add it to your global `texmf` tree.
*   **`I do not know the key '/tikz/uml_compose'...`**
    *   *Fix:* You forgot to add `\usepackage{modern-uml-style}` in the preamble of your document.
*   **Diagram is cut off in `standalone` mode.**
    *   *Fix:* Sometimes TikZ bounding boxes miscalculate. Increase the margin in the document class: `\documentclass[margin=20pt]{standalone}`.
