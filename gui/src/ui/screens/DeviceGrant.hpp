/**************************************************************************/
/* DeviceGrant.hpp                                                        */
/**************************************************************************/
/*                          This file is part of:                         */
/*                                SushiHub                                */
/*                https://github.com/SushiSystems/SushiHub                */
/*                         https://sushisystems.io                        */
/**************************************************************************/
/* Copyright (c) 2026-present Mustafa Garip & Sushi Systems               */
/*                                                                        */
/* Licensed under the PolyForm Noncommercial License 1.0.0 (the           */
/* "License"); you may not use this file except in compliance with the    */
/* License. You may obtain a copy of the License at                       */
/*                                                                        */
/*     https://polyformproject.org/licenses/noncommercial/1.0.0           */
/*                                                                        */
/* Noncommercial use is free. Commercial use requires a separate licence  */
/* from Sushi Systems; see COMMERCIAL.md. The software is provided        */
/* "as is", without warranty of any kind.                                 */
/**************************************************************************/

/** @file DeviceGrant.hpp
 *  @brief Declares what a person needs to approve a sign-in and how a run is read for it.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/RunState.hpp"

#include <string>

namespace SushiHub
{
namespace Gui
{

/** @brief Holds one sign-in in flight: the code a person types and the page to type it on. */
struct DeviceGrant
{
    /** @brief Holds the code the person types, empty until the run has shown one. */
    std::string user_code;

    /** @brief Holds the page the code is typed on, empty until the run has shown one. */
    std::string verification_uri;
};

/**
 * @brief Reads the grant out of what a sign-in run has produced so far.
 * @param state The run's state; the result payload's own fields win over its messages.
 * @return The code and the page, either field empty when the run has not shown it.
 */
DeviceGrant read_device_grant(const RunState& state);

}
}
