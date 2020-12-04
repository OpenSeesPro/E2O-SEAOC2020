# E2O-SEAOC2020
#### Python source code accompanying the Goings et al. (2020) paper published in the SEAOC 2020 proceedings

Hi fellow engineers! This is an open-source library of Python functions for converting the ETABS model included within the `models` directory into a nonlinear OpenSees equivalent and running a response history analysis on the nonlinear OpenSees model.
The ideas implemented in this library are readily extensible to other ETABS models developed with the methodology explained in our paper. However, we 
currently limit the scope of this library to the enclosed model.

#### Recommended steps to use this library:

1. Fork this repository to your GitHub account and clone to your machine. 
2. Run the enclosed ETABS model and keep ETABS open in the background as you work on Step 3 and beyond.
3. Use your favorite Python distribution and IDE to run the `main.py` script. We recommend using Spyder, which is included in the [Anaconda3-2019.10](https://repo.anaconda.com/archive/) distribution. Newer Anaconda3 distributions have issues interfacing with ETABS.

If you use the Anaconda3 distribution noted above, you may need to also manually install Python packages which are not included in the Anaconda3 distribution but are noted as dependencies below. We recommend Using `pip` on the Anaconda Powershell for manually installing packages.

#### Add-on dependency packages required to use this library:
  - [OpenSeesPy](https://openseespydoc.readthedocs.io/en/latest/index.html) **not included in Anaconda3-2019.10** ([installation tutorial](https://www.youtube.com/watch?v=uuhuewl1Z-k))
  - [Pandas](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html) `included in Anaconda3-2019.10`
  - [comtypes](https://pypi.org/project/comtypes/) `included in Anaconda3-2019.10`
  - [numpy](https://numpy.org/install/) `included in Anaconda3-2019.10`
  - [tqdm](https://pypi.org/project/tqdm/) **not included in Anaconda3-2019.10** (installation similar to OpenSeesPy tutorial)
  
If you would like to propose changes, please submit a pull requests from your fork.

#### Helpful links to learn more about GitHub workflow:

  - [Forks](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-forks)
  - [Pull Requests](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests)
  - [Creating Pull Requests from Forks](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork)
  
Feel free to submit bugs or ideas for enhancements as [issues](https://guides.github.com/features/issues/) directly to this repository.

Thanks for your interest in this library!
