#!/usr/bin/env python
# coding: utf-8

# In[2]:


import numpy as np

def gaussian_plusline(x,mu,sig,A,alpha,beta):
    return alpha+x*beta+(A/np.sqrt(2*np.pi)/sig)*np.exp(-(x-mu)**2/2/sig**2)
def gaussian(x,mu,sig,A):
    return (A/np.sqrt(2*np.pi)/sig)*np.exp(-(x-mu)**2/2/sig**2)

