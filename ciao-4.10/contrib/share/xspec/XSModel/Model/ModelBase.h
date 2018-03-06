//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MODELBASE_H
#define MODELBASE_H 1
#include <XSModel/Data/SpectralData.h>
#include <set>

// utility
#include <utility>
// xsTypes
#include <xsTypes.h>
// Error
#include <XSUtil/Error/Error.h>
// map
#include <map>
// XSModExpTree
#include <XSUtil/Parse/XSModExpTree.h>

class Response;
class UniqueEnergy;
class UniqueEnergyManager;
class SumComponent;
class ComponentGroup;
class Component;
#include <XSModel/GlobalContainer/ModelTypes.h>
class Parameter;
class ModParam;

#include <XSUtil/Parse/ModelExpression.h>
#include <XSUtil/Parse/ModelExprContexts.h>




class ModelBase 
{

  public:


    class NotAnAddComponent : public YellowAlert  //## Inherits: <unnamed>%3F280AB90045
    {
      public:
          NotAnAddComponent (const string& diag);

      protected:
      private:
      private: //## implementation
    };
      ModelBase (const string& modelName, size_t source);
      ~ModelBase();

      void createParts ();
      ModelBase* clone () const;
      void registerParameters () const;
      int incrementModelParameterCount ();
      int incrementModelComponentCount ();
      void setDataGroupIndexing (size_t group);
      Parameter* getLocalParameter (size_t i) const;
      bool responseIsDummy () const;
      void makeInactive (const bool attachDummy);
      void makeActive ();
      static string refreshExpression (const ModelExprTree& expressionTree);
      std::list<ModParam*> normParams () const;
      //	set all the 'compute' flags for the components to
      //	value. Used to ensure that models are completely
      //	computed, e.g. on initialization (otherwise if user
      //	accepts all of the defaults the compute flag may be false
      //	everywhere).
      void setComputeFlag (bool value);
      void clearArrays ();
      void deleteConv ();
      bool removeResponse (size_t spectrumNumber = 0);
      void allButNorms (IntegerArray& paramsToFreeze) const;
      void resetComponentFlux () const;
      void saveComponentFlux () const;
      void clearSources () throw ();
      void deleteComponent (int group, int component, int index);
      void decrementParameterCount (int by);
      void recreateParts ();
      int decrementModelComponentCount ();
      bool nestedGroups () const;
      void insertComponent (int group, int componentOffset, int index, const string& name, char op);
      std::pair<size_t,size_t> getComponentPeak (size_t compNumber, Real& compTotal);
      Real calcContinuumFlux (size_t compNumber, size_t iMax, size_t specNum, Real fraction);
      void deregisterParameters ();
      Component* firstComponent ();
      void attachResponse (Response* response);
      void fillEnergyContainer ();
      const std::set<UniqueEnergy*>& getUniqueEnergies () const;
      void setAutonomousEnergy (const RealArray& energyArray);
      void setAutonomousEnergy (const XSContainer::ExtendRange& extended);
      void setSpectraForAutonomousEngs ();
      void alignFluxForFold (ArrayContainer& saveFlux, ArrayContainer& saveFluxError, SumComponent* sourceComp = 0);
      void updateNewGainFromFit (const Response* response);
      void bundleParameters (std::vector<Parameter*>& parameters) const;
      void bundleComponents (std::vector<Component*>& components) const;
      static void makeExtendArray (const XSContainer::ExtendRange& extRange, RealArray& extArray);
      //	If there are multiple sources represented in the
      //	data, which sources this model is assigned to fit
      //	(this source number will match with a source parameter
      //	in the Response object).
      size_t sourceNumber () const;
      void sourceNumber (size_t value);
      size_t index () const;
      void index (size_t value);
      const string& name () const;
      void name (const string& value);
      //	If there are multiple sources represented in the
      //	data, which sources this model is assigned to fit
      //	(this source number will match with a source parameter
      //	in the Response object).
      size_t dataGroupNumber () const;
      void dataGroupNumber (size_t value);
      size_t parameterIndexBase () const;
      void parameterIndexBase (size_t value);
      int modelParameterCount () const;
      size_t modelComponentCount () const;
      const string& fullExpression () const;
      void fullExpression (const string& value);
      const bool folded () const;
      void folded (bool value);
      const XSContainer::MixLocations& mixingLocs () const;
      void mixingLocs (const XSContainer::MixLocations& value);
      const SpectralData::FluxCalc& lastModelFluxCalc () const;
      void lastModelFluxCalc (const SpectralData::FluxCalc& value);
      const SpectralData::FluxCalc& lastModelLuminCalc () const;
      void lastModelLuminCalc (const SpectralData::FluxCalc& value);
      bool areCompsSpecDependent () const;
      const std::set<UniqueEnergy*>& autonomousEnergies () const;
      const ModelExprTree& expressionTree () const;
      void expressionTree (const ModelExprTree& value);
      const ArrayContainer& foldedModel () const;
      const RealArray& foldedModel (size_t spectrumNumber) const;
      void foldedModel (size_t spectrumNumber, const RealArray& value);
      const ArrayContainer& modelFlux () const;
      void setModelFlux (const ArrayContainer& value);
      const RealArray& modelFlux (size_t spectrumNumber) const;
      void modelFlux (size_t spectrumNumber, const RealArray& value);
      const ArrayContainer& modelFluxError () const;
      void setModelFluxError (const ArrayContainer& value);
      const RealArray& modelFluxError (size_t spectrumNumber) const;
      void modelFluxError (size_t spectrumNumber, const RealArray& value);
      const std::map<size_t, Response*>& detector () const;
      void detector (const std::map<size_t, Response*>& value);
      const Response* detector (size_t spectrumNumber) const;
      void detector (size_t spectrumNumber, Response* value);
      const ArrayContainer& foldedModelError () const;
      const RealArray& foldedModelError (size_t spectrumNumber) const;
      void foldedModelError (size_t spectrumNumber, const RealArray& value);
      const ArrayContainer& energy () const;
      void setEnergy (const ArrayContainer& value);
      const RealArray& energy (size_t spectrumNumber) const;
      void energy (size_t spectrumNumber, const RealArray& value);
      Real keVFlux (size_t index) const;
      void keVFlux (size_t index, Real value);
      Real ergFlux (size_t index) const;
      void ergFlux (size_t index, Real value);
      const std::pair< Real,Real > keVFluxRange (size_t index) const;
      void keVFluxRange (size_t index, std::pair< Real,Real > value);
      const std::pair< Real,Real > ergFluxRange (size_t index) const;
      void ergFluxRange (size_t index, std::pair< Real,Real > value);
      const std::list<SumComponent*>& componentSource () const;
      void componentSource (const std::list<SumComponent*>& value);
      const UniqueEnergyManager* uniqueEnergyFromResp () const;
      const XSModExpTree<ComponentGroup*>& compGroupTree () const;
      void compGroupTree (const XSModExpTree<ComponentGroup*>& value);
      void checkZeroNorms (std::set<int>& parsWithZeroNorms);
      bool checkParameterMagnitudes(Real threshold) const;

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      ModelBase(const ModelBase &right);
      ModelBase & operator=(const ModelBase &right);
      void checkForSpecDependency ();
      void bundleSubTreeComponents (std::vector<Component*>& components, XSModExpTree<ComponentGroup*>::const_iterator& itCg) const;
      static void makeExtendArrayHelper (const XSContainer::ExtendRecord& extendInfo, Real edge, bool isLow, bool isReverse, RealArray& extendedArray);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      size_t m_sourceNumber;
      size_t m_index;
      string m_name;
      size_t m_dataGroupNumber;
      size_t m_parameterIndexBase;
      int m_modelParameterCount;
      size_t m_modelComponentCount;
      string m_fullExpression;
      bool m_folded;
      // For storage of 0-based component indices of mix (first) or amx (second) type.
      XSContainer::MixLocations m_mixingLocs;
      SpectralData::FluxCalc m_lastModelFluxCalc;
      SpectralData::FluxCalc m_lastModelLuminCalc;
      bool m_areCompsSpecDependent;
      std::set<UniqueEnergy*> m_autonomousEnergies;
      ModelExprTree m_expressionTree;

    // Data Members for Associations
      ArrayContainer m_foldedModel;
      ArrayContainer m_modelFlux;
      ArrayContainer m_modelFluxError;
      std::map<size_t, Response*> m_detector;
      ArrayContainer m_foldedModelError;
      ArrayContainer m_energy;
      std::map<size_t,Real> m_keVFlux;
      std::map<size_t,Real> m_ergFlux;
      std::map<size_t,std::pair< Real,Real > > m_keVFluxRange;
      std::map<size_t,std::pair< Real,Real > > m_ergFluxRange;
      std::list<SumComponent*> m_componentSource;
      UniqueEnergyManager* m_uniqueEnergyFromResp;
      XSModExpTree<ComponentGroup*> m_compGroupTree;

    // Additional Implementation Declarations

};

// Class ModelBase::SpectrumNotDefined 

// Class ModelBase::NotAnAddComponent 

// Class ModelBase 

inline size_t ModelBase::sourceNumber () const
{
  return m_sourceNumber;
}

inline void ModelBase::sourceNumber (size_t value)
{
  m_sourceNumber = value;
}

inline size_t ModelBase::index () const
{
  return m_index;
}

inline void ModelBase::index (size_t value)
{
  m_index = value;
}

inline const string& ModelBase::name () const
{
  return m_name;
}

inline void ModelBase::name (const string& value)
{
  m_name = value;
}

inline size_t ModelBase::dataGroupNumber () const
{
  return m_dataGroupNumber;
}

inline void ModelBase::dataGroupNumber (size_t value)
{
  m_dataGroupNumber = value;
}

inline size_t ModelBase::parameterIndexBase () const
{
  return m_parameterIndexBase;
}

inline void ModelBase::parameterIndexBase (size_t value)
{
  m_parameterIndexBase = value;
}

inline int ModelBase::modelParameterCount () const
{
  return m_modelParameterCount;
}

inline size_t ModelBase::modelComponentCount () const
{
  return m_modelComponentCount;
}

inline const string& ModelBase::fullExpression () const
{
  return m_fullExpression;
}

inline void ModelBase::fullExpression (const string& value)
{
  m_fullExpression = value;
}

inline const bool ModelBase::folded () const
{
  return m_folded;
}

inline void ModelBase::folded (bool value)
{
  m_folded = value;
}

inline const XSContainer::MixLocations& ModelBase::mixingLocs () const
{
  return m_mixingLocs;
}

inline void ModelBase::mixingLocs (const XSContainer::MixLocations& value)
{
  m_mixingLocs = value;
}

inline const SpectralData::FluxCalc& ModelBase::lastModelFluxCalc () const
{
  return m_lastModelFluxCalc;
}

inline void ModelBase::lastModelFluxCalc (const SpectralData::FluxCalc& value)
{
  m_lastModelFluxCalc = value;
}

inline const SpectralData::FluxCalc& ModelBase::lastModelLuminCalc () const
{
  return m_lastModelLuminCalc;
}

inline void ModelBase::lastModelLuminCalc (const SpectralData::FluxCalc& value)
{
  m_lastModelLuminCalc = value;
}

inline bool ModelBase::areCompsSpecDependent () const
{
  return m_areCompsSpecDependent;
}

inline const std::set<UniqueEnergy*>& ModelBase::autonomousEnergies () const
{
  return m_autonomousEnergies;
}

inline const ModelExprTree& ModelBase::expressionTree () const
{
  return m_expressionTree;
}

inline void ModelBase::expressionTree (const ModelExprTree& value)
{
  m_expressionTree = value;
}

inline const ArrayContainer& ModelBase::foldedModel () const
{
  return m_foldedModel;
}

inline void ModelBase::foldedModel (size_t spectrumNumber, const RealArray& value)
{
  ArrayContainer::iterator f =  m_foldedModel.find(spectrumNumber) ;
  if ( f != m_foldedModel.end() )
  {   
        m_foldedModel.erase(f);
  }
  m_foldedModel.insert(ArrayContainer::value_type(spectrumNumber,value));   
}

inline const ArrayContainer& ModelBase::modelFlux () const
{
  return m_modelFlux;
}

inline void ModelBase::setModelFlux (const ArrayContainer& value)
{
  m_modelFlux = value;
}

inline void ModelBase::modelFlux (size_t spectrumNumber, const RealArray& value)
{
  ArrayContainer::iterator f =  m_modelFlux.find(spectrumNumber) ;
  if ( f != m_modelFlux.end() )
  {   
        m_modelFlux.erase(f);
  }
  m_modelFlux.insert(ArrayContainer::value_type(spectrumNumber,value));   
}

inline const ArrayContainer& ModelBase::modelFluxError () const
{
  return m_modelFluxError;
}

inline void ModelBase::setModelFluxError (const ArrayContainer& value)
{
  m_modelFluxError = value;
}

inline void ModelBase::modelFluxError (size_t spectrumNumber, const RealArray& value)
{
  ArrayContainer::iterator f =  m_modelFluxError.find(spectrumNumber) ;
  if ( f != m_modelFluxError.end() )
  {   
        m_modelFluxError.erase(f);
  }        
  m_modelFluxError.insert(ArrayContainer::value_type(spectrumNumber,value));   
}

inline const std::map<size_t, Response*>& ModelBase::detector () const
{
  return m_detector;
}

inline void ModelBase::detector (const std::map<size_t, Response*>& value)
{
  m_detector = value;
}

inline const ArrayContainer& ModelBase::foldedModelError () const
{
  return m_foldedModelError;
}

inline void ModelBase::foldedModelError (size_t spectrumNumber, const RealArray& value)
{
  ArrayContainer::iterator f =  m_foldedModelError.find(spectrumNumber) ;
  if ( f != m_foldedModelError.end() )
  {   
        m_foldedModelError.erase(f);
  }
  m_foldedModelError.insert(ArrayContainer::value_type(spectrumNumber,value));   
}

inline const ArrayContainer& ModelBase::energy () const
{
  return m_energy;
}

inline void ModelBase::setEnergy (const ArrayContainer& value)
{
  m_energy = value;
}

inline void ModelBase::energy (size_t spectrumNumber, const RealArray& value)
{
  ArrayContainer::iterator f =  m_energy.find(spectrumNumber) ;
  if ( f != m_energy.end() )
  {   
        m_energy.erase(f);
  }
  m_energy.insert(ArrayContainer::value_type(spectrumNumber,value));   
}

inline Real ModelBase::keVFlux (size_t index) const
{
  std::map<size_t,Real>::const_iterator ei = m_keVFlux.find(index);
  if ( ei != m_keVFlux.end()) return ei->second;
  else return 0;
}

inline void ModelBase::keVFlux (size_t index, Real value)
{
  m_keVFlux[index] = value;
}

inline Real ModelBase::ergFlux (size_t index) const
{
  std::map<size_t,Real>::const_iterator ei = m_ergFlux.find(index);
  if ( ei != m_ergFlux.end()) return ei->second;
  else return 0;
}

inline void ModelBase::ergFlux (size_t index, Real value)
{
  m_ergFlux[index] = value;
}

inline const std::pair< Real,Real > ModelBase::keVFluxRange (size_t index) const
{
  std::map<size_t,std::pair<Real, Real> >::const_iterator ei = m_keVFluxRange.find(index);
  if ( ei != m_keVFluxRange.end()) return ei->second;
  else return std::pair<Real,Real>(0,0);
}

inline void ModelBase::keVFluxRange (size_t index, std::pair< Real,Real > value)
{
  m_keVFluxRange[index] = value;
}

inline const std::pair< Real,Real > ModelBase::ergFluxRange (size_t index) const
{
  std::map<size_t,std::pair<Real, Real> >::const_iterator ei = m_ergFluxRange.find(index);
  if ( ei != m_ergFluxRange.end()) return ei->second;
  else return std::pair<Real,Real>(0,0);
}

inline void ModelBase::ergFluxRange (size_t index, std::pair< Real,Real > value)
{
  m_ergFluxRange[index] = value;
}

inline const std::list<SumComponent*>& ModelBase::componentSource () const
{
  return m_componentSource;
}

inline void ModelBase::componentSource (const std::list<SumComponent*>& value)
{
  m_componentSource = value;
}

inline const UniqueEnergyManager* ModelBase::uniqueEnergyFromResp () const
{
  return m_uniqueEnergyFromResp;
}

inline const XSModExpTree<ComponentGroup*>& ModelBase::compGroupTree () const
{
  return m_compGroupTree;
}

inline void ModelBase::compGroupTree (const XSModExpTree<ComponentGroup*>& value)
{
  m_compGroupTree = value;
}


#endif
