/**************************************************************************/
/* Browser.hpp                                                            */
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

/** @file Browser.hpp
 *  @brief Declares the one call that hands a link to whatever the desktop opens links with.
 *  @author Mustafa Garip
 */

#pragma once

#include <string>

namespace SushiHub
{
namespace Gui
{

/**
 * @brief Opens @p url in the desktop's registered handler for it.
 * @param url An absolute link; it is never passed through a shell.
 * @return Whether the desktop accepted the request, which is not whether a page appeared.
 */
bool open_in_browser(const std::string& url);

}
}
