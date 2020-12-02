//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef STRATEGY_H
#define STRATEGY_H 1


class Fit;




class FitStrategy 
{
  public:
      FitStrategy();
      virtual ~FitStrategy();

      //	apply the strategy to the fit data.
      //
      //	Template method instance: provide public interface in
      //	base class to private abstract methods.
      virtual void perform (Fit* fit);

  protected:
      virtual void doPerform (Fit* fit) = 0;

  private:
      FitStrategy(const FitStrategy &right);
      FitStrategy & operator=(const FitStrategy &right);

  private: //## implementation
};

// Class FitStrategy 


#endif
