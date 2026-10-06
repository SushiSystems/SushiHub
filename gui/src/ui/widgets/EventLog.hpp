/**************************************************************************/
/* EventLog.hpp                                                           */
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

/** @file EventLog.hpp
 *  @brief Declares the scrolling region a run's events are drawn in, in arrival order.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/RunState.hpp"

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

/**
 * @brief Draws every event @p state holds in the order the command produced it.
 * @param id The identifier ImGui keeps the region's scroll position under.
 * @param height The region's height in pixels; zero fills whatever space is left.
 * @pre A progress event is left to draw_progress and is skipped here.
 */
void draw_event_log(const char* id, const RunState& state, float height);

}
}
}
