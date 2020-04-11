AC_INIT([bogus], [1.0])
AM_INIT_AUTOMAKE([foreign dist-bzip2 no-define])
AM_SILENT_RULES([yes])

dnl Intentionally not putting an AC HELP_STRING here so that this option
dnl does not show up in "./configure --help" output.
AC_ARG_ENABLE([dist])

OMPI_TOP_BUILDDIR="`pwd`"
AC_SUBST(OMPI_TOP_BUILDDIR)
cd "$srcdir"
OMPI_TOP_SRCDIR="`pwd`"
AC_SUBST(OMPI_TOP_SRCDIR)
cd "$OMPI_TOP_BUILDDIR"

AC_PATH_PROG([PANDOC], [pandoc])
AS_IF([test -z "$PANDOC"],
      [AS_IF([test "$enable_dist" = "yes"],
             [AC_MSG_WARN([You selected --enable-dist, but pandoc cannot be found])
              AC_MSG_ERROR([Cannot continue])],
             [PANDOC="$OMPI_TOP_SRCDIR/scripts/fake_pandoc.sh"])])

AC_CONFIG_FILES([Makefile man/Makefile])
AC_OUTPUT
