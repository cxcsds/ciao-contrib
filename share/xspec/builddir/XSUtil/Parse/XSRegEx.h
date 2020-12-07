#ifndef XSREGEX_H
#define XSREGEX_H

#include <iostream>
#include <vector>

using namespace std;

template <typename MatchEngine>
class XSRegEx : public MatchEngine {
 public:
    XSRegEx(const string& s);
};

template <typename MatchEngine>
XSRegEx<MatchEngine>::XSRegEx(const string& s) : MatchEngine(s)
{
}

#endif
