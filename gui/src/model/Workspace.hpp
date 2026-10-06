/**************************************************************************/
/* Workspace.hpp                                                          */
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

/** @file Workspace.hpp
 *  @brief Declares the one run per screen and the refresh that replaces it.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/CommandRun.hpp"

#include <functional>
#include <map>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Keeps one started CommandRun per screen and hands it to whoever draws that screen. */
class Workspace
{
public:
    /** @brief Binds the workspace to the `hub` executable every run is spawned from. */
    explicit Workspace(std::string hub_executable);

    /** @brief Returns the run for @p screen, starting it the first time it is asked for. */
    CommandRun& run_for(std::string_view screen);

    /** @brief Throws away the run for @p screen and starts a fresh one. */
    void refresh(std::string_view screen);

    /** @brief Returns the `hub` executable every run is spawned from. */
    const std::string& executable() const;

private:
    /** @brief Builds the argument vector that asks `hub` for @p screen as JSON. */
    std::vector<std::string> argv_for(std::string_view screen) const;

    /** @brief Starts a fresh run for @p screen and returns it. */
    CommandRun& open(std::string_view screen);

    /** @brief Holds the `hub` executable, however the caller found it. */
    std::string hub_executable_;

    /** @brief Holds one run per screen name, keyed so a string_view looks one up. */
    std::map<std::string, std::unique_ptr<CommandRun>, std::less<>> runs_;
};

}
}
