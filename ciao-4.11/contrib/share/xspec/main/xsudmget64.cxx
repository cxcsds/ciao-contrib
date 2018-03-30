/* Dynamic memory like iraf does it for fortran */
/* $Id$

   Explanatory comments added July 1999 Ben Dorman indicated  by BD 7/99

   $Log$
   Revision 1.3  2011/01/13 23:13:52  gordon
   For ALL *.cxx and *.h files in the Xspec/src tree:

   Removed all lines which began with the Rational Rose meta-data
   comment specifier "//##".  Rose hasn't been available for use
   since 03/10, so these were no longer needed.

   This was performed with my removeRose program, which isn't
   smart enough to remove Rose comments which start in the middle
   of a line rather than at the beginning.  But these are a tiny
   fraction of all the comments, and are found only in the *.h
   files.

   Revision 1.2  2010/01/25 20:30:23  irby
   With x86_64 defined on newer Mac hardware, the mallopt call was getting
   hit (shouldn't be on Macs), so it's been ifdef'd out.

   Revision 1.1  2009/03/12 18:21:48  gordon
   New (and perhaps final) resting place for xspec.h xsudmget.cxx.
   These used to be in src/include and src/XSFunctions respectively,
   but were no longer needed there after udmget removals. They
   will remain here in case users wish to grab them for their local
   model builds.

   Revision 1.10  2008/07/18 13:44:10  gordon
   Went back to old C-style headers for stdlib.h, stdio.h, and string.h.
   Otherwise Solaris requires declaring the std namespace, and it's
   not worth diverging further from the xanlib udmget.

   Revision 1.9  2008/07/17 20:55:39  gordon
   Now using udm_malloc, udm_free, and udm_realloc wrapper functions,
   provided by Jeremy Sanders.  These are intended for 64-bit
   platforms to ensure lower 32-bit addressing.  On Fedora Core 8 the
   earlier mallopt fix did not always guarantee this.

   Revision 1.8  2008/07/10 19:59:21  gordon
   Obscure bug fix made to find_used function - added check of elsize in 
   addition to the retval test.  Other modifications: removed the unsigned 
   qualifier for the elsize and size types in udmget_.  Also made some minor 
   changes to bring this closer to xanlib's udmget.

   Revision 1.7  2005/06/20 20:21:06  gordon
   Modified test to determine if *pointer has been previously allocated, by
   replacing *pointer > 0 condition with *pointer != 0.  This is what xanlib
   version does and the end result is far fewer calls to find_free function,
   which makes it less likely MAXBLK limit will be reached.

   Revision 1.6  2005/06/07 13:26:33  gordon
   Increased MAXBLK from 100 to 1000.

   Revision 1.5  2005/05/10 19:00:19  gordon
   Minor syntax fix: needed to remove parentheses in an #ifndef statement.

   Revision 1.4  2005/04/21 16:54:05  irby
   Sync with xanlib/memory/udmget.c #2:
     Fix from Keith Arnaud to improve diagnostics generated when guard memory is
     corrupted:  Changed udmget to make the output more consistent and removed
     the abort() in favor of returning an error.  Status is 0 for ok, 100 for
     invalid type, 101 for error allocating memory, and 102 for a detected change
     in the guard elements.

   Revision 1.3  2005/04/21 16:30:41  irby
   Sync with xanlib/memory/udmget.c #1:
     Use mallopt for x86_64 platform (in addition to the alphas) to keep
     malloc'd memory in lower 31-bit addresses.

   Revision 1.2  2003/12/19 16:26:52  irby
   Define MEM for Darwin, and do not include malloc.h there.

   Revision 1.1.1.1  2003/11/25 22:45:47  dorman
   Xspec12.0 Export Version 11-25-2003

   Revision 9.1  2003/02/04 20:20:35  dorman


   minor changes to local model codes to allow compilation.

   add gamma.cxx to provide simple wrappers for fortran programmers to
   access C++ code for gamma functions.

   change call for udmget back from xsudmget to allow for backward compatibility.

   Revision 9.0  2003/01/27 17:32:26  dorman

   repository version number change
   completion of check in for new files supporting function definition scheme.

   Revision 8.0  2002/11/27 14:48:51  dorman

   Update version number

   Revision 7.0  2002/07/12 16:06:39  dorman

   version number change

   Revision 6.0  2002/03/27 21:38:21  dorman



   version number change

   Revision 3.0  2001/04/05 21:47:52  dorman



   Version number change.

   Revision 1.1.1.1  2001/04/05 20:58:59  dorman
   XSPEC12 revised registry

   Revision 2.0  2001/01/23 18:39:10  dorman
   *** empty log message ***

   Revision 1.2  1999/10/04 18:48:17  dorman
   Add xsftop (xspec subroutine to open FITS files).

   Revision 1.1  1999/09/24 15:30:57  dorman
   Add xspec function directory to C++ development code.

   udmget has been protoized and one static_cast operator
   was required to satisfy the C++ compiler. This could also be done
   with a C-style cast (allowing this version to compile under C), but I
   chose to keep to the C++ way of doing things.

   Revision 1.2  1999/08/19 15:04:57  dorman
   Add explicit cast for GUARD definition in two additional places
   to avoid compiler warning.

   Revision 1.1  1999/08/19 14:44:47  dorman
   move udmget dynamic memory allocation in functions library to a new
   function internal to the library.

   Building of this code has been tested (to date) under solaris, with
   correct functioning tested by creating a model that uses virtual memory
   (ascac).

   Revision 1.7  1999/07/22 17:59:27  dorman
   No code changes: clarifying comments added to demystify udmget's
   deep black magic.

   Revision 1.6  1998/07/14 18:57:20  peachey
   Cygwin port

 * Revision 1.5  1998/06/30  16:35:57  miket
 * MMAP hack peformed for Linux/Alpha only to keep malloc to lower 31-bit addrs
 *
   Revision 1.4  1998/04/24 18:57:52  peachey
   Two changes:
   1) benign: change diagnostic printfs to use %lx instead of %x, to handle
      long addresses
   2) very scary: change the calculation of the "pointer" variable, i.e.,
      the index which is passed back to the calling Fortran program. The
      purpose for the change is to make sure that a valid, *signed*
      Fortran integer is passed back; under some circumstances, a positive
      2s-complement was being returned instead, causing seg-faults.

   Revision 1.3  1997/02/12 17:01:15  dah
   Do previously described fix the RIGHT way.

 * Revision 1.2  1997/02/12  14:12:32  dah
 * Fix bug which caused miscalulation of pointer value when allocating
 * double precision space.  If difference between MEM and the allocated
 * pointer was not an integer multiple of 8, then guard values were being
 * written outside the allocated space.
 * CVS:----------------------------------------------------------------------
 * CVS:----------------------------------------------------------------------
 *
 * Revision 1.1  1996/12/24  19:37:49  dunfee
 * Moved from host to xanlib/memory.... of the way we were...
 *
   Revision 3.10  1996/11/19 15:03:55  dah
   Add support for character type variables (type 2).  Fix a couple of error
   messages.

   Revision 1.5  1996/11/05 19:46:23  dah
   Tie up loose ends in dynamic mem.

   Revision 1.4  1996/10/11 17:00:12  dah
   Add missing carriage returns after a couple of error messages.

   Revision 1.3  1996/09/04 20:59:32  dah
   Better error messages.

 * Revision 3.8  1996/08/05  13:54:37  oneel
 * fix Id
 *
 * Revision 3.7  1996/08/05  13:53:26  oneel
 * From Dean Hinshaw:
 *
 * 8/2/96 dah -- Fix bugs in size calculation and guard filling/checking
 *
 * This should remove the "devil's numbers" problem
 *
 * Revision 3.6  1996/07/11  15:53:41  miket
 * MJT 11July96 g77/linux-related changes
 *
   Revision 3.5.1.1  1996/04/16 01:41:15  dunfee
   Start of pristine ftools CVS...

 * Revision 1.4  1995/12/19  19:03:32  oneel
 * Released new udmget.c
 *
 * Revision 1.3  1995/12/19  12:04:16  oneel
 * Max was wrong
 *
 * Revision 1.2  1995/12/18  20:28:47  oneel
 * Made sure that nelem in the umdget call was at least 100.
 *
 * Revision 1.1  1995/12/18  20:24:49  oneel
 * Initial revision
 *

 */
/* 3/10/94 -- logical was sized at 1, made sure it's size was 4 */
/* 3/11/94 -- Fix problem with first element of the array       */
/* 3/14/94 -- Add guard areas                                   */

/* 8/2/96 dah -- Fix bugs in size calculation and guard filling/checking */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
/* 
*  compiler dependent C/fortran definition of fortran variable names as seen by C 
*  BD 7/99
*/
/* 30Jun98 MJT -- need to use mallopt() (see below) */
#if ( (defined(__alpha) || defined(__x86_64__)) && defined(g77Fortran))
#ifndef __APPLE__
#include <malloc.h>
#endif
#endif

#ifdef __APPLE__
#define MEM mem_
#endif

#ifdef m88k
#define MEM mem__
#endif

#ifdef __hpux
#define MEM mem_
#endif

#ifdef linux
#define MEM mem_
#endif


#ifdef sun
#define MEM mem_
#endif

#ifdef NeXT
#define MEM mem
#endif

#ifdef ultrix
#define MEM mem_
#endif

#ifdef __osf__
#define MEM mem_
#endif

#ifdef __sgi
#define MEM mem_
#endif

#ifdef VMS
#define MEM mem
#endif

#ifdef __CYGWIN32__
#define MEM mem_
#endif

/* number of distinct memory blocks that can be allocated. */

#define MAXBLK 1000

#ifdef __cplusplus
extern "C" {
#endif

typedef long udm_int_8;
typedef unsigned long udm_uint_8;

int udmget_ (int* nelem,int* datatype,udm_int_8* pointer,int* status);

int udmfre_ (udm_int_8* pointer, int* datatype,int* status);

#ifdef __cplusplus
}
#endif

static int find_free ();
static int find_used (udm_int_8 retval,int elsize);
static int dysize(int intype);
static int fill_guard (udm_int_8 pointer,int elsize,int nelem);

/*
*   ptr - a pointer for each individual memory block. typed to char (1 byte)
*   retval - the  address of the block, expressed as an offset from the base pointer MEM
*   nelem - the number of array elements in an individual block
*   elsize - the size of each element in an individual block
*
*   in the code, the individual blocks are indexed by i.
*   BD 7/99
*/

static struct
{
  char * ptr;
  udm_int_8 retval;
  int nelem;
  int elsize;
} blocks [MAXBLK] = {NULL,0}; 


/* GUARD is a filler value used to test whether the memory is uncorrupted from its
*  earlier allocation by a previous call to udmget BD 7/99
*
*/

#define GUARD 0x96


/* Sample fortran program....

C  Example fortran protram that uses dynamic memory arrays

C  the following MEM common block definition is in the system iraf77.inc file
C
C Get IRAF MEM common into main program.
C
      LOGICAL          MEMB(1)
      INTEGER*2        MEMS(1)
      INTEGER*4        MEMI(1)
      INTEGER*4        MEML(1)
      REAL             MEMR(1)
      DOUBLE PRECISION MEMD(1)
      COMPLEX          MEMX(1)
      EQUIVALENCE (MEMB, MEMS, MEMI, MEML, MEMR, MEMD, MEMX)
      COMMON /MEM/ MEMD

      integer nelem, datatype, pointer, status

C     nelem specifies the number of data values required to be held in memory
      nelem = 1000000

C     datatype gives a symbolic code for the data type, e.g.,  4 = Integer*4
C     1 is boolean
C     2 is character
C     3 is short integer
C     4 is integer
C     5 is long integer
C     6 is single precision real
C     7 is double precision real
C     8 complex
      datatype = 4

C     get space for 'nelem' number of elements of data type 'datatype':
C        udmget returns a pointer to the first element in the MEMx array
C        that is the start of the allocated memeory.

C Status is 0 for ok, 100 for invalid type, 101 for error allocating memory,
C and 102 for a detected change in the guard elements
      call udmget (nelem, datatype, pointer, status)

C     now pass the array, and its size to a subroutine that needs it
      call work ( nelem, memi(pointer))
      call work1 ( nelem, memi(pointer))

C     release the memory that was allocated with udmget
      call udmfre ( pointer, datatype, status)

      end

C-----------------------------------------------------------

      subroutine work( nelem, array)

      integer nelem
      integer array(nelelm)
      integer i


      do i=1,nelem
         array(i) = nelem-i+1
      end do


      return
      end


      subroutine work1( nelem, array)

      integer nelem
      integer array(nelelm)
      integer i


      do i=1,nelem
         if (array(i) .ne. nelem-i+1) then
            print *,'error at ',i,array(i),nelem-i+1
         end if
      end do


      return
      end


*/


int dysize(int intype)
{
  /* Converts type to size */
  /* each code 1-8 returns value corresponding to the byte size of the data type  BD 7/99 */
  switch (intype)
    {
    case 1 :
      return 4;  /* logical */
    case 2 :
      return 1;  /* character */
    case 3 :
      return 2;  /* integer*2 */
    case 4 :
      return 4;  /* integer*4 */
    case 5 :
      return 8;  /* integer*8 */
    case 6 :
      return 4;  /* real*4 */
    case 7 :
      return 8;  /* real*8 */
    case 8 :
      return 8;  /* complex */
    default : 
      return -1;
    }
}

extern int MEM; /* this is the name of the common block you need to declare  in fortran */

#if ( (defined(__alpha) || defined(__x86_64__)) && defined(__GNU_LIBRARY__))
#include <sys/mman.h>
#endif
static void* udm_malloc(size_t size)
{
#if ( (defined(__alpha) || defined(__x86_64__)) && defined(__GNU_LIBRARY__))
  /* works by use mmap to allocate memory in an anonymous map,
     storing the size of the allocated memory in the first sizeof(size_t)
     bytes */

  void* ptr;

  /* mmap is readable and writable, but not executable */
  ptr = mmap(NULL, size + sizeof(size_t), PROT_READ | PROT_WRITE,
	     MAP_PRIVATE | MAP_32BIT | MAP_ANONYMOUS,
	     -1, 0);

#ifdef DEBUG
  fprintf(stderr, "UDM_MALLOC: %p (%zi size)\n", ptr, size);
#endif

  /* could not allocate memory */
  if( ptr == MAP_FAILED )
    {
      return 0;
    }

  /* store size at start of block */
  *(size_t*) ptr = size + sizeof(size_t);

  /* return address beyond size measurement */
  return static_cast<void*>(static_cast<char*>(ptr) + sizeof(size_t));
#else
  return malloc(size);
#endif
}

static void udm_free(void* ptr)
{
#if ( (defined(__alpha) || defined(__x86_64__)) && defined(__GNU_LIBRARY__))
#ifdef DEBUG
  fprintf(stderr, "UDM_FREE: %p\n", ptr);
#endif
  if( ptr != 0 )
    {
      void* sizep = static_cast<void*>(static_cast<char*>(ptr) -
				       sizeof(size_t));
      /* use stored size to deallocate mmap */
      munmap(sizep, *static_cast<size_t*>(sizep));
    }
#else
  free(ptr);
#endif
}

static void* udm_realloc(void* ptr, size_t size)
{
#if ( (defined(__alpha) || defined(__x86_64__)) && defined(__GNU_LIBRARY__))
  /* ugly copy of data to new data block */

  void* newptr = udm_malloc(size);

#ifdef DEBUG
  fprintf(stderr, "UDM_REALLOC: %p->%p (%zi size)\n", ptr, newptr, size);
#endif

  if( ptr != 0 && newptr != 0 )
    {
      size_t oldsize = *static_cast<size_t*>(static_cast<void*>(static_cast<char*>(ptr) -
								sizeof(size_t))) - sizeof(size_t);

#ifdef DEBUG
      fprintf(stderr, "UDM_REALLOC: old size is %zi\n", oldsize);
#endif

      memcpy( static_cast<char*>(newptr),
	      static_cast<char*>(ptr),
	      size<oldsize ? size : oldsize );
      udm_free(ptr);
    }

  return newptr;
#else
  return realloc(ptr, size);
#endif
}

static int check_guard (udm_int_8 pointer,int elsize,int nelem)
{
  char *p;
  int i;

  /* location of guard elements for array given by pointer BD 7/99 */

  /* MEM-----------------------|p */
  /*     elsize*(pointer-1)       */

  p = (char *)&MEM + (elsize*((udm_uint_8)pointer-1));
  /*
  *   check  locations indicated by '+++' for guard value. return 2 if different (corrupted)
                                                                         (nelem+1)
                                                                            *
             elsize   elsize         [nelem*elsize]              elsize    elsize
           |-------||-------|p|................................||-------||-------||  
            +++++++                         blocks                        +++++++
  * BD 7/99
  */
  for (i=elsize;i<2*elsize;i++)
    {
#ifdef DEBUG
      printf ("Check_guard: outer buffer, %d\n",i);
      printf ("Checking %lx\n",p-i-1);
#endif
      if (*(p-i-1) != (char) GUARD) return -2;
#ifdef DEBUG
      printf ("Checking %lx\n",p+nelem*elsize+i);
#endif
      if (*(p+nelem*elsize+i) != (char) GUARD) return 2;

    }
  /*  
  * check for guard value in inner block and element beyond last element. BD 7/99
                                                                  nelem
                                                                   *
             elsize   elsize        [nelem*elsize]                elsize
           |-------||-------|p|................................||-------||-------||  
                     +++++++             blocks                 +++++++
  */

  for (i=0;i<elsize;i++)
    {
#ifdef DEBUG
      printf ("Check_guard: inner buffer, %d\n",i);
      printf ("Checking %lx\n",p-i-1);
#endif
      if (*(p-i-1) != (char) GUARD) return -1;
#ifdef DEBUG
      printf ("Checking %lx\n",p+nelem*elsize+i);
#endif
      if (*(p+nelem*elsize+i) != (char) GUARD) return 1;
    }

  return 0;

}

static int find_free ()
{
  int i;
/*
*  Check through the pointer list, find if there is one which has not been allocated,
*  and return its index. If all are allocated, return -1. BD7/99
*
*/  

  for (i=0;i<MAXBLK;i++)
    {
      if (!blocks[i].ptr) return i;
    }

  return -1;

}

static int find_used (udm_int_8 retval, int elsize)
{
  int i;

  /*
  *   find the block index for the input value retval.  BD 7/99
  *   return -1 if the pointer value doesn't match any of the blocks.
  */

  /*  Note that it's possible (though unlikely) that multiple blocks may in
  *   fact share the same retval if they contain data types with different
  *   sizes.  However for blocks within each category of elsize, retval must 
  *   be unique.  CG 7/08
  */
  for (i=0;i<MAXBLK;i++)
    {
      if (retval == blocks[i].retval && elsize == blocks[i].elsize) 
        return i;
    }

  return -1;

}

int fill_guard (udm_int_8 pointer,int elsize,int nelem)
{
  char *p;
  int i;
  /* fill the memory area to be used with guard value. 
  *  this address calculation simply unwinds the transformation into an offset
  *  made by udmget (below) in storing the information about this array 
  *  BD 7/99
  */
  p = (char *)&MEM + (elsize*((udm_uint_8)pointer-1));  
  /*
  *   fill  locations indicated by '+++' with guard value. 
  *                                                                       nelem   (nelem+1)
  *                                                                         *        *
  *                  elsize   elsize         [(nelem-2)*elsize]          elsize    elsize
  *                p|-------||-------||................................||-------||-------||  
  *                  +++++++  +++++++               blocks               +++++++  +++++++
  * BD 7/99
  */


  for (i=0;i<2*elsize;i++)
    {
#ifdef DEBUG
      printf ("Setting %lx\n",p-i-1);
#endif
      *(p-i-1) = (char )GUARD;
#ifdef DEBUG
      printf ("Setting %lx\n",p+nelem*elsize+i);
#endif
      *(p+nelem*elsize+i) = (char )GUARD;
    }
  return 0;

}


int udmget_ (int* nelem,int* datatype,udm_int_8* pointer,int* status)
{

  int size, elsize;
  char *p;
  int j, i=0;
  int *tnelem;
  int tanelem;

  tnelem = &tanelem;

  *tnelem = *nelem;

  *status = 0;

  /* return size of input datatype. */

  if (-1 == (size = dysize(*datatype))) 
    {
      *status = 100;
      return 0;
    }
#ifdef DEBUG
  printf ("Size is %d\n",size); 
#endif

  elsize = size;


  /* Add 6. 2 guard elements at each end, and 2 to make sure we end up on a 
     "whatever" boundary */

  size *= (*tnelem + 6);

  /* if this has been previously allocated, find it, and then check it for intact
     guard values  BD 7/99*/

  if( *pointer != 0 && (i=find_used(*pointer,elsize)) != -1 ){

    j = check_guard(*pointer,elsize,blocks[i].nelem);
#ifdef DEBUG
    printf ("check_guard return %d\n",j);
#endif
    if (j == -1){
      fprintf (stderr,"** Memory Alloc Verification Warning: Lower, inner guard element modified\n");
    }
    else if (j == 1){
      fprintf (stderr,"** Memory Alloc Verification Warning: Upper, inner guard element modified\n");
    }
    else if (j == -2){
      fprintf (stderr,"** Memory Alloc Verification Warning: Lower, outer guard element modified\n");
    }
    else if (j == 2){
      fprintf (stderr,"** Memory Alloc Verification Warning: Upper, outer guard element modified\n");
    }
    if (abs(j) == 1 || abs(j) == 2){
      fprintf (stderr,"** %d %d %d %d\n", *pointer, elsize, blocks[i].nelem, j);
      fflush (stderr);

      *status = 102;
      return 0;
    }

    /* reallocate memory and return pointer to new location. BD 7/99*/
#ifdef DEBUG
    printf ("Reallocing size %d\n",size); 
#endif

    p = static_cast<char*>(udm_realloc( blocks[i].ptr, size ));

    if (p == NULL)
      {
	fprintf (stderr,"Memory Allocation Error: Realloc failed\n");
	fflush (stderr);
	*status = 101;
	return 0;
      }

  }else{

    /* if no memory has been allocated for the pointer  allocate a new memory block  BD 7/99 */
#ifdef DEBUG
    if( i == -1 ) printf("Invalid pointer. Cannot realloc.\n");
    printf ("Mallocing size %d\n",size); 
#endif

/* 30Jun98 MJT keep malloc'd memory in lower 31-bit addresses*/
#ifndef __APPLE__
#if ( (defined(__alpha) || defined(__x86_64__)) && defined(g77Fortran))
    mallopt(M_MMAP_MAX, 0);
#ifdef DEBUG
    printf("MMAP hack performed\n");
#endif
#endif
#endif

    p = (char *)udm_malloc(size);

    if (p == NULL)
      {
	fprintf (stderr,"Memory Allocation Error: Malloc failed\n");
	fflush (stderr);
	*status = 101;
	return 0;
      }

    /* find a free index in the block array to store the information for this array BD 7/99 */  

    i = find_free();
    if (i == -1){
	fprintf (stderr,"Memory Allocation Error: Too many blocks\n");
	fflush (stderr);
	udm_free(p);

	*status = 101;
	return 0;
    }

  }

#ifdef DEBUG
  printf ("&mem %lx p %lx\n",&MEM,p); 
#endif

/* jp 10 apr 1998: handle negative offsets, avoiding overflow, by
   doing unsigned arithmetic, then adding the - sign explicitly if needed.
   warning: in the case of character arrays, this may still not work
   properly, because elsize is 1, and pointer is a signed integer. */

   /* compute memory offset value */

  if(p > (char *) &MEM) {
    *pointer = ((unsigned long) p - (unsigned long) &MEM)
                        /(unsigned long)elsize;
  } else {
    *pointer = - (((unsigned long) &MEM - (unsigned long) p)
                        /(unsigned long)elsize);
  }
  /*
  * This is the forward transformation from absolute address to integer offset,
  * which is reversed in check_guard & fill_guard (for example).
  *  'pointer' appears as a pointer (i.e. an address in those functions, with the 
  * transformation:
  *   p = MEM + pointer(elsize-1)
  *
  * (i.e. pointer ?= (p - MEM)/elsize + 1
  *
  *   However, here its deferenced value *pointer is being manipulated. As pointer is 
  *   there an int-masquerading-as-a-pointer, the pointer's movement by 1 there translates
  *   to movement by 4 here.
  *     
  *     BD/JP 7/99.  
  */
  *pointer += 4;
  fill_guard (*pointer,elsize,*tnelem);
  j = check_guard(*pointer,elsize,*tnelem);
#ifdef DEBUG
  printf ("check_guard return %d\n",j);
#endif

    if (j == -1){
      fprintf (stderr,"** Memory Alloc Verification Warning: Lower, inner guard element modified\n");
    }
    else if (j == 1){
      fprintf (stderr,"** Memory Alloc Verification Warning: Upper, inner guard element modified\n");
    }
    else if (j == -2){
      fprintf (stderr,"** Memory Alloc Verification Warning: Lower, outer guard element modified\n");
    }
    else if (j == 2){
      fprintf (stderr,"** Memory Alloc Verification Warning: Upper, outer guard element modified\n");
    }
    if (abs(j) == 1 || abs(j) == 2){
      fprintf (stderr,"** %d %d %d %d\n", *pointer, elsize, blocks[i].nelem, j);
      fflush (stderr);

      *status = 102;
      return 0;
    }

  blocks[i].ptr = p;
  blocks[i].retval = *pointer;
  blocks[i].nelem = *tnelem;
  blocks[i].elsize = elsize;
#ifdef DEBUG
  printf ("Saved at %d\n",i);
#endif

  return 0;
}



int udmfre_ (udm_int_8* pointer, int* datatype,int* status)
{
  char *p;
  int size;
  int i;
  int j;
  int elsize;
  int nelem;

  *status = 0;

  if (-1 == (size = dysize(*datatype))) 
    {
      *status = 100;
      return 0;
    }

  i = find_used(*pointer,size);
#ifdef DEBUG
  printf ("find_used returned %d for %d\n",i,*pointer);
#endif
  if (i == -1 || blocks[i].ptr == 0)
    {
      fprintf (stderr,"Memory Allocation Error: Invalid pointer, can't free memory\n");
      fflush (stderr);
      *status = 101;
      return 0;
    }
  elsize = blocks[i].elsize;
  nelem = blocks[i].nelem;

  j = check_guard(*pointer,elsize,nelem);
#ifdef DEBUG
  printf ("Check_guard returned %d\n",j);
#endif

    if (j == -1){
      fprintf (stderr,"** Memory Alloc Verification Warning: Lower, inner guard element modified\n");
    }
    else if (j == 1){
      fprintf (stderr,"** Memory Alloc Verification Warning: Upper, inner guard element modified\n");
    }
    else if (j == -2){
      fprintf (stderr,"** Memory Alloc Verification Warning: Lower, outer guard element modified\n");
    }
    else if (j == 2){
      fprintf (stderr,"** Memory Alloc Verification Warning: Upper, outer guard element modified\n");
    }
    if (abs(j) == 1 || abs(j) == 2){
      fprintf (stderr,"** %d %d %d %d\n", *pointer, elsize, blocks[i].nelem, j);
      fflush (stderr);

      *status = 102;
      return 0;
    }

  p = blocks[i].ptr;
  udm_free (p);

  blocks[i].ptr = 0;
  blocks[i].retval = 0;
  *pointer = -1;

  return 0;
}
