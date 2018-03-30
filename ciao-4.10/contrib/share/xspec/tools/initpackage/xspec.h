
c  Include file for XSPEC internal parameters




c Common block for dynamic memory using udmget

      LOGICAL          MEMB(1)
      INTEGER*2        MEMS(1)
      INTEGER*4        MEMI(1)
      INTEGER*4        MEML(1)
      REAL             MEMR(1)
      DOUBLE PRECISION MEMD(1)
      COMPLEX          MEMX(1)
      CHARACTER(1)     MEMC(1)
      EQUIVALENCE (MEMB, MEMS, MEMI, MEML, MEMR, MEMD, MEMX, MEMC)
      COMMON /MEM/ MEMD
