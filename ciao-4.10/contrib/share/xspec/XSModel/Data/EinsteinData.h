//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef EINSTEINDATA_H
#define EINSTEINDATA_H 1

// DataSet
#include <XSModel/Data/DataSet.h>
// EinsteinIO
#include <XSModel/DataFactory/EinsteinIO.h>

//	Dataset specific implementation for Einstein CD-ROM
//	fits format data



class EinsteinData : public DataSet, //## Inherits: <unnamed>%3AA906A5037B
                     	public EinsteinIO  //## Inherits: <unnamed>%3BF52E9B029C
{

  public:
      EinsteinData();

      EinsteinData(const EinsteinData &right);
      virtual ~EinsteinData();

      virtual EinsteinData* clone () const;
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
      EinsteinData & operator=(const EinsteinData &right);

      virtual void defineArrays ();
      virtual void groupQuality ();

    // Additional Private Declarations

  private: //## implementation
    // Additional Implementation Declarations

};

// Class EinsteinData 


#endif
