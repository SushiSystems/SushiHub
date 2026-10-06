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
