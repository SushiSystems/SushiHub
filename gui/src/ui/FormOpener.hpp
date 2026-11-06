/**************************************************************************/
/* FormOpener.hpp                                                         */
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

/** @file FormOpener.hpp
 *  @brief Declares the seam a screen asks the shell to show one command's form through.
 *  @author Mustafa Garip
 */

#pragma once

#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Accepts a screen's request to show the generated form of one command. */
class FormOpener
{
public:
    virtual ~FormOpener() = default;

    /**
     * @brief Shows @p command's form with @p arguments already entered.
     * @param command The catalogue name of the command; an unknown one is ignored.
     * @param arguments Values for the command's positional arguments, in declaration order.
     */
    virtual void open_form(const std::string& command,
                           const std::vector<std::string>& arguments) = 0;
};

}
}
