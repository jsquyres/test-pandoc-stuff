# Makefile

MD3_FILES = \
	MPI_Init.3.md \
	MPI_Finalize.3.md

MD7_FILES = \
	fabric.7.md

man_MANS = $(MD3_FILES:.3.md=.3) $(MD7_FILES:.7.md=.7)

EXTRA_DIST = $(MD3_FILES) $(MD7_FILES) $(man_MANS)

MD2NROFF = $(top_srcdir)/scripts/md2nroff.py

%.3: %.3.md
	$(MD2NROFF) --source=$? --dest=$@ --pandoc=$(PANDOC)

%.7: %.7.md
	$(MD2NROFF) --source=$? --dest=$@ --pandoc=$(PANDOC)

jeff:
	rm $(man_MANS)
