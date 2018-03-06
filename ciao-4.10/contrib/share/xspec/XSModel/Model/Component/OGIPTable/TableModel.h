#ifndef TABLEMODEL_H
#define TABLEMODEL_H 1

#include <xsTypes.h>

// Functions to provide access to XSPEC's internal table model
// interpolation routines from users' local models.

void additiveTable(const RealArray&, const RealArray&, string, int, RealArray&, 
		   RealArray&, const string&);
void exponentialTable(const RealArray&, const RealArray&, string, int, RealArray&, 
		   RealArray&, const string&);
void multiplicativeTable(const RealArray&, const RealArray&, string, int, RealArray&, 
		   RealArray&, const string&);

extern "C" void xsatbl(float* ear, int ne, float* param, const char* filenm, int ifl, 
                float* photar, float* photer);
extern "C" void xsetbl(float* ear, int ne, float* param, const char* filenm, int ifl, 
                float* photar, float* photer);
extern "C" void xsmtbl(float* ear, int ne, float* param, const char* filenm, int ifl, 
                float* photar, float* photer);
                

#endif
