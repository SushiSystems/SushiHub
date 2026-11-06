/**************************************************************************/
/* ProgressBar.cpp                                                        */
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

/** @file ProgressBar.cpp
 *  @brief Defines the completed fraction a progress event is drawn with and its overlay.
 *  @author Mustafa Garip
 */

#include "ui/widgets/ProgressBar.hpp"

#include <imgui.h>

#include <algorithm>
#include <cfloat>
#include <string>

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

namespace
{

/** @brief Returns the completed fraction of @p progress, clamped to the drawable range. */
float completed_fraction(const ProgressEvent& progress)
{
    double fraction = 0.0;
    if (progress.fraction.has_value())
    {
        fraction = *progress.fraction;
    }
    else if (progress.count > 0)
    {
        fraction = static_cast<double>(progress.index) / static_cast<double>(progress.count);
    }
    return static_cast<float>(std::min(std::max(fraction, 0.0), 1.0));
}

/** @brief Returns the text drawn over the bar: the step and, when known, its position. */
std::string overlay_text(const ProgressEvent& progress)
{
    if (progress.count <= 0)
    {
        return progress.label;
    }
    return progress.label + " (" + std::to_string(progress.index) + "/" +
           std::to_string(progress.count) + ")";
}

}

void draw_progress(const ProgressEvent& progress)
{
    const std::string overlay = overlay_text(progress);
    ImGui::ProgressBar(completed_fraction(progress), ImVec2(-FLT_MIN, 0.0F), overlay.c_str());
}

}
}
}
