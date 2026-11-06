/**************************************************************************/
/* ProgressBar.hpp                                                        */
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

/** @file ProgressBar.hpp
 *  @brief Declares the bar one progress event is drawn as.
 *  @author Mustafa Garip
 */

#pragma once

#include "contract/Event.hpp"

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

/**
 * @brief Draws @p progress as a bar labelled with its step and its position in the run.
 * @param progress The latest step; its fraction is used when it carries one, its
 *        position among the steps otherwise.
 */
void draw_progress(const ProgressEvent& progress);

}
}
}
