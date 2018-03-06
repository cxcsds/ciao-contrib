//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef SFDATA_H
#define SFDATA_H 1

// DataSet
#include <XSModel/Data/DataSet.h>
// SfIO
#include <XSModel/DataFactory/SfIO.h>

//	The old sf format data.



class SfData : public DataSet, //## Inherits: <unnamed>%3AA906A0035A
               	public SfIO  //## Inherits: <unnamed>%3BF52EB302A7
{

  public:
      SfData();

      SfData(const SfData &right);
      virtual ~SfData();

      virtual SfData* clone () const;
      //	type() returns true if the input filename is of the
      //	format corresponding to the class.
      bool fileFormat (const string& fileName, XspecDataIO::DataType type = XspecDataIO::SpectrumType);
      virtual void initialize (DataPrototype* proto, DataInputRecord& record);
      void closeSourceFiles ();
      virtual void reportResponse (size_t row) const;
      virtual void initializeFake (DataPrototype* proto, FakeDataInputRecord& record);
      virtual void outputData ();
      virtual std::pair<string,size_t>  getBackCorrLocation (size_t rowNum, bool isCorr = false) const;
      virtual FakeDataInputRecord::Detectors getResponseName (size_t rowNum) const;
      virtual FakeDataInputRecord::Arfs getAncillaryLocation (size_t rowNum, const FakeDataInputRecord::Detectors& respInfo) const;

    // Additional Public Declarations

  protected:
      virtual void setArrays (size_t row = 0);
      virtual void scaleArrays (size_t row = 0);
      virtual void setDescription (size_t spectrumNumber, size_t row = 0);
      //	Abstract function to be called by setData.
      //
      //	Invokes methods that instantiate ancilliary
      //	datasets in the case of DataSet and Response
      //	classes.
      //
      //	Default implementation is to do nothing.
      virtual bool setAncillaryData (size_t row = 0, int ancRow = -1);

    // Additional Protected Declarations

  private:
      SfData & operator=(const SfData &right);

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class SfData 


#endif
