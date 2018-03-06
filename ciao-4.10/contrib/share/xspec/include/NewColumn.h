//	Astrophysics Science Division,
//	NASA/ Goddard Space Flight Center
//	HEASARC
//	http://heasarc.gsfc.nasa.gov
//	e-mail: ccfits@legacy.gsfc.nasa.gov
//
//	Original author: Ben Dorman

#ifndef NEWCOLUMN_H
#define NEWCOLUMN_H 1

// valarray
#include <valarray>
// ColumnCreator
#include "ColumnCreator.h"
// FITSUtil
#include "FITSUtil.h"


namespace CCfits {



  template <typename T>
  class NewColumn : public ColumnCreator  //## Inherits: <unnamed>%394167D103C5
  {

    public:
        NewColumn (vector<T>& data);
        virtual ~NewColumn();

      // Additional Public Declarations

    protected:
        virtual Column* MakeColumn (const int index, const string &name, const string &format, const string &unit, const long repeat, const long width, const string &comment = "", const int decimals = 0);

      // Additional Protected Declarations

    private:
        NewColumn(const NewColumn< T > &right);
        NewColumn< T > & operator=(const NewColumn< T > &right);

      // Additional Private Declarations

    private: //## implementation
      // Additional Implementation Declarations

  };



  template <typename T>
  class NewVectorColumn : public ColumnCreator  //## Inherits: <unnamed>%394167CE0009
  {

    public:
        NewVectorColumn (std::vector<std::valarray<T> >& data);
        virtual ~NewVectorColumn();

      // Additional Public Declarations

    protected:
        virtual Column * MakeColumn (const int index, const string &name, const string &format, const string &unit, const long repeat, const long width, const string &comment = "", const int decimals = 0);

      // Additional Protected Declarations

    private:
        NewVectorColumn(const NewVectorColumn< T > &right);
        NewVectorColumn< T > & operator=(const NewVectorColumn< T > &right);

      // Additional Private Declarations

    private: //## implementation
      // Additional Implementation Declarations

  };

  // Parameterized Class CCfits::NewColumn 

  // Parameterized Class CCfits::NewVectorColumn 

  // Parameterized Class CCfits::NewColumn 

  template <typename T>
  NewColumn<T>::NewColumn (vector<T>& data)
     : m_newData(data)
  {
  }


  template <typename T>
  NewColumn<T>::~NewColumn()
  {
  }


  template <typename T>
  Column* NewColumn<T>::MakeColumn (const int index, const string &name, const string &format, const string &unit, const long repeat, const long width, const string &comment, const int decimals)
  {
   FITSUtils::MatchType<T> findType;


   ColumnData<T>* newColumn = new ColumnData(index,name,findType(),format,unit,p,repeat,width,comment);  
   newColumn->data(m_newData);
   return newColumn;   
  }

  // Additional Declarations

  // Parameterized Class CCfits::NewVectorColumn 

  template <typename T>
  NewVectorColumn<T>::NewVectorColumn (std::vector<std::valarray<T> >& data)
  {
  }


  template <typename T>
  NewVectorColumn<T>::~NewVectorColumn()
  {
  }


  template <typename T>
  Column * NewVectorColumn<T>::MakeColumn (const int index, const string &name, const string &format, const string &unit, const long repeat, const long width, const string &comment, const int decimals)
  {
  }

  // Additional Declarations

} // namespace CCfits


#endif
