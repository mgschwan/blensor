#Taken from http://www.siafoo.net/snippet/229

from numpy import array, abs, arange, dot, int8, int32, float32, floor, fromfunction,\
                  hypot, ones, prod, random, indices, newaxis, poly1d


class PerlinNoise(object):

    def noise(self, coords):

        ijk = (floor(coords) + self.idx_ar).astype(int32)

        uvw = coords - ijk

        indexes = self.P[ijk[:,:, self.order - 1]]

        for i in range(self.order - 1):
            indexes = self.P[(ijk[:,:, i] + indexes) % len(self.P)]

        gradiens = self.G[indexes % len(self.G)]
#        gradiens = self.G[(ijk[:,:, 0] + indexes) % len(self.G)]
        
        res = (self.drop(abs(uvw)).prod(axis=2)*prod([gradiens, uvw], axis=0).sum(axis=2)).sum(axis=1)

        res[res > 1.0] = 1.0
        res[res < -1.0] = -1.0

        return ((res + 1)).astype(float32)

    def getData(self, scale=32.0):
        return self.noise(indices(self.size).reshape(self.order, 1, -1).T / scale)

    
    def __init__(self, size=None, n=None):

        n = n if n else  256        
        self.size = size if size else (256, 256)

        self.order = len(self.size)
        
        # Generate WAY more numbers than we need
        # because we are throwing out all the numbers not inside a unit
        # sphere.  Something of a hack but statistically speaking
        # it should work fine... or crash.
        G = (random.uniform(size=2*self.order*n)*2 - 1).reshape(-1, self.order)

        # GAH! How do I generalize this?!
        #length = hypot(G[:,i] for i in range(self.order))

        if self.order == 1:
            length = G[:,0]
        elif self.order == 2:
            length = hypot(G[:,0], G[:,1])
        elif self.order == 3:
            length = hypot(G[:,0], G[:,1], G[:,2])
        
        self.G = (G[length < 1] / (length[length < 1])[:,newaxis])[:n,]
        self.P = arange(n, dtype=int32)
        
        random.shuffle(self.P)
        
        self.idx_ar = indices(int32(2*ones(self.order)), dtype=int8).reshape(self.order, -1).T
        self.drop = poly1d((-6, 15, -10, 0, 0, 1.0))

