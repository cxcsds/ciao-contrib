//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MATHOPERATOR_H
#define MATHOPERATOR_H 1
#include <xsTypes.h>

namespace Numerics {



    class MathOperator 
    {

      public:
          virtual ~MathOperator() = 0;

          virtual void operator () (RealArray& firstAndNew, const RealArray& second) const;
          virtual void operator () (RealArray& firstAndNew) const;
          size_t nArgs () const;

        // Additional Public Declarations

      protected:
          MathOperator (size_t nArgs);

        // Additional Protected Declarations

      private:
          MathOperator();
          MathOperator & operator=(const MathOperator &right);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          const size_t m_nArgs;

        // Additional Implementation Declarations

    };

  // Binary Functors    
    class PlusOp : public MathOperator
    {
       public:
          //The using decl is to get rid of CC compiler warnings about
          // hiding the non-overridden operator() function in the base class.
          // See item 34 in Sutter's Exceptional C++ for more info.
          using MathOperator::operator();
          PlusOp() : MathOperator(2) {}
          virtual ~PlusOp() {}
          virtual void operator () (RealArray& firstAndNew, const RealArray& second) const;
    };

    class MinusOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          MinusOp() : MathOperator(2) {}
          virtual ~MinusOp() {}
          virtual void operator () (RealArray& firstAndNew, const RealArray& second) const;
    };

    class MultOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          MultOp() : MathOperator(2) {}
          virtual ~MultOp() {}
          virtual void operator () (RealArray& firstAndNew, const RealArray& second) const;
    };

    class DivideOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          DivideOp() : MathOperator(2) {}
          virtual ~DivideOp() {}
          virtual void operator () (RealArray& firstAndNew, const RealArray& second) const;
    };

    class PowOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          PowOp() : MathOperator(2) {}
          virtual ~PowOp() {}
          virtual void operator () (RealArray& firstAndNew, const RealArray& second) const;
    };

    class MaxOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          MaxOp() : MathOperator(2) {}
          virtual ~MaxOp() {}
          virtual void operator () (RealArray& firstAndNew, const RealArray& second) const;
    };

    class MinOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          MinOp() : MathOperator(2) {}
          virtual ~MinOp() {}
          virtual void operator () (RealArray& firstAndNew, const RealArray& second) const;
    };

  // Unary Functors
    class UnaryMinusOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          UnaryMinusOp() : MathOperator(1) {}
          virtual ~UnaryMinusOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class ExpOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          ExpOp() : MathOperator(1) {}
          virtual ~ExpOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class SinOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          SinOp() : MathOperator(1) {}
          virtual ~SinOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class SinDOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          SinDOp() : MathOperator(1) {}
          virtual ~SinDOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class CosOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          CosOp() : MathOperator(1) {}
          virtual ~CosOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class CosDOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          CosDOp() : MathOperator(1) {}
          virtual ~CosDOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class TanOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          TanOp() : MathOperator(1) {}
          virtual ~TanOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class TanDOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          TanDOp() : MathOperator(1) {}
          virtual ~TanDOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class LogOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          LogOp() : MathOperator(1) {}
          virtual ~LogOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class LnOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          LnOp() : MathOperator(1) {}
          virtual ~LnOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class SqrtOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          SqrtOp() : MathOperator(1) {}
          virtual ~SqrtOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class AbsOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          AbsOp() : MathOperator(1) {}
          virtual ~AbsOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class IntOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          IntOp() : MathOperator(1) {}
          virtual ~IntOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class ASinOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          ASinOp() : MathOperator(1) {}
          virtual ~ASinOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class ACosOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          ACosOp() : MathOperator(1) {}
          virtual ~ACosOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class MeanOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          MeanOp() : MathOperator(1) {}
          virtual ~MeanOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class DimOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          DimOp() : MathOperator(1) {}
          virtual ~DimOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class SMinOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          SMinOp() : MathOperator(1) {}
          virtual ~SMinOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    class SMaxOp : public MathOperator
    {
       public:
          using MathOperator::operator();
          SMaxOp() : MathOperator(1) {}
          virtual ~SMaxOp() {}
          virtual void operator () (RealArray& firstAndNew) const;
    };

    // Class Numerics::MathOperator 

    inline MathOperator::MathOperator (size_t nArgs)
      :m_nArgs(nArgs)
    {
    }


    inline size_t MathOperator::nArgs () const
    {
      return m_nArgs;
    }

} // namespace Numerics


#endif
