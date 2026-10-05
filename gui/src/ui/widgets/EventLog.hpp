/****************************************************************/
/* EventLog.hpp                                                 */
/* SushiHub - https://github.com/SushiSystems/SushiHub          */
/* Copyright (c) 2026 Sushi Systems                             */
/* Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.    */
/* Commercial use requires a licence from Sushi Systems.        */
/****************************************************************/

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
