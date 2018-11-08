//	Astrophysics Science Division,
//	NASA/ Goddard Space Flight Center
//	HEASARC
//	http://heasarc.gsfc.nasa.gov
//	e-mail: ccfits@legacy.gsfc.nasa.gov
//
//	Original author: Ben Dorman

#ifndef IMAGE_H
#define IMAGE_H 1

// functional
#include <functional>
// valarray
#include <valarray>
// vector
#include <vector>
// numeric
#include <numeric>
#ifdef _MSC_VER
#include "MSconfig.h" //form std::min
#endif
#include "CCfits.h"
#include "FitsError.h"
#include "FITSUtil.h"


namespace CCfits {



  template <typename T>
  class Image 
  {

    public:
        Image(const Image< T > &right);
        Image (const std::valarray<T>& imageArray = std::valarray<T>());
        ~Image();
        Image< T > & operator=(const Image< T > &right);

        //	Read data reads the image if readFlag is true and
        //	optional keywords if supplied. Thus, with no arguments,
        //	readData() does nothing.
        const std::valarray<T>& readImage (fitsfile* fPtr, long first, long nElements, T* nullValue, const std::vector<long>& naxes, bool& nulls);
        //	Read data reads the image if readFlag is true and
        //	optional keywords if supplied. Thus, with no arguments,
        //	readData() does nothing.
        const std::valarray<T>& readImage (fitsfile* fPtr, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::vector<long>& stride, T* nullValue, const std::vector<long>& naxes, bool& nulls);
        //	Read data reads the image if readFlag is true and
        //	optional keywords if supplied. Thus, with no arguments,
        //	readData() does nothing.
        void writeImage (fitsfile* fPtr, long first, long nElements, const std::valarray<T>& inData, const std::vector<long>& naxes, T* nullValue = 0);
        //	Read data reads the image if readFlag is true and
        //	optional keywords if supplied. Thus, with no arguments,
        //	readData() does nothing.
        void writeImage (fitsfile* fPtr, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::vector<long>& stride, const std::valarray<T>& inData, const std::vector<long>& naxes);
        void writeImage (fitsfile* fPtr, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::valarray<T>& inData, const std::vector<long>& naxes);
        bool isRead () const;
        void isRead (bool value);
        const std::valarray< T >& image () const;
        void setImage (const std::valarray< T >& value);
        const T image (size_t index) const;
        void setImage (size_t index, T value);

      // Additional Public Declarations

    protected:
      // Additional Protected Declarations

    private:
        std::valarray<T>& image ();
        void prepareForSubset (const std::vector<long>& naxes, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::vector<long>& stride, const std::valarray<T>& inData, std::valarray<T>& subset);
        void loop (size_t iDim, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::vector<long>& stride, size_t iPos, const std::vector<size_t>& incr, const std::valarray<T>& inData, size_t& iDat, const std::vector<size_t>& subIncr, std::valarray<T>& subset, size_t iSub);

      // Additional Private Declarations

    private: //## implementation
      // Data Members for Class Attributes
        bool m_isRead;

      // Data Members for Associations
        std::valarray< T > m_image;

      // Additional Implementation Declarations

  };

  // Parameterized Class CCfits::Image 

  template <typename T>
  inline bool Image<T>::isRead () const
  {
    return m_isRead;
  }

  template <typename T>
  inline void Image<T>::isRead (bool value)
  {
    m_isRead = value;
  }

  template <typename T>
  inline const std::valarray< T >& Image<T>::image () const
  {
    return m_image;
  }

  template <typename T>
  inline void Image<T>::setImage (const std::valarray< T >& value)
  {
    m_image.resize(value.size());
    m_image = value;
  }

  template <typename T>
  inline const T Image<T>::image (size_t index) const
  {
    return m_image[index];
  }

  template <typename T>
  inline void Image<T>::setImage (size_t index, T value)
  {
    m_image[index]  = value;
  }

  // Parameterized Class CCfits::Image 

  template <typename T>
  Image<T>::Image(const Image<T> &right)
        : m_isRead(right.m_isRead),
          m_image(right.m_image)
  {
  }

  template <typename T>
  Image<T>::Image (const std::valarray<T>& imageArray)
        : m_isRead(false),
          m_image(imageArray)
  {
  }


  template <typename T>
  Image<T>::~Image()
  {
  }


  template <typename T>
  Image<T> & Image<T>::operator=(const Image<T> &right)
  {
      // all stack allocated.
     m_isRead = right.m_isRead;
     m_image.resize(right.m_image.size());
     m_image = right.m_image;
     return *this;
  }


  template <typename T>
  const std::valarray<T>& Image<T>::readImage (fitsfile* fPtr, long first, long nElements, T* nullValue, const std::vector<long>& naxes, bool& nulls)
  {
        const size_t N(naxes.size());
        if (N > 0)
        {
                int status(0);
                int any (0);
                FITSUtil::MatchType<T> imageType;
                unsigned long init(1);
                unsigned long nelements(std::accumulate(naxes.begin(),naxes.end(),init,
                                std::multiplies<long>()));

                // truncate to valid array size if too much data asked for.
                // note first is 1-based index)
                long elementsToRead(std::min(static_cast<unsigned long>(nElements),
                                nelements - first + 1));
                if ( elementsToRead < nElements)
                {
                        std::cerr << 
                                "***CCfits Warning: data request exceeds image size, truncating\n"; 
                }
                FITSUtil::FitsNullValue<T> null;
                // initialize m_image to nullValue. resize if necessary.
                if (m_image.size() != static_cast<size_t>(elementsToRead)) 
                {
                        m_image.resize(elementsToRead,null());
                }
                if (fits_read_img(fPtr,imageType(),first,elementsToRead,
                       nullValue,&m_image[0],&any,&status) != 0) throw FitsError(status);

                nulls = (any != 0);
                m_isRead = (first == 1 && nelements == static_cast<unsigned long>(nElements)); 
        }
        else
        {
                m_isRead = true;
                m_image.resize(0);
        }
        return m_image;
  }

  template <typename T>
  const std::valarray<T>& Image<T>::readImage (fitsfile* fPtr, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::vector<long>& stride, T* nullValue, const std::vector<long>& naxes, bool& nulls)
  {



     FITSUtil::CVarray<long> carray;


     int any(0);
     int status(0);
     const size_t N(naxes.size());

     size_t arraySize(1);

     for (size_t j = 0; j < N; ++j)
     {
             arraySize *= (lastVertex[j] - firstVertex[j] + 1);       
     }

     FITSUtil::auto_array_ptr<long> pFpixel(carray(firstVertex));
     FITSUtil::auto_array_ptr<long> pLpixel(carray(lastVertex));
     FITSUtil::auto_array_ptr<long> pStride(carray(stride));

     FITSUtil::MatchType<T> imageType;

     size_t n(m_image.size());
     if (n != arraySize)  m_image.resize(arraySize);
     if (fits_read_subset(fPtr,imageType(),
                             pFpixel.get(),pLpixel.get(),
                             pStride.get(),nullValue,&m_image[0],&any,&status) != 0)
     {
                throw FitsError(status);        

     }

     nulls = (any != 0);
     return m_image;    
  }

  template <typename T>
  void Image<T>::writeImage (fitsfile* fPtr, long first, long nElements, const std::valarray<T>& inData, const std::vector<long>& naxes, T* nullValue)
  {


     int status(0);
     size_t init(1);   
     size_t totalSize= static_cast<size_t>(std::accumulate(naxes.begin(),naxes.end(),init,std::multiplies<long>() ));
     FITSUtil::FitsNullValue<T> null;
     if (m_image.size() != totalSize) m_image.resize(totalSize,null());
     FITSUtil::CAarray<T> convert;
     FITSUtil::auto_array_ptr<T>    pArray(convert(inData));                     
     T* array = pArray.get();


     FITSUtil::MatchType<T> imageType;
     long type(imageType());

     if (fits_write_imgnull(fPtr,type,first,nElements,array,
                     nullValue,&status) || fits_flush_file(fPtr,&status) != 0)
     {
                throw FitsError(status);        

     }



     m_image[std::slice(first-1,nElements,1)]  = inData;
  }

  template <typename T>
  void Image<T>::writeImage (fitsfile* fPtr, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::vector<long>& stride, const std::valarray<T>& inData, const std::vector<long>& naxes)
  {
        // input vectors' size equality will be verified in prepareForSubset.
        const size_t nDim = naxes.size();
        FITSUtil::auto_array_ptr<long> pFPixel(new long[nDim]);
        FITSUtil::auto_array_ptr<long> pLPixel(new long[nDim]);
        std::valarray<T> subset;
        prepareForSubset(naxes,firstVertex,lastVertex,stride,inData,subset);

        long* fPixel = pFPixel.get();
        long* lPixel = pLPixel.get();
        for (size_t i=0; i<nDim; ++i)
        {
           fPixel[i] = firstVertex[i];
           lPixel[i] = lastVertex[i];
        }

        FITSUtil::CAarray<T> convert;
        FITSUtil::auto_array_ptr<T> pArray(convert(subset));
        T* array = pArray.get();
        FITSUtil::MatchType<T> imageType;        
        int status(0);

        if ( fits_write_subset(fPtr,imageType(),fPixel,lPixel,array,&status) 
                        || fits_flush_file(fPtr,&status)  != 0) throw FitsError(status);
  }

  template <typename T>
  std::valarray<T>& Image<T>::image ()
  {

    return m_image;
  }

  template <typename T>
  void Image<T>::prepareForSubset (const std::vector<long>& naxes, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::vector<long>& stride, const std::valarray<T>& inData, std::valarray<T>& subset)
  {

    // naxes, firstVertex, lastVertex, and stride must all be the same size.
    const size_t N = naxes.size();
    if (N != firstVertex.size() || N != lastVertex.size() || N != stride.size())
    {
       string errMsg("*** CCfits Error: Image write function requires that naxes, firstVertex,");
       errMsg += "       \nlastVertex, and stride vectors all be the same size.\n";
       bool silent = false;
       throw FitsException(errMsg, silent);
    }
    for (size_t i=0; i<N; ++i)
    {
       if (naxes[i] < 1)
       {
          bool silent = false;
          throw FitsException("*** CCfits Error: Invalid naxes value sent to image write function.\n", silent);
       }
       string rangeErrMsg("*** CCfits Error: Out-of-range value sent to image write function in arg: ");
       if (firstVertex[i] < 1 || firstVertex[i] > naxes[i]) 
       {
          bool silent = false;
          rangeErrMsg += "firstVertex\n";
          throw FitsException(rangeErrMsg, silent);
       }
       if (lastVertex[i] < firstVertex[i] || lastVertex[i] > naxes[i])
       {
          bool silent = false;
          rangeErrMsg += "lastVertex\n";
          throw FitsException(rangeErrMsg, silent);
       }
       if (stride[i] < 1)
       {
          bool silent = false;
          rangeErrMsg += "stride\n";
          throw FitsException(rangeErrMsg, silent);
       }
    }

    // nPoints refers to the subset of m_image INCLUDING the zero'ed elements 
    // resulting from the stride parameter.  
    // subSizeWithStride refers to the same subset, not counting the zeros.
    size_t subSizeWithStride = 1;
    size_t nPoints = 1;
    std::vector<size_t> subIncr(N);
    for (size_t i=0; i<N; ++i)
    {
       subIncr[i] = nPoints;
       nPoints *= static_cast<size_t>(1+lastVertex[i]-firstVertex[i]);
       subSizeWithStride *= static_cast<size_t>(1+(lastVertex[i]-firstVertex[i])/stride[i]);
    }
    FITSUtil::FitsNullValue<T> null;
    subset.resize(nPoints, null());

    // Trying to avoid at all costs an assignment between 2 valarrays of 
    // different sizes when m_image gets set below.
    if (subSizeWithStride != inData.size())
    {
       bool silent = false;
       string errMsg("*** CCfits Error: Data array size is not consistent with the values");
       errMsg += "\n      in range and stride vectors sent to the image write function.\n";
       throw FitsException(errMsg, silent);
    }

    size_t startPoint = 0;
    size_t dimMult = 1;
    std::vector<size_t> incr(N);
    for (size_t j = 0; j < N; ++j)
    {
       startPoint += dimMult*(firstVertex[j]-1);
       incr[j] = dimMult;
       dimMult *= static_cast<size_t>(naxes[j]);
    }
    const size_t imageSize = dimMult;
    m_image.resize(imageSize,null());

    size_t inDataPos = 0;
    size_t iSub = 0;
    loop(N-1, firstVertex, lastVertex, stride, startPoint, incr, inData, inDataPos, subIncr, subset, iSub);           
  }

  template <typename T>
  void Image<T>::loop (size_t iDim, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::vector<long>& stride, size_t iPos, const std::vector<size_t>& incr, const std::valarray<T>& inData, size_t& iDat, const std::vector<size_t>& subIncr, std::valarray<T>& subset, size_t iSub)
  {
     size_t start = static_cast<size_t>(firstVertex[iDim]);
     size_t stop = static_cast<size_t>(lastVertex[iDim]);
     size_t skip = static_cast<size_t>(stride[iDim]);
     if (iDim == 0)
     {
        size_t length = stop - start + 1;
        for (size_t i=0; i<length; i+=skip)
        {
           m_image[i+iPos] = inData[iDat];
           subset[i+iSub] = inData[iDat++];
        }
     }
     else
     {
        size_t jump = incr[iDim]*skip;
        size_t subJump = subIncr[iDim]*skip;
        for (size_t i=start; i<=stop; i+=skip)
        {
           loop(iDim-1, firstVertex, lastVertex, stride, iPos, incr, inData, iDat, subIncr, subset, iSub);
           iPos += jump;
           iSub += subJump;
        }
     }
  }

  template <typename T>
  void Image<T>::writeImage (fitsfile* fPtr, const std::vector<long>& firstVertex, const std::vector<long>& lastVertex, const std::valarray<T>& inData, const std::vector<long>& naxes)
  {
     std::vector<long> stride(firstVertex.size(), 1);
     writeImage(fPtr, firstVertex, lastVertex, stride, inData, naxes);
  }

  // Additional Declarations

} // namespace CCfits


#endif
