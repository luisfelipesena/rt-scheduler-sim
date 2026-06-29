# Build the Beamer slides. Requires latexmk + a TeX distribution.
.PHONY: all clean

all: main.pdf

main.pdf: main.tex beamerthemeDCC.sty
	latexmk -pdf -interaction=nonstopmode main.tex

clean:
	latexmk -C
	rm -f build.log install.log
