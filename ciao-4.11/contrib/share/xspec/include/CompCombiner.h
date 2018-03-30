//C++
#ifndef COMPCOMBINER_H
#define COMPCOMBINER_H 1

#include <xsTypes.h>
#include <XSModel/Model/Component/ComponentListTypes.h>
#include <XSUtil/Parse/XSModExpTree.h>
#include <stack>
#include <vector>

class CompCombiner;
class Model;
class Component;
class ComponentGroup;
class SumComponent;



class CombineIterator
{
   public:
      friend class CompCombiner;
      CombineIterator(const CombineIterator &right);
      CombineIterator & operator=(const CombineIterator &right);
      CombineIterator& operator ++ ();
      // Equality operators are currently valid only for comparing 'end' condition.
      bool operator == (const CombineIterator& right) const;
      bool operator != (const CombineIterator& right) const;
      ~CombineIterator();
      
   private:
      // General constructor
      CombineIterator(const CompCombiner* combiner);
      // Constructor for creating 'empty' end iterator.
      CombineIterator();
      
      struct CompLocInfo
      {
         CompLocInfo(ComponentListConstIterator itComp, size_t iComp)
           : m_itComp(itComp), m_iComp(iComp) {}
         ComponentListConstIterator m_itComp;
         size_t m_iComp;
      };
      
      void initForComponentGroup();
      void initForSubgroup();
      void postfixOperatorLocs (size_t skipIdx, size_t nSkip);
      void setToEnd();
      
      const CompCombiner* m_combiner;
      const size_t m_nGroups;
      size_t m_iCurModel;
      
      // These vectors will all be sized to m_nGroups.
      std::vector<XSModExpTree<ComponentGroup*>::const_iterator> m_itCurCompGroups;
      std::vector<size_t> m_iCalcSubgroups;
      std::vector<std::vector<std::pair<CompLocInfo,CompLocInfo> > > m_subgroupLocs;
      std::vector<CompLocInfo> m_curCompLocs;
      std::vector<std::stack<Component*> > m_compStacks;
      std::vector<SumComponent*> m_totalAccumulated;
      
      std::vector<size_t> m_starLocs;
      size_t m_iCurStarLoc;
      
      // Members for handling parentheses sum.
      std::vector<SumComponent*> m_parenFluxes; // also sized to m_nGroups
      size_t m_insIdx;
      size_t m_nSkip;
      
      // Member for calculating individual component sources
      //  (ie. eqwidth, setplot add).
      //  Vector elements are: m_indivStacks[iModel_obj][iAdditiveSources].
      //  This is not to be used unless CompCombiner's doStoreSources = True.
      typedef std::vector<std::vector<std::stack<Component*> > > AddCompStacks;
      AddCompStacks m_indivStacks;
      
};

class CompCombiner
{
   public:
      CompCombiner(const std::vector<Model*>& models, bool storeSources=false);
      ~CompCombiner();
      
      typedef CombineIterator iterator;
      
      iterator begin();
      iterator end();
      const std::vector<Model*>& models() const;
      bool doStoreSources() const;
      
   private:
      CompCombiner(const CompCombiner &right);
      CompCombiner & operator=(const CompCombiner &right);
      
      const std::vector<Model*> m_models;
      const bool m_doStoreSources;
};

inline const std::vector<Model*>& CompCombiner::models() const
{
   return m_models;
}

inline bool CompCombiner::doStoreSources() const
{
   return m_doStoreSources;
}
#endif
