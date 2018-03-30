//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef MODELCONTAINER_H
#define MODELCONTAINER_H 1
#include <set>

// ctype
#include <ctype.h>
// Error
#include <XSUtil/Error/Error.h>
// cstdlib
#include <cstdlib>
// Observer
#include <XSUtil/Utils/Observer.h>
// ModelTypes
#include <XSModel/GlobalContainer/ModelTypes.h>
// Cosmology
#include <XSModel/GlobalContainer/Cosmology.h>

class DataSet;
class Response;
namespace XSContainer {
    class MdefContainer;
} // namespace XSContainer

class Component;
class Parameter;
class Model;
class SpectralData;


namespace XSContainer {
    //	Container for the model structures. Singleton.



    class ModelContainer : public Observer, //## Inherits: <unnamed>%381605D3B7B8
                           	public Subject  //## Inherits: <unnamed>%3C72CD9E03DB
    {

      public:



        class NoSuchParameter : public YellowAlert  //## Inherits: <unnamed>%3C0BB229031B
        {
          public:
              NoSuchParameter (int index, const string& modelName);

          protected:
          private:
          private: //## implementation
        };
          ~ModelContainer();

          static ModelContainer* Instance ();
          virtual void Update (Subject* data = 0);
          void addToList (Model* newModel);
          void addParameterToList (const string& key, Parameter* value);
          //	Erase parameters from the global parameter list.
          //
          //	Calls reindex to move index values of parameters
          //	with higher index numbers.
          void deregisterModelParameters (const string& keyString);
          Parameter* lookupParameter (int index, const string& model = string()) const;
          Parameter* lookupParameter (const string& qualKey) const;
          //	Internal engine for removing a model from the container
          //	and its parts from the global lists.
          void remove (const string& name);
          //	remove individual model group instance.
          void remove (const string& name, size_t group);
          //	returns pointer to Model identified by name and data
          //	group number.
          Model* lookup (const string& name, size_t group = 0);
          void clearLists ();
          //	Simple function that returns true if a model by name
          //	of the argument has been defined.
          bool isModel (const string& name);
          void attachResponses (const string& modelName) throw (YellowAlert&);
          void calculate (const string& modelName, bool saveComponentFlux = false, bool onlyFrozenNorms=false) const;
          void setParameterFromPrompt (int index, const string& modelName = string(), const string& inputArg = string()) const;
          string indexToName (int index, const string& modelName) const;
          //	global driver for manipulating Component's recompute
          //	flag.
          void setCompute (const string& name, bool value = true);
          int keyToIndex (const string& key) const;
          void setFirstOfModelName (Model* newModel);
          //	return model name corresponding to unique index number.
          //	Most expedient to search through the model map and grab
          //	an index from the first model that matches the name.
          string modelName (int index) const;
          Real countRate (size_t spectrumNumber) const;
          //	utility function that assists the conversion of a model
          //	name qualified parameter index number from user input of
          //	the form
          //
          //	modelName:n
          int fullIndex (int index, const string& modelName) const;
          void makeSourceComponents ();
          void makeSourceComponents (const std::vector<Model*>& mods);
          void foldSources ();
          void clearSources () throw ();
          void fold ();
          std::vector<Model*> lookupModelGroup (const string& modelName = string()) const;
          void fillFakeData (DataSet* dSet) const;
          void explActiveSources (IntegerArray& sourceNums) const;
          int eraseComponentParameters (Component* doomed);
          void registerModel (Model* model);
          Real calcEqWidths (const EqWidthRecord& currComp, Model* mod);
          void deregisterParameter (int oldIndex, int modelIndex);
          //	Erase parameters from the global parameter list.
          //
          //	Calls reindex to move index values of parameters
          //	with higher index numbers.
          void registerModelParameters (const string& keyString);
          void saveData (std::ostream& s);
          void restoreFluxes (const string& modelName, const GroupFluxContainer& savedFluxes) const;
          void storeFluxes (const string& modelName, GroupFluxContainer& fluxes) const;
          void fold (const string& modelName) const;
          void makeDerivatives (const string& modelName, GroupFluxContainer& difference, Real delta, ArrayContainer& foldedDerivative) const;
          void resetComponentFluxes (const string& modelName) const;
          void storeFluxErrors (const string& modelName, GroupFluxContainer& fluxErrors) const;
          void restoreFluxErrors (const string& modelName, const GroupFluxContainer& savedFluxes) const;
          EnergyPointer gatherGroupEnergy (const string& modelName) const;
          void deactivateModel (const string& name);
          static size_t SHIFT ();
          Model* lookup (const Response* resp);
          void applyAutonomousEnergies (const RealArray& energyArray);
          void modifyExtendedEnergies (const ExtendRecord& extend, bool isHigh);
          void rerouteBrokenParLinks (std::vector<Model*>& doomedMods);
          string lookupModelForSource (size_t sourceNum) const;
          bool isExtended () const;
          std::vector<const Model*> getModsForSpec (const SpectralData* spectrum);
          void applyExtendedEnergies ();
          static void flagDoomedPars (std::vector<Model*>& doomedMods);
          //	Public wrapper function for assigning a Model explicit
          //	active status (though may be either on or off).  This
          //	deactivates any other Model that was active for the
          //	source number, and updates the necessary internal arrays.
          void designateActive (const Model* mod);
          void showModel () const;
          void reportModelRate (const SpectralData* sd);
          Real modelSystematicError () const;
          void modelSystematicError (Real value);
          const RealArray& autonomousEnergy () const;
          const ExtendRange& extendedEnergy () const;
          //	If this is set to a positive finite value, model
          //	parameters will use this to produce a fit delta
          //	proportional to the parameter value.
          Real proportionalDelta () const;
          void proportionalDelta (Real value);
          Cosmology& cosmo ();
          void cosmo (const Cosmology& value);
          //	Storing this by pointer only to get away with a forward
          //	declaration to MdefContainer.
          MdefContainer* userMdefs ();
          const ModelMap& modelSet () const;
          const std::map<string,Parameter*>& parameterList () const;
          void parameterList (string key, Parameter* value);
          const std::map<string,std::size_t>& modelLookupTable () const;
          const std::size_t modelLookupTable (string modelName) const;
          void modelLookupTable (string modelName, std::size_t value);
          
          // The activeModelNames map stores 'true' for models
          // designated 'active' for their particular source number.
          // Note that they still might be 'active/off'.
          const std::map<string,bool>& activeModelNames () const;
          const bool activeModelNames (string modelName) const;
          void initializeMixingTransformation (const string& modelName) const;

      public:
        // Additional Public Declarations

      protected:
        // Additional Protected Declarations

      private:
          ModelContainer();

          ModelContainer(const ModelContainer &right);
          ModelContainer & operator=(const ModelContainer &right);

          //	Reindex parameters in list after erasure of a model
          //	or a component.
          //
          //	Strictly private: called by Parameters' erase operations.
          //
          //	Parameters should have access to index field of the
          //	parameters in the list through the mutable keyword.
          //
          //	Arguments are:
          //	first - the index number one greater than
          //	the highest parameterList member erased.
          //
          //	reduceBy - the number of parameterList members
          //	erased.
          void reindexParameterList (int first, int reduceBy);
          void addParameterLookup (int index, const string& key);
          size_t incrementModelCounter ();
          //	Erase parameters from the global parameter list.
          //
          //	Calls reindex to move index values of parameters
          //	with higher index numbers.
          void deregisterModelParameters (const string& keyString, size_t group);
          void reAttachResponses (const string& modelName);
          void deactivateOthers (size_t sourceNum);
          void determineModelObjectStatus (std::map<string,std::vector<Model*> >& doomed, std::map<string,std::vector<Model*> >& alive, std::map<string,std::vector<size_t> >& needed);
          const size_t uniqueNamedModel () const;

        // Data Members for Associations
          ModelMap m_modelSet;

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          static ModelContainer* s_instance;
          std::map<int,string> m_parameterLookupTable;
          size_t m_uniqueNamedModel;
          static const size_t s_SHIFT;
          std::map<string,int> m_parameterReverseLookup;
          Real m_modelSystematicError;
          RealArray m_autonomousEnergy;
          std::map<size_t,string> m_modelForSource;
          ExtendRange m_extendedEnergy;
          Real m_proportionalDelta;

        // Data Members for Associations
          Cosmology m_cosmo;
          MdefContainer* m_userMdefs;
          std::map<string,Parameter*> m_parameterList;
          std::map<string,std::size_t> m_modelLookupTable;
          std::map<string,bool> m_activeModelNames;

        // Additional Implementation Declarations

    };

    // Class XSContainer::ModelContainer::NoSuchParameter 

    // Class XSContainer::ModelContainer 

    inline size_t ModelContainer::SHIFT ()
    {
      return s_SHIFT;
    }

    inline bool ModelContainer::isExtended () const
    {
      return (m_extendedEnergy.first.nBins || m_extendedEnergy.second.nBins);
    }

    inline const size_t ModelContainer::uniqueNamedModel () const
    {
      return m_uniqueNamedModel;
    }

    inline Real ModelContainer::modelSystematicError () const
    {
      return m_modelSystematicError;
    }

    inline void ModelContainer::modelSystematicError (Real value)
    {
      m_modelSystematicError = value;
    }

    inline const RealArray& ModelContainer::autonomousEnergy () const
    {
      return m_autonomousEnergy;
    }

    inline const ExtendRange& ModelContainer::extendedEnergy () const
    {
      return m_extendedEnergy;
    }

    inline Real ModelContainer::proportionalDelta () const
    {
      return m_proportionalDelta;
    }

    inline void ModelContainer::proportionalDelta (Real value)
    {
      m_proportionalDelta = value;
    }

    inline Cosmology& ModelContainer::cosmo ()
    {
      return m_cosmo;
    }

    inline void ModelContainer::cosmo (const Cosmology& value)
    {
      m_cosmo = value;
    }

    inline MdefContainer* ModelContainer::userMdefs ()
    {
      return m_userMdefs;
    }

    inline const ModelMap& ModelContainer::modelSet () const
    {
      return m_modelSet;
    }

    inline const std::map<string,Parameter*>& ModelContainer::parameterList () const
    {
      return m_parameterList;
    }

    inline const std::map<string,std::size_t>& ModelContainer::modelLookupTable () const
    {
      return m_modelLookupTable;
    }

    inline const std::size_t ModelContainer::modelLookupTable (string modelName) const
    {
      std::map<string,size_t>::const_iterator f = m_modelLookupTable.find(modelName);
      return (f != m_modelLookupTable.end() ? f->second : 0);
    }

    inline void ModelContainer::modelLookupTable (string modelName, std::size_t value)
    {
      m_modelLookupTable[modelName] = value;
    }

    inline const std::map<string,bool>& ModelContainer::activeModelNames () const
    {
      return m_activeModelNames;
    }

    inline const bool ModelContainer::activeModelNames (string modelName) const
    {
      std::map<string,bool>::const_iterator f = m_activeModelNames.find(modelName);
      return (f != m_activeModelNames.end() ? f->second : false);
    }

} // namespace XSContainer


#endif
