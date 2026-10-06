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
