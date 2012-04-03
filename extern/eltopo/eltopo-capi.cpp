#include "common/vec.h"
#include "ccd_wrapper.h"
#include "cfloat"
#include "../../source/blender/blenlib/BLI_memarena.h"
// --------------------------------------------------------------------------------------------------
// Continuous collision detection
// --------------------------------------------------------------------------------------------------

MemArena *arena = NULL;

/*overload default new operator*/
void *operator new(size_t size) {
	if (arena)
		return BLI_memarena_alloc(arena, size);
	else
		return malloc(size);
}

void operator delete(void *ptr) {
	if (!arena)
		free(ptr);
}

extern "C" void eltopo_start_memarena(void)
{
	arena = BLI_memarena_new(1<<18, "eltopo arena");	
}

extern "C" void eltopo_end_memarena(void)
{
	if (arena) {
		BLI_memarena_free(arena);
		arena = NULL;
	}
}
