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
/* Licensed under the Apache License, Version 2.0 (the "License"); you    */
/* may not use this file except in compliance with the License. You may   */
/* obtain a copy of the License at                                        */
/*                                                                        */
/*     https://www.apache.org/licenses/LICENSE-2.0                        */
/*                                                                        */
/* Unless required by applicable law or agreed to in writing, software    */
/* distributed under the License is distributed on an "AS IS" BASIS,      */
/* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or        */
/* implied. See the License for the specific language governing           */
/* permissions and limitations under the License.                         */
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
