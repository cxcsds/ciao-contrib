//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef XSMODEXPTREE_H
#define XSMODEXPTREE_H 1
#include <xsTypes.h>
#include <XSUtil/Error/Error.h>
#include <vector>
#include <algorithm>
template <typename T>
class XSModExpTree;

class ExpTreeNodeType 
{
   public:
      ExpTreeNodeType():pos(-999), parentPos(-1), children() {}
      int pos;
      int parentPos;
      IntegerArray children;

};

//	It would really be cleaner to combine the ValCont and Ret
//	Type template parameters into a single Traits class.
//	However, SunWS6.0 seemed to have bizarre and
//	unsystematic compile-time errors when RetType was
//	enclosed in a traits class and used as the return type
//	of a function (which is really its sole purpose).



template <typename T, typename ValCont, typename RetType>
class XSModExpTree_Iterator 
{

  public:
      XSModExpTree_Iterator(const XSModExpTree_Iterator< T,ValCont,RetType > &right);
      ~XSModExpTree_Iterator();
      XSModExpTree_Iterator< T,ValCont,RetType > & operator=(const XSModExpTree_Iterator< T,ValCont,RetType > &right);

      XSModExpTree_Iterator<T,ValCont,RetType>& operator ++ ();
      const XSModExpTree_Iterator<T,ValCont,RetType> operator ++ (int );
      bool operator == (const XSModExpTree_Iterator<T,ValCont,RetType>& right) const;
      bool operator != (const XSModExpTree_Iterator<T,ValCont,RetType>& right) const;
      RetType& operator * ();
      RetType* operator -> ();
      void childNodes (IntegerArray& children) const;
      XSModExpTree_Iterator<T,ValCont,RetType>& postOrderNext ();

    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      XSModExpTree_Iterator (const ExpTreeNodeType* nodePointer, const std::vector<ExpTreeNodeType>& nodeArray, ValCont& valueArray, const XSModExpTree<T>* theContainer);

      int nextPreOrder (int nodePos) const;

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      const ExpTreeNodeType* m_nodePointer;
      const std::vector<ExpTreeNodeType>& m_nodeArray;
      ValCont& m_valueArray;
      const XSModExpTree<T>* m_theContainer;

    // Additional Implementation Declarations
       template <typename U>
       friend class XSModExpTree;
};
//	This is a specialized tree class for containing the
//	relations between XSPEC Expressions and their nested
//	sub-Expressions (or the same relations among Component
//	Group objects).  This does not offer the level of
//	functionality of STL containers (by a long shot).
//
//	Important:  This performs NO internal ordering.  It
//	ASSUMES client will enter values in a POST_ORDER fashion
//	and supply appropriate relational information .  The
//	tree iterators will then perform a PRE-ORDER traversal,
//	but with the begin node defined as the root's first
//	child rather than the root itself (due to the nature of
//	the way Expressions and ComponentGroups are used in
//	XSPEC).
//
//	As with STL, the end iterator does not point to a valid
//	element.  Also like STL, this DOES NOT call delete on
//	values during cleanup if T is a pointer.  The client
//	will need to do this by retrieving the values array.



template <typename T>
class XSModExpTree 
{

  public:



    typedef XSModExpTree_Iterator<T,std::vector<T>,T > iterator;



    typedef XSModExpTree_Iterator<T,const std::vector<T>, const T > const_iterator;
      XSModExpTree();

      XSModExpTree(const XSModExpTree< T > &right);
      ~XSModExpTree();
      XSModExpTree< T > & operator=(const XSModExpTree< T > &right);

      typename XSModExpTree<T>::iterator begin ();
      typename XSModExpTree<T>::iterator end ();
      void clear ();
      //	This REQUIRES that insertion is done in post-order
      //	fashion, meaning that all nodes specified in the
      //	children array have already been inserted.
      void insert (T entry, const IntegerArray& children);
      typename XSModExpTree<T>::const_iterator begin () const;
      typename XSModExpTree<T>::const_iterator end () const;
      std::vector<T>& values ();
      size_t size () const;
      int position (const typename XSModExpTree<T>::iterator& it) const;
      int position (const typename XSModExpTree<T>::const_iterator& it) const;
      typename XSModExpTree<T>::iterator postBegin ();
      typename XSModExpTree<T>::const_iterator postBegin () const;
      void insertRoot (const IntegerArray& rootChildren);
      const IntegerArray& getRoot () const;
      const std::vector<T>& values () const;

  public:
    // Additional Public Declarations

  protected:
    // Additional Protected Declarations

  private:
      void swap (XSModExpTree<T>& right);

    // Additional Private Declarations

  private: //## implementation
    // Data Members for Class Attributes
      std::vector<ExpTreeNodeType> m_nodes;
      std::vector<T> m_values;

    // Additional Implementation Declarations

};

// Parameterized Class XSModExpTree_Iterator 

template <typename T, typename ValCont, typename RetType>
inline bool XSModExpTree_Iterator<T,ValCont,RetType>::operator == (const XSModExpTree_Iterator<T,ValCont,RetType>& right) const
{
   return m_nodePointer == right.m_nodePointer;
}

template <typename T, typename ValCont, typename RetType>
inline bool XSModExpTree_Iterator<T,ValCont,RetType>::operator != (const XSModExpTree_Iterator<T,ValCont,RetType>& right) const
{
   return m_nodePointer != right.m_nodePointer;
}

template <typename T, typename ValCont, typename RetType>
inline RetType& XSModExpTree_Iterator<T,ValCont,RetType>::operator * ()
{
   if (!m_nodePointer)
      throw RedAlert("Attempting to dereference non-existing XSModExpTree node.");
   return m_valueArray[m_nodePointer->pos];
}

template <typename T, typename ValCont, typename RetType>
inline RetType* XSModExpTree_Iterator<T,ValCont,RetType>::operator -> ()
{
   if (!m_nodePointer)
      throw RedAlert("Attempting to dereference non-existing XSModExpTree node.");
   return &m_valueArray[m_nodePointer->pos];
}

template <typename T, typename ValCont, typename RetType>
inline void XSModExpTree_Iterator<T,ValCont,RetType>::childNodes (IntegerArray& children) const
{
   children = m_nodePointer->children;
}

// Parameterized Class XSModExpTree 

template <typename T>
inline std::vector<T>& XSModExpTree<T>::values ()
{
   return m_values;
}

template <typename T>
inline size_t XSModExpTree<T>::size () const
{
   return m_values.size();
}

template <typename T>
inline int XSModExpTree<T>::position (const typename XSModExpTree<T>::iterator& it) const
{
   int nodePos = it.m_nodePointer->pos;
   if (nodePos < 0 || nodePos >= (int)m_values.size())
      throw RedAlert("Invalid node pointer accessed in ExpTree position function.");
   return nodePos;
}

template <typename T>
inline int XSModExpTree<T>::position (const typename XSModExpTree<T>::const_iterator& it) const
{
   int nodePos = it.m_nodePointer->pos;
   if (nodePos < 0 || nodePos >= (int)m_values.size())
      throw RedAlert("Invalid node pointer accessed in ExpTree position function.");
   return nodePos;
}

template <typename T>
inline const std::vector<T>& XSModExpTree<T>::values () const
{
  return m_values;
}

// Parameterized Class XSModExpTree_Iterator 

template <typename T, typename ValCont, typename RetType>
XSModExpTree_Iterator<T,ValCont,RetType>::XSModExpTree_Iterator(const XSModExpTree_Iterator<T,ValCont,RetType> &right)
  :m_nodePointer(right.m_nodePointer), // shallow copies, non-owning
   m_nodeArray(right.m_nodeArray),
   m_valueArray(right.m_valueArray),
   m_theContainer(right.m_theContainer)
{
}

template <typename T, typename ValCont, typename RetType>
XSModExpTree_Iterator<T,ValCont,RetType>::XSModExpTree_Iterator (const ExpTreeNodeType* nodePointer, const std::vector<ExpTreeNodeType>& nodeArray, ValCont& valueArray, const XSModExpTree<T>* theContainer)
   :m_nodePointer(nodePointer),
    m_nodeArray(nodeArray),
    m_valueArray(valueArray),
    m_theContainer(theContainer)
{
}


template <typename T, typename ValCont, typename RetType>
XSModExpTree_Iterator<T,ValCont,RetType>::~XSModExpTree_Iterator()
{
}


template <typename T, typename ValCont, typename RetType>
XSModExpTree_Iterator<T,ValCont,RetType> & XSModExpTree_Iterator<T,ValCont,RetType>::operator=(const XSModExpTree_Iterator<T,ValCont,RetType> &right)
{
   if (m_theContainer != right.m_theContainer)
      throw RedAlert("Invalid attempt to assign iterator of one XSModExpTree to another.");
   m_nodePointer = right.m_nodePointer;
   return *this;
}


template <typename T, typename ValCont, typename RetType>
XSModExpTree_Iterator<T,ValCont,RetType>& XSModExpTree_Iterator<T,ValCont,RetType>::operator ++ ()
{
   // Pre-increment.  If m_nodePointer = 0, assume we are at the end and
   // do nothing.
   if (m_nodePointer)
   {
      // Let's not assume anywhere that &a[n] == &a[0]+n since this 
      // wasn't truly in the '98 standard.
      int nextPos = nextPreOrder(m_nodePointer->pos);
      if (nextPos == (int)m_nodeArray.size()-1)
      {
         // This is the root node, which we'll use for the end.
         m_nodePointer = 0;
      }
      else
         m_nodePointer = &m_nodeArray[nextPos];
   }
   return *this;
}

template <typename T, typename ValCont, typename RetType>
const XSModExpTree_Iterator<T,ValCont,RetType> XSModExpTree_Iterator<T,ValCont,RetType>::operator ++ (int )
{
   XSModExpTree_Iterator<T, ValCont, RetType> oldNode(*this);
   ++(*this);
   return oldNode;
}

template <typename T, typename ValCont, typename RetType>
int XSModExpTree_Iterator<T,ValCont,RetType>::nextPreOrder (int nodePos) const
{
   // This is a recursive function.
   const ExpTreeNodeType& testNode = m_nodeArray[nodePos];
   int nChildren = (int)testNode.children.size();
   int currPos = m_nodePointer->pos;
   int nextPos = 0;
   if (nChildren)
   {
      if (currPos == testNode.pos)
         // Simple case, just grab the node's first child.
         nextPos = testNode.children[0];
      else 
      {
         // It has been kicked back up here from a child.  Therefore
         // find whose subtree this is coming from, indicated by first
         // child with pos >= currPos (ASSUMING insertions were post-order).
         int currSubTree = -1;
         for (int i=0; i<nChildren; ++i)
         {
            if (testNode.children[i] >= currPos)
            {
               currSubTree = i;
               break;
            }
         }
         if (currSubTree == -1)
         {
            throw RedAlert("ModExpTree structural relation error.");
         }
         else if (currSubTree == nChildren-1)
         {
            // Pass back up to parent, or if we're at root, simply return
            // the root node position.
            if (testNode.parentPos >= 0)
               nextPos = nextPreOrder(testNode.parentPos);
            else
               nextPos = m_nodeArray.size() - 1;
         }
         else
         {
            // Start on next subtree
            nextPos = testNode.children[currSubTree+1];
         }         
      }
   }
   else
   {
      // Pass back up to parent.  Don't need to check if this is root
      // node, since root will always have at least 1 child and can't
      // get in here.
      nextPos = nextPreOrder(testNode.parentPos);
   }
   return nextPos;             
}

template <typename T, typename ValCont, typename RetType>
XSModExpTree_Iterator<T,ValCont,RetType>& XSModExpTree_Iterator<T,ValCont,RetType>::postOrderNext ()
{
   if (m_nodePointer)
   {
      int currPos = m_nodePointer->pos;
      if (currPos >= (int)m_nodeArray.size() - 2)
      {
         // Next is the root node, which we'll use for the end.
         m_nodePointer = 0;
      }
      else
         m_nodePointer = &m_nodeArray[currPos+1];
   }
   return *this;
}

// Additional Declarations

// Parameterized Class XSModExpTree 

template <typename T>
XSModExpTree<T>::XSModExpTree()
{
}

template <typename T>
XSModExpTree<T>::XSModExpTree(const XSModExpTree<T> &right)
  : m_nodes(right.m_nodes),
    m_values(right.m_values)
{
}


template <typename T>
XSModExpTree<T>::~XSModExpTree()
{
}


template <typename T>
XSModExpTree<T> & XSModExpTree<T>::operator=(const XSModExpTree<T> &right)
{
   if (this != &right)
   {
      XSModExpTree<T> tmp(right);
      swap(tmp);
   }
   return *this;
}


template <typename T>
typename XSModExpTree<T>::iterator XSModExpTree<T>::begin ()
{
   // Not true pre-order since begin is not defined as the root,
   // but the root's first child.  The root will be treated as
   // the end.
   ExpTreeNodeType* beginNode = 0;
   if (m_nodes.size() > 1)
   {
      // We have a root, and root has a child.
      const ExpTreeNodeType& root = m_nodes[m_nodes.size()-1];
      beginNode = &m_nodes[root.children[0]];
   }
   return iterator(beginNode, m_nodes, m_values, this);
}

template <typename T>
typename XSModExpTree<T>::iterator XSModExpTree<T>::end ()
{
   ExpTreeNodeType* endNode = 0;
   return iterator(endNode, m_nodes, m_values, this);
}

template <typename T>
void XSModExpTree<T>::clear ()
{
   m_values.clear();
   m_nodes.clear();
}

template <typename T>
void XSModExpTree<T>::insert (T entry, const IntegerArray& children)
{
   m_values.push_back(entry);
   ExpTreeNodeType newNode;
   newNode.pos = static_cast<int>(m_values.size()-1);
   // parentPos will be set when this node's parent is
   // inserted into the tree.
   newNode.parentPos = -1;
   newNode.children = children;
   m_nodes.push_back(newNode);
   for (size_t i=0; i<children.size(); ++i)
   {
      m_nodes[children[i]].parentPos = newNode.pos;
   }
}

template <typename T>
typename XSModExpTree<T>::const_iterator XSModExpTree<T>::begin () const
{
   const ExpTreeNodeType* beginNode = 0;
   if (m_nodes.size() > 1)
   {
      // We have a root, and root has a child.
      const ExpTreeNodeType& root = m_nodes[m_nodes.size()-1];
      beginNode = &m_nodes[root.children[0]];
   }
   return const_iterator(beginNode, m_nodes, m_values, this);
}

template <typename T>
typename XSModExpTree<T>::const_iterator XSModExpTree<T>::end () const
{
   const ExpTreeNodeType* endNode = 0;
   return const_iterator(endNode, m_nodes, m_values, this);
}

template <typename T>
void XSModExpTree<T>::swap (XSModExpTree<T>& right)
{
   std::swap(m_nodes, right.m_nodes);
   std::swap(m_values, right.m_values);
}

template <typename T>
typename XSModExpTree<T>::iterator XSModExpTree<T>::postBegin ()
{
   ExpTreeNodeType* beginNode = 0;
   if (m_nodes.size() > 1)
   {
      // We have a root, and root has a child.
      beginNode = &m_nodes[0];
   }
   return iterator(beginNode, m_nodes, m_values, this);
}

template <typename T>
typename XSModExpTree<T>::const_iterator XSModExpTree<T>::postBegin () const
{
   const ExpTreeNodeType* beginNode = 0;
   if (m_nodes.size() > 1)
   {
      // We have a root, and root has a child.
      beginNode = &m_nodes[0];
   }
   return const_iterator(beginNode, m_nodes, m_values, this);
}

template <typename T>
void XSModExpTree<T>::insertRoot (const IntegerArray& rootChildren)
{
   // Root must be inserted AFTER all other nodes.  This will
   // always make m_nodes.size() == m_values.size()+1 in a well
   // constructed tree.
   if (m_nodes.size() && m_nodes.size() == m_values.size())
   {
      ExpTreeNodeType newNode;
      newNode.pos = static_cast<int>(m_nodes.size());
      // parentPos will be set when this node's parent is
      // inserted into the tree.
      newNode.parentPos = -1;
      newNode.children = rootChildren;
      m_nodes.push_back(newNode);
      for (size_t i=0; i<rootChildren.size(); ++i)
      {
         m_nodes[rootChildren[i]].parentPos = newNode.pos;
      }
   }
   else
   {
      throw RedAlert("Improper root insertion attempt in ModExpTree.");
   }
}

template <typename T>
const IntegerArray& XSModExpTree<T>::getRoot () const
{
   if (!m_nodes.size())
   {
      throw RedAlert("Attempting to get root node of empty ModExpTree.");
   }
   return m_nodes[m_nodes.size()-1].children;
}

// Additional Declarations


#endif
