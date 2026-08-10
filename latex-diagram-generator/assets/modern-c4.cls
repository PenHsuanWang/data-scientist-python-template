\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{modern-c4}[2026/06/11 Modern Technical Document Class with C4 Support]

% --- Base Class Selection ---
% We use scrartcl (KOMA-Script) for modern European-style typography
\LoadClass[11pt, a4paper]{scrartcl}

% --- Custom Style Requirements ---
\RequirePackage{modern-c4-style}

% --- KOMA-Script Global Options ---
\KOMAoptions{
    parskip=half,      % Use space between paragraphs instead of indentation
    headings=normal,   % Better sizing for technical reports
    abstract=true      % Ensure abstract formatting is available
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
% Customize headings to use our DocText color and sans-serif font
\setkomafont{section}{\color{DocPrimary}\sffamily\bfseries\Large}
\setkomafont{subsection}{\color{DocText}\sffamily\bfseries\large}
\setkomafont{subsubsection}{\color{DocText}\sffamily\bfseries\normalsize}

\endinput
