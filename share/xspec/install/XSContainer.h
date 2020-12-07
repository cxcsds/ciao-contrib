
#ifndef XSCONTAINER_H
#define XSCONTAINER_H


class XspecRegistry;
class Fit;
class PlotDirector;

namespace XSContainer
{
        class  ModelContainer;
        class  ResponseContainer;
        class  DataContainer;
        extern DataContainer* datasets;
        extern ModelContainer* models;
        extern ResponseContainer* responses;
        extern XspecRegistry* xsRegistry;
        extern Fit* fit;
	extern PlotDirector* plot;
}

#endif
