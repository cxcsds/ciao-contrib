// Convolving a model with a kernel. Uses a kernel function pointer as a template
// parameter for efficiency. Uses fftw to do the convolution.


#ifndef CONVOLUTION_H
#define CONVOLUTION_H

#include <xsTypes.h>
#include <XSUtil/Numerics/LinearInterp.h>
#include <XSUtil/Numerics/BinarySearch.h>
#include <fftw/fftw3.h>
#include <iostream>
#include <limits>

namespace Numerics {

  template<void KernelFunction(const RealArray& kernelEnergyArray, const RealArray& kernelParams, int spectrumNumber, RealArray& kernelFlux, RealArray& kernelFluxErr, const string& kernelInitString)>
    void Convolution(const RealArray& energyArray, const RealArray& kernelParams, const Real kernelFiducialEnergy, const int spectrumNumber, const string& kernelInitString, RealArray& fluxArray, RealArray& fluxErrArray);


  template<void KernelFunction(const RealArray& kernelEnergyArray, const RealArray& kernelParams, int spectrumNumber, RealArray& kernelFlux, RealArray& kernelFluxErr, const string& kernelInitString)>
    void ConvolutionInLnSpace(const RealArray& energyArray, const RealArray& kernelParams, const Real kernelFiducialEnergy, const int spectrumNumber, const string& kernelInitString, RealArray& fluxArray, RealArray& fluxErrArray);


  // The Convolution method is for a KernelFunction which is constant in energy

  template<void KernelFunction(const RealArray& kernelEnergyArray, const RealArray& kernelParams, int spectrumNumber, RealArray& kernelFlux, RealArray& kernelFluxErr, const string& kernelInitString)>
    void Convolution(const RealArray& energyArray, const RealArray& kernelParams, const Real kernelFiducialEnergy, const int spectrumNumber, const string& kernelInitString, RealArray& fluxArray, RealArray& fluxErrArray)
    {


      static RealArray saveEnergyArray(0);
      static RealArray constBinEnergyArray;

      static size_t inputBinForward, outputBinForward;
      static size_t inputBinBackward, outputBinBackward;
      static IntegerVector startBinForward, endBinForward;
      static IntegerVector startBinBackward, endBinBackward;
      static RealArray startWeightForward, endWeightForward;
      static RealArray startWeightBackward, endWeightBackward;

      static size_t nBins, nBinsFFT;

      static fftw_complex *fluxIn(0), *fluxOut(0);
      static fftw_complex *kernIn(0), *kernOut(0);
      static fftw_complex *convIn(0), *convOut(0);
      static fftw_plan pFlux(0), pKern(0), pConv(0);

      const Real FUZZY = 1.0e-6;


      // check for a change in the input energy array
      bool newEnergies(false);
      if ( energyArray.size() != saveEnergyArray.size() ) newEnergies = true;
      if ( !newEnergies ) {
	for (size_t i=0; i<energyArray.size(); i++) {
	  if ( energyArray[i] != saveEnergyArray[i] ) newEnergies = true;
	  if ( newEnergies) break;
	}
      }
      
      if ( newEnergies ) {
	saveEnergyArray.resize(energyArray.size());
	saveEnergyArray = energyArray;

	// if new energies then find the minimum energy bin size

	Real minBinSize = energyArray[1] - energyArray[0];
	for (size_t i=1; i<energyArray.size()-1; i++ ) {
	  if ( minBinSize > (energyArray[i+1]-energyArray[i]) ) {
	    minBinSize = energyArray[i+1] - energyArray[i];
	  }
	}

	// find the number of bins of size <= minBinSize which fits in the energy
	// range

	Real energyRange = energyArray[energyArray.size()-1] - energyArray[0];
	nBins = (int)(energyRange/minBinSize) + 2;
	Real binSize = energyRange/(nBins-1);

	constBinEnergyArray.resize(nBins+1);
	constBinEnergyArray[0] = energyArray[0];
	for (size_t i=1; i<constBinEnergyArray.size(); i++) {
	  constBinEnergyArray[i] = constBinEnergyArray[i-1] + binSize;
	}

	// now set up the rebinning info (in both directions because we will
	// have to convert back the convolved flux array).

	Rebin::findFirstBins(energyArray, constBinEnergyArray, FUZZY, inputBinForward,
			     outputBinForward);
	Rebin::initializeBins(energyArray, constBinEnergyArray, FUZZY, inputBinForward,
			      outputBinForward, startBinForward, endBinForward,
			      startWeightForward, endWeightForward);

	Rebin::findFirstBins(constBinEnergyArray, energyArray, FUZZY, inputBinBackward,
			     outputBinBackward);
	Rebin::initializeBins(constBinEnergyArray, energyArray, FUZZY, inputBinBackward,
			      outputBinBackward, startBinBackward, endBinBackward,
			  startWeightBackward, endWeightBackward);


	// we can set up the fftw plan here as well
	if ( fluxIn != 0 ) {
	  fftw_free(fluxIn);
	  fftw_free(fluxOut);
	  fftw_free(kernIn);
	  fftw_free(kernOut);
	  fftw_free(convIn);
	  fftw_free(convOut);
	  fftw_destroy_plan(pFlux);
	  fftw_destroy_plan(pKern);
	  fftw_destroy_plan(pConv);
	}

	// The FFTs have to be zero-padded to avoid cyclical effects
	nBinsFFT = 2*nBins - 1;
	fluxIn = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	fluxOut = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	kernIn = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	kernOut = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	convIn = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	convOut = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	
	pFlux = fftw_plan_dft_1d(nBinsFFT, fluxIn, fluxOut, FFTW_FORWARD, FFTW_ESTIMATE);
	pKern = fftw_plan_dft_1d(nBinsFFT, kernIn, kernOut, FFTW_FORWARD, FFTW_ESTIMATE);
	pConv = fftw_plan_dft_1d(nBinsFFT, convIn, convOut, FFTW_BACKWARD, FFTW_ESTIMATE);
    
	// end of the code which only needs to be rerun if the energies change
      }

      // rebin fluxArray onto the energy binning for the FFT

      RealArray constBinFluxArray(constBinEnergyArray.size()-1);
      Numerics::Rebin::rebin(fluxArray, startBinForward, endBinForward, startWeightForward,
			     endWeightForward, constBinFluxArray);

      // calculate the kernel flux on the energy binning for the FFT

      RealArray constBinKernelFluxArray(constBinEnergyArray.size()-1);
      RealArray kernelFluxErr(0);
      KernelFunction(constBinEnergyArray, kernelParams, spectrumNumber, 
		     constBinKernelFluxArray, kernelFluxErr, kernelInitString);

      // find the flux bin which contains kernelFiducialEnergy

      int kernelFiducialBin = BinarySearch(constBinEnergyArray, kernelFiducialEnergy);

      // load the flux and kernel arrays, padding with zeroes and forward FFT them

      for (size_t i=0; i<nBinsFFT; i++) {
	fluxIn[i][0] = 0.0;
	fluxIn[i][1] = 0.0;
      }
      for (size_t i=0; i<nBins; i++) {
	fluxIn[i][0] = constBinFluxArray[i];
      }

      // rotate the kernel array so the kernel fiducial energy is the first bin

      for (size_t i=0; i<nBinsFFT; i++) {
	kernIn[i][0] = 0.0;
	kernIn[i][1] = 0.0;
      }
      for (size_t i=0; i<nBins; i++) {
	int j = i - kernelFiducialBin;
	if ( j < 0 ) j += nBinsFFT;
	kernIn[j][0] = constBinKernelFluxArray[i];
      }
      
      fftw_execute(pFlux);
      fftw_execute(pKern);

      // multiply the FFTs together
  
      for (size_t i=0; i<nBinsFFT; i++) {
	convIn[i][0] = fluxOut[i][0]*kernOut[i][0]-fluxOut[i][1]*kernOut[i][1];
	convIn[i][1] = fluxOut[i][0]*kernOut[i][1]+fluxOut[i][1]*kernOut[i][0];
      }
  
      // FFT back. divide by nBinsFFT because of the fftw scaling

      fftw_execute(pConv);
      RealArray convolvedFluxArray(constBinEnergyArray.size()-1);
      for (size_t i=0; i<nBins; i++) {
	convolvedFluxArray[i] = (convOut[i][0]/nBinsFFT);
      }

      // rebin the convolved flux back onto the output flux array
      
      fluxArray = 0.0;
      Numerics::Rebin::rebin(convolvedFluxArray, startBinBackward, endBinBackward, 
			     startWeightBackward, endWeightBackward, fluxArray);
  
      return;
    }


  // The ConvolutionInLnSpace method is the convolution in log space for the 
  // case of kernel function which is constant in g(x/y) instead of g(x-y). For
  // example kernels which calculate SR and GR effects


  template<void KernelFunction(const RealArray& kernelEnergyArray, const RealArray& kernelParams, int spectrumNumber, RealArray& kernelFlux, RealArray& kernelFluxErr, const string& kernelInitString)>
    void ConvolutionInLnSpace(const RealArray& energyArray, const RealArray& kernelParams, const Real kernelFiducialEnergy, const int spectrumNumber, const string& kernelInitString, RealArray& fluxArray, RealArray& fluxErrArray)
    {


      static RealArray saveEnergyArray(0);
      static RealArray constBinEnergyArray;

      static size_t inputBinForward, outputBinForward;
      static size_t inputBinBackward, outputBinBackward;
      static IntegerVector startBinForward, endBinForward;
      static IntegerVector startBinBackward, endBinBackward;
      static RealArray startWeightForward, endWeightForward;
      static RealArray startWeightBackward, endWeightBackward;

      static size_t nBins, nBinsFFT;

      static fftw_complex *fluxIn(0), *fluxOut(0);
      static fftw_complex *kernIn(0), *kernOut(0);
      static fftw_complex *convIn(0), *convOut(0);
      static fftw_plan pFlux(0), pKern(0), pConv(0);

      const Real FUZZY = 1.0e-6;


      // check for a change in the input energy array
      bool newEnergies(false);
      if ( energyArray.size() != saveEnergyArray.size() ) newEnergies = true;
      if ( !newEnergies ) {
	for (size_t i=0; i<energyArray.size(); i++) {
	  if ( energyArray[i] != saveEnergyArray[i] ) newEnergies = true;
	  if ( newEnergies) break;
	}
      }
      
      if ( newEnergies ) {

	saveEnergyArray.resize(energyArray.size());
	saveEnergyArray = energyArray;

	// since this is convolution in ln space it is a bit more complicated to
	// calculate the number of bins required. ideally we need to have every
	// bin in our log binning array to have equal or smaller size to the
	// bin in the input array at the same energy.

	// it will be useful to have arrays of input energy bin sizes and
	// central energies

	RealArray energyArrayBinSize(energyArray.size()-1);
	RealArray energyArrayCentralE(energyArray.size()-1);
	for (size_t i=0; i<energyArray.size()-1; i++) {
	  energyArrayBinSize[i] = energyArray[i+1]-energyArray[i];
	  energyArrayCentralE[i] = (energyArray[i+1]+energyArray[i])/2.0;
	}

	// start with the number of bins in the input energy array
	nBins = energyArray.size()-1;
	Real emin = energyArray[0];
	Real emax = energyArray[energyArray.size()-1];

	bool done(false);
	while (!done) {

	  // create the constant log binning with this number of bins
	  constBinEnergyArray.resize(nBins+1);
	  constBinEnergyArray[0] = energyArray[0];
	  Real logBinSize = (log(emax)-log(emin))/nBins;
	  for (size_t i=1; i<constBinEnergyArray.size(); i++) {
	    constBinEnergyArray[i] = constBinEnergyArray[i-1]*exp(logBinSize);
	  }

	  // loop through the bins checking that they are equal or smaller
	  // than the input bin at the same energy. We know that the first bins
	  // in both arrays start at the same energy. Only need to continue
	  // until one bad case is found

	  done = true;
	  size_t inPt = 0;
	  for (size_t i=0; i<nBins; i++) {
	    while (constBinEnergyArray[i+1] > energyArrayCentralE[inPt] && 
		   inPt < energyArrayCentralE.size()-1 ) inPt++;
	    if ( (constBinEnergyArray[i+1]-constBinEnergyArray[i]) 
		 > energyArrayBinSize[inPt] ) {
	      done = false;
	      break;
	    }
	  }

	  if ( !done ) nBins *= 2;

	}

	// now set up the rebinning info (in both directions because we will
	// have to convert back the convolved flux array).

	Rebin::findFirstBins(energyArray, constBinEnergyArray, FUZZY, inputBinForward,
			     outputBinForward);
	Rebin::initializeBins(energyArray, constBinEnergyArray, FUZZY, inputBinForward,
			      outputBinForward, startBinForward, endBinForward,
			      startWeightForward, endWeightForward);

	Rebin::findFirstBins(constBinEnergyArray, energyArray, FUZZY, inputBinBackward,
			     outputBinBackward);
	Rebin::initializeBins(constBinEnergyArray, energyArray, FUZZY, inputBinBackward,
			      outputBinBackward, startBinBackward, endBinBackward,
			  startWeightBackward, endWeightBackward);


	// we can set up the fftw plan here as well
	if ( fluxIn != 0 ) {
	  fftw_free(fluxIn);
	  fftw_free(fluxOut);
	  fftw_free(kernIn);
	  fftw_free(kernOut);
	  fftw_free(convIn);
	  fftw_free(convOut);
	  fftw_destroy_plan(pFlux);
	  fftw_destroy_plan(pKern);
	  fftw_destroy_plan(pConv);
	}

	// The FFTs have to be zero-padded to avoid cyclical effects
	nBinsFFT = 2*nBins - 1;
	
	fluxIn = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	fluxOut = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	kernIn = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	kernOut = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	convIn = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	convOut = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * nBinsFFT);
	
	pFlux = fftw_plan_dft_1d(nBinsFFT, fluxIn, fluxOut, FFTW_FORWARD, FFTW_ESTIMATE);
	pKern = fftw_plan_dft_1d(nBinsFFT, kernIn, kernOut, FFTW_FORWARD, FFTW_ESTIMATE);
	pConv = fftw_plan_dft_1d(nBinsFFT, convIn, convOut, FFTW_BACKWARD, FFTW_ESTIMATE);
    
	// end of the code which only needs to be rerun if the energies change
      }

      // rebin fluxArray onto the energy binning for the FFT

      RealArray constBinFluxArray(constBinEnergyArray.size()-1);
      Numerics::Rebin::rebin(fluxArray, startBinForward, endBinForward, startWeightForward,
			     endWeightForward, constBinFluxArray);

      // calculate the kernel flux on the energy binning for the FFT

      RealArray constBinKernelFluxArray(constBinEnergyArray.size()-1);
      RealArray kernelFluxErr(0);
      KernelFunction(constBinEnergyArray, kernelParams, spectrumNumber, 
		     constBinKernelFluxArray, kernelFluxErr, kernelInitString);

      // find the flux bin which contains kernelFiducialEnergy

      int kernelFiducialBin = BinarySearch(constBinEnergyArray, kernelFiducialEnergy);

      // load the flux and kernel arrays, padding with zeroes and forward FFT them
      // flux is multiplied by the geometric mean of the energy bin

      for (size_t i=0; i<nBinsFFT; i++) {
	fluxIn[i][0] = 0.0;
	fluxIn[i][1] = 0.0;
      }
      for (size_t i=0; i<nBins; i++) {
	fluxIn[i][0] = constBinFluxArray[i];
	//	fluxIn[i][0] = constBinFluxArray[i] * sqrt(constBinEnergyArray[i+1]*constBinEnergyArray[i]);
      }

      // rotate the kernel array so the kernel fiducial energy is the first bin

      for (size_t i=0; i<nBinsFFT; i++) {
	kernIn[i][0] = 0.0;
	kernIn[i][1] = 0.0;
      }
      for (size_t i=0; i<nBins; i++) {
	int j = i - kernelFiducialBin;
	if ( j < 0 ) j += nBinsFFT;
	kernIn[j][0] = constBinKernelFluxArray[i];
      }
      
      fftw_execute(pFlux);
      fftw_execute(pKern);

      // multiply the FFTs together
  
      for (size_t i=0; i<nBinsFFT; i++) {
	convIn[i][0] = fluxOut[i][0]*kernOut[i][0]-fluxOut[i][1]*kernOut[i][1];
	convIn[i][1] = fluxOut[i][0]*kernOut[i][1]+fluxOut[i][1]*kernOut[i][0];
      }
  
      // FFT back. divide by nBinsFFT because of the fftw scaling

      fftw_execute(pConv);
      RealArray convolvedFluxArray(constBinEnergyArray.size()-1);
      for (size_t i=0; i<nBins; i++) {
	convolvedFluxArray[i] = (convOut[i][0]/nBinsFFT);
      }

      // rebin the convolved flux back onto the output flux array
      
      fluxArray = 0.0;
      Numerics::Rebin::rebin(convolvedFluxArray, startBinBackward, endBinBackward, 
			     startWeightBackward, endWeightBackward, fluxArray);
  
      return;
    }

}

#endif
