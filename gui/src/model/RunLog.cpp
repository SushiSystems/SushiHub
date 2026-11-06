/**************************************************************************/
/* RunLog.cpp                                                             */
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

/** @file RunLog.cpp
 *  @brief Defines the adoption of a run and the reads the activity strip makes.
 *  @author Mustafa Garip
 */

#include "model/RunLog.hpp"

#include <utility>

namespace SushiHub
{
namespace Gui
{

void RunLog::adopt(CommandRun& run, std::string label)
{
    run_ = &run;
    label_ = std::move(label);
}

bool RunLog::has_run() const
{
    return run_ != nullptr;
}

CommandRun& RunLog::run()
{
    return *run_;
}

const std::string& RunLog::label() const
{
    return label_;
}

}
}
