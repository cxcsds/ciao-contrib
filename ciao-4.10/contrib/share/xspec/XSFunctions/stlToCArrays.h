#ifndef STLTOCARRAYS_H
#define STLTOCARRAYS_H

#include <xsTypes.h>
#include <valarray>
#include <vector>
#include <cstring>

namespace XSFunctions
{
   template <typename T>
   void stlToFloatArrays(const RealArray& energy, const RealArray& params, 
              const RealArray& flux, const RealArray& fluxErr,  
              T*& cEng, T*& cPars, T*& cFlux, T*& cFluxErr); 

   template <typename T>
   void floatFluxToStl(const T* cFlux, const T* cFluxErr, const int nE, 
                const bool isErr, RealArray& flux, RealArray& fluxErr);              
}


template <typename T>
void XSFunctions::stlToFloatArrays(const RealArray& energy, const RealArray& params, 
              const RealArray& flux, const RealArray& fluxErr,  
              T*& cEng, T*& cPars, T*& cFlux, T*& cFluxErr)
{
   const size_t nBins = energy.size() - 1;
   const size_t nPars = params.size();

   const size_t nBinsp1 = nBins + 1;
   cEng = new T[nBinsp1];
   for (size_t i=0; i<nBinsp1; ++i)
      cEng[i] = energy[i];
   cPars = new T[nPars];
   for (size_t i=0; i<nPars; ++i)
      cPars[i] = params[i];

   cFlux = new T[nBins];
   if (flux.size())
   {
      for (size_t i=0; i<nBins; ++i)
         cFlux[i] = flux[i];
   }
   else
   {
      memset(cFlux, 0, nBins*sizeof(T));
   }
   cFluxErr = new T[nBins];
   if (fluxErr.size())
   {
      for (size_t i=0; i<nBins; ++i)
         cFluxErr[i] = fluxErr[i];
   }
   else
   {
      memset(cFluxErr, 0, nBins*sizeof(T));
   }
} 

template <typename T>
void XSFunctions::floatFluxToStl(const T* cFlux, const T* cFluxErr, const int nE, 
             const bool isErr, RealArray& flux, RealArray& fluxErr)
{
   flux.resize(nE);
   for (int i=0; i<nE; ++i)
      flux[i] = cFlux[i];
   if (isErr)
   {
      fluxErr.resize(nE);
      for (int i=0; i<nE; ++i)
         fluxErr[i] = cFluxErr[i];
   }
   else
      fluxErr.resize(0);
}            
#endif
