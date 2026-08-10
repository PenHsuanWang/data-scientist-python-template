---
name: latex-diagram-generator
description: Generate architectural diagrams (C4, Sequence, UML) and presentation slides using the custom LaTeX framework. Use this skill when asked to create or draw software architecture diagrams, design document visuals, or Beamer presentations.
---

# LaTeX Diagram Generator

This skill enables the generation of modern, version-controllable architectural diagrams and presentation slides using the project's custom LaTeX framework.

## 1. Preparation

Before writing any LaTeX code, review the syntax rules, available macros, node styles, and code examples found in [diagram-templates.md](references/diagram-templates.md). 

## 2. Generating the Diagram

1. Create a new `.tex` file in the appropriate directory (e.g., `design-doc/latex/` or where requested by the user).
2. Ensure the required `.cls` and `.sty` files are present in the same directory as your `.tex` file. If they are missing from the project, you can find them in this skill's `assets/` directory and copy them to the target location.
3. For standalone diagrams, always use the `standalone` document class with a margin.
4. Import the required style package:
   - C4 Diagrams: `\usepackage{modern-c4-style}`
   - Sequence Diagrams: `\usepackage{modern-seq-style}`
   - UML Diagrams: `\usepackage{modern-uml-style}`
   - Presentation Slides: `\usepackage{modern-slide-style}`
5. Write the TikZ or Beamer code according to the templates in the reference guide.

## 3. Compilation

1. Always compile the `.tex` document using `pdflatex` via the `run_shell_command` tool.
2. Run the command from the directory containing the `.tex` file to ensure the `.sty` and `.cls` files can be resolved (e.g., `cd design-doc/latex && pdflatex -interaction=nonstopmode your_document.tex`).
3. If the document includes complex references, run the compilation command twice.
4. Verify the output (a `.pdf` file will be generated).
