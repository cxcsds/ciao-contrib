//C++
#ifndef PROCESSMANAGER_H
#define PROCESSMANAGER_H 1

#include <xsTypes.h>
#include <map>
#include <vector>
#include <stdio.h>
#include <unistd.h>
#include <string>

struct TransferStruct
{
   TransferStruct():
      iValues(), dValues(), sValues(), status(0)
      {}
   std::vector<std::vector<int> > iValues;
   std::vector<std::vector<double> > dValues;
   std::vector<std::string> sValues;
   int status;            
};

class ParallelFunc
{
   public:
      ParallelFunc() {}
      virtual ~ParallelFunc() {}
      // This function is allowed to throw, though YellowAlerts will not
      //   propagate out of ProcessManager.  If this also wishes to prevent
      //   the remainder of the execution loop from occuring, it should
      //   set the output.status flag to a negative value prior to throwing. 
      virtual void execute(const bool isParallel, const TransferStruct& input,
                        TransferStruct& output) = 0;
};

struct Process
{
   // The child process id, as retained by the parent.
   pid_t pid;
   // File descriptor for the parent's end of the pipe (or socket).
   int fd;
   // Pointer to "file" opened on fd.
   FILE* fp;
   // This flag will be 'true' from the time the child process is sent
   // the signal to execute until all expected output values have been
   // retrieved.  It should be 'false' at ALL other times.
   bool resultsPending;
};

class ProcessManager
{
   public:
      // ProcessManager assumes ownership of childFunc.
      ProcessManager(ParallelFunc* childFunc, const string& contextName);
      ~ProcessManager();
      
      typedef std::map<int, TransferStruct> ParallelResults;
      
      // nRequestedProcs is the number of procs the calling code is
      //  requesting.  It may not get all of them, depending on the user's
      //  setting in s_maxProcs.  This may throw, but only after it kills
      //  all the child processes it created, and calls waitpid on each of them.
      void createProcesses(const int nRequestedProcs);
      // This can only throw a RedAlert.  But if the execute function has thrown
      //  AND set its corresponding output.status to a negative value, this will
      //  prevent the rest of the execution calls from occuring and set each of
      //  the remaining output.status flags negative.
      void run(const std::vector<TransferStruct>& input, ParallelResults& output);
      void killProcesses();
      const string& contextName() const;
      bool isParallel() const;
      
      static std::map<string,int>& maxProcs();
      static void initMaxProcsMap();
      
   private:
      ProcessManager(const ProcessManager& right);
      ProcessManager& operator=(const ProcessManager& right);
      void multiProcesses(const std::vector<TransferStruct>& input);
      // This gets executed when doParallel=false is passed to run().
      void singleProcess(const std::vector<TransferStruct>& input);
      // See description for m_processAssignments below.
      void setProcessAssignments(const size_t inputVecSize);
      // Pass execution info from m_processAssignments to the 
      //   individual child processes.  This releases them from
      //   the waiting state which they entered in createProcs.
      void startChildProcs();
      void getResults(ParallelResults& results);
      
      static void transferSend(const TransferStruct& outgoing, FILE* fp);
      static void transferReceive(TransferStruct& incoming, FILE* fp);
      
      // This vector should remain empty when in single-process mode, 
      //    ie. when m_doParallel is false.
      std::vector<Process> m_processes;
      ParallelFunc* const m_childFunc;
      ParallelResults m_singleProcResults;
      // When s_maxProcs is less than the vector size of input TransferStructs,
      //  processes will have to handle multiple calls to the execution
      //  function.  m_processAssignments will be resized to nProcs+1 where
      //  nProcs is the number of child processes.  Each element contains
      //  the 0-based starting index of the TransferStruct (with the nProc
      //  element containing one past the last index).
      //  It will not be resized or set when m_doParallel = false.
      std::vector<size_t> m_processAssignments;
      const string m_context;
      bool m_doParallel;
      
      // These values are sent through sockets via non-const pointers,
      //  which is why they are not consts (or enums for that matter).
      static size_t s_READY;
      static size_t s_QUIT;
      
      // Map entries <context>:<maxProcs> will be filled by xsParallel handler
      // If context is not found in map (as will happen if 'parallel' has never
      // been called by user), we will assume its maxProcs = 1.
      // The context names entered into this map ought to match the
      // names inserted into m_context for individual ProcessManager objects.
      static std::map<string,int> s_maxProcs;
};

inline const string& ProcessManager::contextName() const
{
   return m_context;
}

inline bool ProcessManager::isParallel() const
{
   return m_doParallel;
}

inline std::map<string,int>& ProcessManager::maxProcs()
{
   return s_maxProcs;
}

#endif
