//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%
//	Component List Types typedef file, encapsulating
//	definitions for Component List implementation and its
//	iterators.

#ifndef COMPONENTLISTTYPES_H
#define COMPONENTLISTTYPES_H 1

// list
#include <list>

class Component;




typedef std::list<Component*> ComponentList;



typedef ComponentList::iterator ComponentListIterator;



typedef ComponentList::const_iterator ComponentListConstIterator;


#endif
