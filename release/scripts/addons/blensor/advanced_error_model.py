# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 22:25:13 2015

@author: mgschwan
"""


"""Error measurements taken from 
ACCURATE SLAM WITH APPLICATION FOR AERIAL PATH PLANNING
Chen Friedman, 2013
src: http://www.inderjitchopra.umd.edu/documents/Friedman-PhD-2013.pdf

distance, average_error, 3sigma
2.0,0.0114,0.028
3.0,0.0165,0.024
4.5,0.00405,0.018
6.0,0.0072,0.03
9.0,0.0225,0.045
10.5,0.00735,0.0525
12.0,0.0048,0.06
15.0,0.0075,0.072
21.0,0.0021,0.09449
23.0,0.0161,0.0644
25.0,0.0075,0.05
29.0,0.0174,0.1015
30,0.0009,0.194999
"""

import numpy as np
import ast
try:
  import blensor
  from blensor import gaussian_error_model
except:
  """Standalone mode without blensor"""
  import gaussian_error_model




class AdvancedErrorModel(gaussian_error_model.GaussianErrorModel):
  """error profile over distance. A list of distance,mu,sigma tuples"""
  error_model = None
 
  def __init__(self, error_model_string):
    self.error_model = None
    try:
      em = ast.literal_eval(error_model_string)
      self.error_model = sorted (em,key = lambda x: x[0])
    except:
      pass
    if self.error_model is None:
      raise blensor.UserInfoException("Error in Advanced Error Model string")              

  def getErrorParams(self, dist):
      index = 0
      for idx,t in enumerate(self.error_model):
         if dist < t[0]: 
             break
         index = idx
         
      d_lower,mu_lower,sigma_lower = self.error_model[index]   

      """If we are at the last element we DO NOT extrapolate but use only
         the last element"""
      if index == len(self.error_model) -1:
          d_upper,mu_upper,sigma_upper= dist,mu_lower,sigma_lower
      else:
          d_upper,mu_upper,sigma_upper= self.error_model[index+1] 


      drange = float(d_upper-d_lower)
      if drange > 0.000001:
          dl = float(dist-d_lower)/drange
          du = float(d_upper-dist)/drange
          
          mu_combined = (1.0-dl)*mu_lower+(1.0-du)*mu_upper
          sigma_combined = (1.0-dl)*sigma_lower+(1.0-du)*sigma_upper
      else:
          mu_combined,sigma_combined = mu_lower,sigma_lower
      return mu_combined, sigma_combined

  def drawErrorFromModel(self,dist):
    mu,sigma = self.getErrorParams(dist)
    if sigma < 0.0000001:
      return mu
    return(np.random.normal(mu,sigma))
    
    

if __name__=="__main__":
    import matplotlib.pylab as plt
    
    model = AdvancedErrorModel("[(2.0, 0.0, 0.009333333333333334), (3.0, 0.0, 0.008),(4.5, 0.0, 0.005999999999999999), (6.0, 0.0, 0.01), (9.0, 0.0, 0.015),(10.5, 0.0, 0.017499999999999998), (12.0, 0.0, 0.02),(15.0, 0.0, 0.023999999999999997), (21.0, 0.0, 0.031496666666666666), (23.0, 0.0, 0.021466666666666665), (25.0, 0.0, 0.016666666666666666), (29.0, 0.0, 0.03383333333333333), (30, 0.0, 0.06499966666666666)]")

    nr_samples = 100
    
    distances = np.arange(0,30,0.1)
    error_parameters = np.array([model.getErrorParams(x) for x in distances])
    
    mus = np.tile(error_parameters[:,0],(nr_samples,1))
    sigmas = np.tile(error_parameters[:,1],(nr_samples,1))
    
    errors = np.abs(np.random.normal(mus,sigmas))
    
    mean_errors = np.array([np.mean(errors[:,x]) for x in range(errors.shape[1])])
    plt.xlabel("Distance (m)")
    plt.ylabel("Mean error (mm)")
    plt.plot(distances, 100*mean_errors)
    plt.show()


