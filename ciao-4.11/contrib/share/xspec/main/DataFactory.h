//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef DATAFACTORY_H
#define DATAFACTORY_H 1


class DataSet;
class BackCorr;
class Response;
typedef BackCorr Correction;
typedef BackCorr Background;

//	Class implementing an abstract Factory for datasets
//	and their associated files.



class DataFactory 
{

  public:
      virtual ~DataFactory();

      virtual DataSet* MakeDataSet () const = 0;
      virtual Response* MakeResponse () const = 0;
      virtual Background* MakeBackground () const = 0;
      virtual Correction* MakeCorrection () const = 0;

    // Additional Public Declarations

  protected:
      DataFactory();

    // Additional Protected Declarations

  private:
      DataFactory(const DataFactory &right);
      DataFactory & operator=(const DataFactory &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};
//	Data Prototype class. Has pointers to concrete objects.



class DataPrototype : public DataFactory  //## Inherits: <unnamed>%39A3D64A01CB
{
  public:
      DataPrototype(const DataPrototype &right);
      DataPrototype (DataSet* pDataSet, Response* pResponse, Background* pBackground, Correction* pCorrection = 0);
      virtual ~DataPrototype();
      DataPrototype & operator=(const DataPrototype &right);

      virtual DataSet* MakeDataSet () const;
      virtual Response* MakeResponse () const;
      virtual Background* MakeBackground () const;
      virtual Correction* MakeCorrection () const;

  protected:
  private:
      void swap (DataPrototype& right) throw ();
      Background* protoBackground ();
      void protoBackground (Background* value);
      Correction* protoCorrection ();
      void protoCorrection (Correction* value);
      DataSet* protoDataSet ();
      void protoDataSet (DataSet* value);
      Response* protoResponse ();
      void protoResponse (Response* value);

  private: //## implementation
    // Data Members for Associations
      Background* m_protoBackground;
      Correction* m_protoCorrection;
      DataSet* m_protoDataSet;
      Response* m_protoResponse;
    friend class XspecRegistry;
};

// Class DataFactory 

// Class DataPrototype 

inline Background* DataPrototype::protoBackground ()
{
  return m_protoBackground;
}

inline void DataPrototype::protoBackground (Background* value)
{
  m_protoBackground = value;
}

inline Correction* DataPrototype::protoCorrection ()
{
  return m_protoCorrection;
}

inline void DataPrototype::protoCorrection (Correction* value)
{
  m_protoCorrection = value;
}

inline DataSet* DataPrototype::protoDataSet ()
{
  return m_protoDataSet;
}

inline void DataPrototype::protoDataSet (DataSet* value)
{
  m_protoDataSet = value;
}

inline Response* DataPrototype::protoResponse ()
{
  return m_protoResponse;
}

inline void DataPrototype::protoResponse (Response* value)
{
  m_protoResponse = value;
}


#endif
