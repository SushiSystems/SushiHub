/**************************************************************************/
/* LineQueue.cpp                                                          */
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

/** @file LineQueue.cpp
 *  @brief Defines the mutex-guarded deque behind LineQueue.
 *  @author Mustafa Garip
 */

#include "bridge/LineQueue.hpp"

#include <utility>

namespace SushiHub
{
namespace Gui
{

void LineQueue::push(std::string line)
{
    const std::lock_guard<std::mutex> guard(mutex_);
    lines_.push_back(std::move(line));
}

bool LineQueue::try_pop(std::string& line)
{
    const std::lock_guard<std::mutex> guard(mutex_);
    if (lines_.empty())
    {
        return false;
    }

    line = std::move(lines_.front());
    lines_.pop_front();
    return true;
}

void LineQueue::close()
{
    const std::lock_guard<std::mutex> guard(mutex_);
    closed_ = true;
}

bool LineQueue::closed() const
{
    const std::lock_guard<std::mutex> guard(mutex_);
    return closed_;
}

bool LineQueue::empty() const
{
    const std::lock_guard<std::mutex> guard(mutex_);
    return lines_.empty();
}

}
}
