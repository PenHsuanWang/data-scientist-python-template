# LaTeX Diagram Templates and Syntax

This document provides the necessary syntax, node styles, and relationship arrows for drawing diagrams using the custom LaTeX framework.

## 1. Document Setup (Standalone)
For all standalone diagrams (C4, Sequence, UML), use the `standalone` class with a margin.
```latex
\documentclass[margin=15pt]{standalone}
\usepackage{<STYLE_PACKAGE_HERE>} % e.g., modern-c4-style
\begin{document}
\begin{tikzpicture}[node distance=2.5cm, auto]
    % ... diagram logic ...
\end{tikzpicture}
\end{document}
```

## 2. C4 Architecture Diagrams (`modern-c4-style.sty`)
Provides native TikZ representations of the C4 Model.

**Available Node Styles:**
*   `c4_person`: Vibrant Blue. Used for actors/users.
*   `c4_system`: Light Blue. Used for internal systems.
*   `c4_container`: White fill, dashed border. Used for apps, microservices.
*   `c4_external`: Slate Gray. Used for third-party systems.
*   `c4_database`: Emerald Green cylinder. Used for data stores.

**Available Path/Arrow Styles:**
*   `c4_rel`: Standard thick relationship arrow.

**Example C4 Context:**
```latex
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
```

## 3. Time Sequence Diagrams (`modern-seq-style.sty`)
Provides easy macros for vertical lifelines and horizontal messages without complex coordinate math.

**Available Macros:**
*   `\def\seqheight{10}`: Set the total vertical length of the dashed lifelines.
*   `\seqactor{id}{Label}{x_position}`: Creates actor block and downward lifeline.
*   `\seqactivate{id}{start_y}{end_y}`: Draws a light blue activation box on an actor's lifeline between two Y coordinates.
*   `\seqmessage{from_id}{to_id}{Label}{y_level}`: Draws a solid request arrow.
*   `\seqreturn{from_id}{to_id}{Label}{y_level}`: Draws a dashed response arrow.

**Example Sequence:**
```latex
\def\seqheight{6}
\seqactor{client}{Mobile App}{0}
\seqactor{server}{Backend API}{5}
\seqactivate{server}{1}{3}
\seqmessage{client}{server}{1. Authenticate}{1}
\seqreturn{server}{client}{2. JWT Token}{3}
```

## 4. UML Class Diagrams (`modern-uml-style.sty`)
Uses `shapes.multipart` to draw three-tier UML class boxes (Title, Fields, Methods).
Use `\nodepart{two}` for fields/variables and `\nodepart{three}` for methods/functions.

**Available Node Styles:**
*   `uml_class`: Standard blue class header.
*   `uml_interface`: Green interface header.
*   `uml_abstract`: Gray abstract class header.

**Available Relationship Arrows:**
*   `uml_inherit`: Solid line, empty triangle (Subclass to Superclass).
*   `uml_realize`: Dashed line, empty triangle (Class to Interface).
*   `uml_compose`: Solid line, filled diamond (Part to Whole).
*   `uml_aggregate`: Solid line, empty diamond (Part to Whole).
*   `uml_assoc`: Solid line, standard arrow (Directed Association).
*   `uml_depend`: Dashed line, standard arrow (Dependency).

**Example UML:**
```latex
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
\draw[uml_compose] (Order) -- node[above] {1..*} (Item);
```

## 5. Beamer Slides (`modern-slide-style.sty`)
Overrides Beamer defaults to provide a clean 16:9 widescreen experience.
You can embed C4, Sequence, or UML TikZ diagrams directly inside slides by loading their respective `.sty` files.

**Important Slide Constraints:**
*   Pass `[aspectratio=169]` to the `\documentclass`.
*   Wrap large diagrams in `\resizebox{0.8\textwidth}{!}{ ... }` so they fit on the slide.

**Example Slide:**
```latex
\documentclass[aspectratio=169]{beamer}
\usepackage{modern-slide-style}
\usepackage{modern-c4-style}

\begin{document}
\begin{frame}{Target Architecture}
    \centering
    \resizebox{0.8\textwidth}{!}{
        \begin{tikzpicture}[node distance=3cm, auto]
            \node[c4_system] (api) {API Gateway};
            \node[c4_database, right=of api] (db) {Database};
            \draw[c4_rel] (api) -- node {SQL} (db);
        \end{tikzpicture}
    }
\end{frame}
\end{document}
```