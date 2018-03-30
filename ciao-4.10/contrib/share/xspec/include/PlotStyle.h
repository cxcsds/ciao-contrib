//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTSTYLE_H
#define PLOTSTYLE_H 1

namespace PlotStyle {



    typedef enum{NONE, SOLID, DASH, DASHDOT, DOTTED, DASHDOTDOTDOT} LineStyle;



    typedef enum {BLANK,DOT,CROSS,ASTERISK,CIRCLE,XCROSS,SQUARE,TRIANGLE,EARTH,SUN,CURVESQUARE,DIAMOND,STAR,FILLEDTRIANGLE,OPENCROSS,HEXAGRAM,FILLED_SQUARE,FILLED_CIRCLE,FILLED_STAR} Symbol;



    typedef enum {BLACK,WHITE,RED,GREEN,BLUE,LIGHTBLUE,MAGENTA,YELLOW,ORANGE,YELLOW_GREEN,GREEN_CYAN,BLUE_CYAN,BLUE_MAGENTA,RED_MAGENTA,DARK_GREY,LIGHT_GREY} Colour;



    typedef enum {DATA,BACKGROUND,MODEL,SOURCES} VectorCategory;



    typedef enum {LOG,LINEAR} ScaleType;



    typedef enum {XMIN=8, XMAX=4, YMIN=2, YMAX=1} RangeFlags;

} // namespace PlotStyle


#endif
