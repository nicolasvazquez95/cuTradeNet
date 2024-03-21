import numpy as np
from numba import cuda
from numba.cuda.random import create_xoroshiro128p_states
from time import time 
from . Utils import GraphManager as gm
from . Utils import ExceptionsManager as EM
import igraph as ig
from networkx import Graph as nxGraph