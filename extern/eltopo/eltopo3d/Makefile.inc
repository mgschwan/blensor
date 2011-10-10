
# Source files
LIB_SRC = accelerationgrid.cpp broadphasegrid.cpp dynamicsurface.cpp \
          nondestructivetrimesh.cpp subdivisionscheme.cpp surftrack.cpp \
          eltopo.cpp

# Common
LIB_SRC += ../common/collisionqueries.cpp ../common/wallclocktime.cpp \
           ../common/newsparse/sparse_matrix.cpp \
           ../common/newsparse/krylov_solvers.cpp \
           ../common/cubic_ccd_wrapper.cpp \

# object files
LIB_RELEASE_OBJ = $(patsubst %.cpp,obj/%.o,$(notdir $(LIB_SRC)))
LIB_DEBUG_OBJ = $(patsubst %.cpp,obj_debug/%.o,$(notdir $(LIB_SRC)))

# Build the library
$(LIBRARY)_release.a: $(LIB_RELEASE_OBJ)
	ar r $@ $(LIB_RELEASE_OBJ)
	ranlib $@
		  
$(LIBRARY)_debug.a: $(LIB_DEBUG_OBJ)
	ar r $@ $(LIB_DEBUG_OBJ)
	ranlib $@

