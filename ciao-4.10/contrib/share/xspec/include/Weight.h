//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef WEIGHT_H
#define WEIGHT_H 1
#include "xsTypes.h"

// xsTypes
#include <xsTypes.h>
// Error
#include <XSUtil/Error/Error.h>

class SpectralData;
class Model;

namespace XSContainer {



    class Weight 
    {
      public:



        class ArrayInitializationError : public RedAlert  //## Inherits: <unnamed>%3C599F4E02B9
        {
          public:
              ArrayInitializationError (size_t num);

          protected:
          private:
          private: //## implementation
        };
          virtual ~Weight() = 0;

          virtual void operator () (SpectralData& spectrum, const RealArray& norm) const = 0;
          virtual void dataVariance (const Model& model, ArrayContainer& variance) const;
          //	returns an array representing the derivative of the
          //	weighting for the input spectrum number.
          virtual void varianceDeriv (const Model& model, ArrayContainer& dv) const;
          virtual Weight* clone () const = 0;
          const string& name () const;

      public:
      protected:
          Weight (const string& name);

      private:
      private: //## implementation
        // Data Members for Class Attributes
          const string m_name;

    };



    class StandardWeight : public Weight  //## Inherits: <unnamed>%3C4348F50116
    {
      public:
          StandardWeight ();
          virtual ~StandardWeight();

          virtual void operator () (SpectralData& spectrum, const RealArray& norm) const;
          virtual void dataVariance (const Model& model, ArrayContainer& variance) const;
          virtual StandardWeight* clone () const;

      protected:
      private:
      private: //## implementation
    };



    class ModelWeight : public Weight  //## Inherits: <unnamed>%3C4341EF0301
    {
      public:
          ModelWeight ();
          virtual ~ModelWeight();

          virtual void dataVariance (const Model& model, ArrayContainer& variance) const;
          //	returns an array representing the derivative of the
          //	weighting for the input spectrum number.
          virtual void varianceDeriv (const Model& model, ArrayContainer& dv) const;
          void operator () (SpectralData& spectrum, const RealArray& norm) const;
          virtual ModelWeight* clone () const;

      protected:
      private:
      private: //## implementation
    };



    class GehrelsWeight : public Weight  //## Inherits: <unnamed>%3C4341EB033F
    {
      public:
          GehrelsWeight ();
          virtual ~GehrelsWeight();

          virtual void operator () (SpectralData& spectrum, const RealArray& norm) const;
          virtual void dataVariance (const Model& model, ArrayContainer& variance) const;
          virtual GehrelsWeight* clone () const;

      protected:
      private:
      private: //## implementation
    };



    class ChurazovWeight : public Weight  //## Inherits: <unnamed>%3C4341E700C4
    {
      public:
          ChurazovWeight ();
          virtual ~ChurazovWeight();

          virtual void operator () (SpectralData& spectrum, const RealArray& norm) const;
          virtual void dataVariance (const Model& model, ArrayContainer& variance) const;
          virtual ChurazovWeight* clone () const;

      protected:
      private:
      private: //## implementation
    };

    // Class XSContainer::Weight::ArrayInitializationError 

    // Class XSContainer::Weight 

    inline const string& Weight::name () const
    {
      return m_name;
    }

    // Class XSContainer::StandardWeight 

    // Class XSContainer::ModelWeight 

    // Class XSContainer::GehrelsWeight 

    // Class XSContainer::ChurazovWeight 

} // namespace XSContainer


#endif
