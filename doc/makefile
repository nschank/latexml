BUILD=pdflatex
TARGET=documentation

all: *.tex
	@ $(BUILD) $(TARGET).tex
	@ rm -rf *.log *.aux
	
clean:
	rm -rf *.log *.aux *.pdf
	