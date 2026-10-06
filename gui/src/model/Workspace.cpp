/**************************************************************************/
/* Workspace.cpp                                                          */
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

/** @file Workspace.cpp
 *  @brief Defines the per-screen run cache and the argument vector each screen asks for.
 *  @author Mustafa Garip
 */

#include "model/Workspace.hpp"

#include <utility>

namespace SushiHub
{
namespace Gui
{

Workspace::Workspace(std::string hub_executable)
    : hub_executable_(std::move(hub_executable))
{
}

CommandRun& Workspace::run_for(std::string_view screen)
{
    const auto found = runs_.find(screen);
    if (found != runs_.end())
    {
        return *found->second;
    }
    return open(screen);
}

void Workspace::refresh(std::string_view screen)
{
    const auto found = runs_.find(screen);
    if (found != runs_.end())
    {
        runs_.erase(found);
    }
    open(screen);
}

const std::string& Workspace::executable() const
{
    return hub_executable_;
}

std::vector<std::string> Workspace::argv_for(std::string_view screen) const
{
    return {hub_executable_, "--json", std::string(screen)};
}

CommandRun& Workspace::open(std::string_view screen)
{
    auto run = std::unique_ptr<CommandRun>(new CommandRun(argv_for(screen)));
    run->start();

    const auto inserted = runs_.emplace(std::string(screen), std::move(run));
    return *inserted.first->second;
}

}
}
