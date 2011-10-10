/** \file itasc/WorldObject.cpp
 *  \ingroup itasc
 */
/* $Id: WorldObject.cpp 35155 2011-02-25 11:45:16Z jesterking $
 * WorldObject.cpp
 *
 *  Created on: Feb 10, 2009
 *      Author: benoitbolsee
 */

#include "WorldObject.hpp"

namespace iTaSC{

/* special singleton to be used as base for uncontrolled object */
WorldObject Object::world;

WorldObject::WorldObject():UncontrolledObject()
{
	initialize(0,1);
	m_internalPose = Frame::Identity();
}

WorldObject::~WorldObject() 
{
}


}
