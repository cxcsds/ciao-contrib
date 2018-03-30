// C++

#ifndef MODELSETUP_H
#define MODELSETUP_H

#include<vector>
#include<string>
#include<iosfwd>
#include <utility> // for std::pair

std::string lowerCase(const std::string& inputString);


std::string expandDirectoryPath (const std::string& input);


std::vector<std::string> getCodeList(const std::string& dir, const std::string& suffix);

void writeMakefile(const std::string& dir, const std::string& packageName, bool isStatic, bool isRandomize);

typedef std::vector<std::pair<std::string,std::string> > ClassInfoContainer;

int checkPreExistingFiles(const std::string& dir, const std::string& packageName, std::string& existingName);
int checkForInitFile(const std::string& dir, const std::string& modInitFile, std::string& fullModelInitFile);
void addUdmgetFiles(const std::string& dir, bool is64);
void createFunctionMapFiles(const std::string& dir, const std::string& packageName,
                const std::string& fullModelInitFile);
void createPackageInitFile(const std::string& dir, const std::string& packageName, 
        const std::string& fullModelInitFile, const ClassInfoContainer& classes, bool isStatic);
void processRandomizerDat(const std::string& fullDatFile, ClassInfoContainer& classes);
void createTclPkgIndex(const string& directory, const string& packageName);
#endif
