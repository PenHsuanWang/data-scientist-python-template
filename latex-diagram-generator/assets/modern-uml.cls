\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{modern-uml}[2026/06/11 Modern UML Diagram Class]

% --- Base Class Selection ---
\LoadClass[11pt, a4paper]{scrartcl}

% --- Custom Style Requirements ---
\RequirePackage{modern-uml-style}

% --- KOMA-Script Global Options ---
\KOMAoptions{
    parskip=half,      
    headings=normal,   
    abstract=true      
}

% --- Page Layout ---
\RequirePackage[margin=2.5cm]{geometry}
\RequirePackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=DocPrimary,
    filecolor=DocPrimary,
    urlcolor=DocPrimary,
    citecolor=DocPrimary,
}

% --- Section Styling ---
\setkomafont{section}{\color{DocPrimary}\sffamily\bfseries\Large}
\setkomafont{subsection}{\color{DocText}\sffamily\bfseries\large}
\setkomafont{subsubsection}{\color{DocText}\sffamily\bfseries\normalsize}

\endinput
