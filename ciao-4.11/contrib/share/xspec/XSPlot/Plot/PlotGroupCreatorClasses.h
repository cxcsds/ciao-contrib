//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef PLOTGROUPCREATORCLASSES_H
#define PLOTGROUPCREATORCLASSES_H 1
#include <xsTypes.h>
#include <queue>

// PlotGroupCreator
#include <XSPlot/Plot/PlotGroupCreator.h>

class Model;




class CreateModelPlotGroups : public PlotGroupCreator  //## Inherits: <unnamed>%4AB7CF0D021E
{

  public:
      CreateModelPlotGroups();
      virtual ~CreateModelPlotGroups();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings);
      std::queue<string>& modNames ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      CreateModelPlotGroups(const CreateModelPlotGroups &right);
      CreateModelPlotGroups & operator=(const CreateModelPlotGroups &right);

      PlotGroup* initializePlotGroup (const Model* model, int specNum, const RealArray& energy, const PlotSettings& settings);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      std::queue<string> m_modNames;

    // Additional Implementation Declarations

};



class CreateDemPlotGroups : public PlotGroupCreator  //## Inherits: <unnamed>%4AB7D08F031F
{

  public:
      CreateDemPlotGroups();
      virtual ~CreateDemPlotGroups();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      CreateDemPlotGroups(const CreateDemPlotGroups &right);
      CreateDemPlotGroups & operator=(const CreateDemPlotGroups &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

class CreateEqwPlotGroups : public PlotGroupCreator  //## Inherits: <unnamed>%4AB7D08F031F
{

  public:
      CreateEqwPlotGroups();
      virtual ~CreateEqwPlotGroups();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      CreateEqwPlotGroups(const CreateEqwPlotGroups &right);
      CreateEqwPlotGroups & operator=(const CreateEqwPlotGroups &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};



class CreateEfficiencyPlotGroups : public PlotGroupCreator  //## Inherits: <unnamed>%4AB7D1B6024C
{

  public:
      CreateEfficiencyPlotGroups();
      virtual ~CreateEfficiencyPlotGroups();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      CreateEfficiencyPlotGroups(const CreateEfficiencyPlotGroups &right);
      CreateEfficiencyPlotGroups & operator=(const CreateEfficiencyPlotGroups &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};



class CreateChainPlotGroups : public PlotGroupCreator  //## Inherits: <unnamed>%4AB7D2A6004D
{

  public:
      CreateChainPlotGroups();
      virtual ~CreateChainPlotGroups();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings);
      void addColNums(size_t xCol, size_t yCol);
      void clearCmdArgs();
      // See data member description for why this is necessary.
      void setPaneIndex(int value);
      void addNSkip(size_t nSkip);
      
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      CreateChainPlotGroups(const CreateChainPlotGroups &right);
      CreateChainPlotGroups & operator=(const CreateChainPlotGroups &right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      // PlotGroupCreators do not normally need to know pane index.  But
      // due to the extra-argument input, chain plots do.  Both their
      // plot group data and axes labels can vary between panes.
      int m_paneIndex;
      std::vector<std::pair<size_t,size_t> > m_colNums;
      // Users may set this to thin out crowded chain plots.
      // Only 1 out of every m_nSkip points will be plotted.
      std::vector<size_t> m_nSkip;

    // Additional Implementation Declarations

};

// Class CreateModelPlotGroups 

inline std::queue<string>& CreateModelPlotGroups::modNames ()
{
   return m_modNames;
}

// Class CreateEfficiencyPlotGroups 

// Class CreateChainPlotGroups 

inline void CreateChainPlotGroups::setPaneIndex(int value)
{
   m_paneIndex = value;
}

inline void CreateChainPlotGroups::addColNums (size_t xCol, size_t yCol)
{
   m_colNums.push_back(std::pair<size_t,size_t>(xCol,yCol));
}

inline void CreateChainPlotGroups::clearCmdArgs ()
{
   m_colNums.clear();
   m_nSkip.clear();
}

inline void CreateChainPlotGroups::addNSkip(size_t nSkip)
{
   m_nSkip.push_back(nSkip);
}


class CreateGoodnessPlotGroups : public PlotGroupCreator  //## Inherits: <unnamed>%4AB7D08F031F
{

  public:
      CreateGoodnessPlotGroups();
      virtual ~CreateGoodnessPlotGroups();

      virtual std::vector<PlotGroup*> createPlotGroups (const PlotSettings& settings);

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      CreateGoodnessPlotGroups(const CreateGoodnessPlotGroups &right);
      CreateGoodnessPlotGroups & operator=(const CreateGoodnessPlotGroups &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};







#endif
