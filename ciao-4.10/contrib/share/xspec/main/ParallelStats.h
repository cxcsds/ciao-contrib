//C++

#ifndef PARALLELSTATS_H
#define PARALLELSTATS_H 1

#include <XSUtil/Utils/ProcessManager.h>

class ParallelStats : public ParallelFunc
{
   public:
         virtual void execute(const bool isParallel, const TransferStruct& input,
                        TransferStruct& output);
   private:
};



#endif
