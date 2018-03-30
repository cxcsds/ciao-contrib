/* Add a definition of isfinite() if it is not already defined in
 * in math.h, as in GCC 4.1.x, 4.2.x.  This is also an issue for
 * "isnormal", so future development may necessitate inclusion of
 * a homegrown definition of that here too.
 */

#ifndef headas_hd_math_compat_h
#define headas_hd_math_compat_h

#ifdef __cplusplus
#include <cmath>
#else
#include <math.h>
#endif

#ifndef isfinite
#define isfinite(x) ((x) * 0 == 0)
#endif

#endif
