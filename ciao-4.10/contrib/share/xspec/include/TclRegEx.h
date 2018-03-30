//C++
#ifndef TCLREGEX_H
#define TCLREGEX_H

#include <string>
#include <tcl.h>
#include <vector>
#include <iterator>
#include <XSUtil/Error/Error.h>

using namespace std;

class BadExpression : public RedAlert {
 public:
    BadExpression(const string& s, int errCode);
};

inline BadExpression::BadExpression(const string& s, int errCode) 
    : RedAlert(s, errCode) 
{
}

class match_results;

class TclRegEx {
 public:
    typedef match_results result_type;

    TclRegEx(const string& = "");
    ~TclRegEx();

   // Returns 1 if s contains a match of reg exp, 0 if no match, -1 if error.
   // Results are stored in matches container, where the first element applies 
   // to the entire match and the rest refer to the capturing parenthesized 
   // subexpressions.
    bool regex_search(const string& s, result_type& matches, int flags = 0);
    bool regex_search(string::const_iterator beg, string::const_iterator end,
		      result_type& matches, int flags = 0);

   // Calls Tcl's regsub function, returns inString but with every
   // part that matches reg exp replaced with substString.                  
    string regSub(const string& inString, const string& substString);
    static const string& REAL();
    static const int match_not_bol = TCL_REG_NOTBOL;
 private:
    Tcl_RegExp m_regexp;
    Tcl_Interp* m_interp;
    string m_strExp;
    static const string s_REAL;

 private:
    TclRegEx(const TclRegEx& right);
    TclRegEx& operator=(const TclRegEx& right);
    bool createExpFromType(const string& exp);
};

// This class corresponds to the capturing parenthesized subexpressions in the reg exp.
class sub_match {
 private:
    sub_match();
 public:
    // Returns the string of portion matched, empty if not matched.
    string str() const;

    bool matched;
    // Iterators to the portion matched, second points to 1 beyond the
    // last character in the match.
    string::const_iterator first;
    string::const_iterator second;

    friend class match_results;
    friend class TclRegEx;
};

class match_results {
 public:
    // size() = 1 + number of capturing parenthesized subexpressions in reg ex.
    // The zero element refers to the ENTIRE match, indices 1 through size()-1
    // are the subexpressions.
    sub_match operator[] (int index);
    void subs(const vector<sub_match> & match_info);
    size_t size() const;
    void clear();

 private:
    vector<sub_match> m_subs;
};

inline sub_match::sub_match() 
{
}

inline string sub_match::str() const
{
    return (matched ? string(first, second) : string(""));
}

inline sub_match match_results::operator [] (int index)
{
    return m_subs[index];
}

inline void match_results::subs(const vector<sub_match>& match_info) 
{
    m_subs = match_info;
}

inline size_t match_results::size() const {
    return m_subs.size();
}

inline void match_results::clear() {
    m_subs.clear();
}

inline const string& TclRegEx::REAL()
{
   return s_REAL;
}
#endif
