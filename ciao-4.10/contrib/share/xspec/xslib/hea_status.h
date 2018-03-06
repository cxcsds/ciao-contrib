#ifndef HEASTATUS_H
#define HEASTATUS_H
/*  Reset the error status */
    void ResetHEAStatus();      

/*  Set the non-zero error status. For the zero status, do nothing.    
    If you try to set the status to zero, call the ResetHEAStatus
    instead. */
    void SetHEAStatus(int status);      

/*  Get the error status */   
    int GetHEAStatus(int *status);      

/*  Check the error status. If it is an error, then exit it imediately. */   
    void HEATermination(); 
#endif     
