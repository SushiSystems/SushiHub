/**************************************************************************/
/* TitleBar.hpp                                                           */
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

/** @file TitleBar.hpp
 *  @brief Declares the row at the top of the window that names the application and the workspace.
 *  @author Mustafa Garip
 */

#pragma once

#include <string>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the application's identity, the open workspace and the signed-in account. */
class TitleBar
{
public:
    /**
     * @brief Draws one row carrying the name, @p version, @p workspace in a chip and @p account.
     * @param version The version `hub --describe` reports, or empty while it is being read.
     * @param workspace The path the window is open on, shown as it was given.
     * @param account The signed-in identity, or an empty string when nobody is signed in.
     */
    void draw(const std::string& version, const std::string& workspace,
              const std::string& account);

    /** @brief Returns the row's height in pixels at the current font size. */
    static float height();
};

}
}
