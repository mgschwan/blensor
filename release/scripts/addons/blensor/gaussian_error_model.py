# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 22:25:13 2015

@author: mgschwan
"""

import numpy as np


class GaussianErrorModel:
  mu = 0.0
  sigma = 1.0
  def __init__(self,mu,sigma):
    self.mu = mu
    self.sigma = sigma

  def drawErrorFromModel(self,dist):
    if self.sigma < 0.0000001:
      return self.mu
    return np.random.normal(self.mu,self.sigma) 
