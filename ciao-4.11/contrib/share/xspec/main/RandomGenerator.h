//   Read the documentation to learn more about C++ code generator
//   versioning.
//	  %X% %Q% %Z% %W%

#ifndef RANDOMGENERATOR
#define RANDOMGENERATOR 1

// RandomLuxAdapter
#include <XSUtil/Numerics/RandomLuxAdapter.h>
#include <xsTypes.h>

namespace Numerics {
    void GaussRand(RealArray& gaussSamples);
    void PoissonRand(RealArray& poissonMeans);
    void UniformRand(RealArray& randomNumbers);
    void CauchyRand(RealArray& randomNumbers);



    template <typename T>
    class RandomGenerator 
    {

      public:
          ~RandomGenerator();

          static RandomGenerator<T>& instance ();
          void initialize ();
          void getRandom (std::vector<Real>& randNumbers) const;
          void getRandom (float* randNumbers, int length) const;
          void getRandom (Real* randNumbers, int length) const;
          int seed () const;
          void seed (int value);
          const std::vector<Real>& parHooks () const;
          void parHooks (const std::vector<Real>& value);

        // Additional Public Declarations

      protected:
          RandomGenerator();

        // Additional Protected Declarations

      private:
          RandomGenerator(const RandomGenerator< T > &right);
          RandomGenerator< T > & operator=(const RandomGenerator< T > &right);

        // Additional Private Declarations

      private: //## implementation
        // Data Members for Class Attributes
          int m_seed;
          std::vector<Real> m_parHooks;
          T* m_generator;

        // Additional Implementation Declarations

    };



    typedef RandomGenerator< Numerics::RandomLuxAdapter  > DefaultRandomGenerator;

    // Parameterized Class Numerics::RandomGenerator 

    template <typename T>
    inline int RandomGenerator<T>::seed () const
    {
      return m_seed;
    }

    template <typename T>
    inline void RandomGenerator<T>::seed (int value)
    {
      m_seed = value;
    }

    template <typename T>
    inline const std::vector<Real>& RandomGenerator<T>::parHooks () const
    {
      return m_parHooks;
    }

    template <typename T>
    inline void RandomGenerator<T>::parHooks (const std::vector<Real>& value)
    {
      m_parHooks = value;
    }

    // Parameterized Class Numerics::RandomGenerator 

    template <typename T>
    RandomGenerator<T>::RandomGenerator()
    {
       m_generator = new T;
    }


    template <typename T>
    RandomGenerator<T>::~RandomGenerator()
    {
       // Remember this is a Meyers Singleton.  Destruction must NOT 
       // depend on existence of any other Singletons. 
       delete m_generator; 
    }


    template <typename T>
    RandomGenerator<T>& RandomGenerator<T>::instance ()
    {
       // The Meyers variation of the Singleton pattern.
       static RandomGenerator<T> randomGenerator;
       return randomGenerator;
    }

    template <typename T>
    void RandomGenerator<T>::initialize ()
    {
         m_generator->initialize(m_seed, m_parHooks);
    }

    template <typename T>
    void RandomGenerator<T>::getRandom (std::vector<Real>& randNumbers) const
    {
       m_generator->getRandom(randNumbers, m_parHooks);
    }

    template <typename T>
    void RandomGenerator<T>::getRandom (float* randNumbers, int length) const
    {
       m_generator->getRandom(randNumbers, length, m_parHooks);
    }

    template <typename T>
    void RandomGenerator<T>::getRandom (Real* randNumbers, int length) const
    {
       m_generator->getRandom(randNumbers, length, m_parHooks);
    }

    // Additional Declarations

} // namespace Numerics


#endif
