/**************************************************************************/
/* FixtureFile.hpp                                                        */
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

/** @file FixtureFile.hpp
 *  @brief Declares the readers every suite uses to load a file from tests/fixtures.
 *  @author Mustafa Garip
 */

#pragma once

#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace SushiHub
{
namespace GuiTests
{

/** @brief Returns the whole text of @p relative_path under the fixture directory. */
inline std::string fixture_text(const std::string& relative_path)
{
    const std::string full_path = std::string(SUSHIHUB_GUI_FIXTURE_DIR) + "/" + relative_path;
    std::ifstream file(full_path, std::ios::binary);
    std::ostringstream contents;
    contents << file.rdbuf();
    return contents.str();
}

/** @brief Returns the non-empty lines of @p relative_path under the fixture directory. */
inline std::vector<std::string> fixture_lines(const std::string& relative_path)
{
    std::istringstream text(fixture_text(relative_path));
    std::vector<std::string> lines;
    std::string line;
    while (std::getline(text, line))
    {
        if (!line.empty() && line.back() == '\r')
        {
            line.pop_back();
        }
        if (!line.empty())
        {
            lines.push_back(line);
        }
    }
    return lines;
}

}
}
