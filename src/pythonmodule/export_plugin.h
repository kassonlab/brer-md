//
// Created by Eric Irrgang on 11/3/17.
//

#ifndef HARMONICRESTRAINT_EXPORT_PLUGIN_H
#define HARMONICRESTRAINT_EXPORT_PLUGIN_H

#include "gmxapi/md.h"
#include "gmxapi/md/mdmodule.h"

namespace gmxpy
{
/*!
 * \brief Wrapper for pluggable MD modules.
 */
class PyMDModule
{
    public:
        std::shared_ptr<gmxapi::MDModule> module;
};
} // end namespace gmxpy

#endif //HARMONICRESTRAINT_EXPORT_PLUGIN_H
