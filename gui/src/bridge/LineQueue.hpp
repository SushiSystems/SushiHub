/**************************************************************************/
/* LineQueue.hpp                                                          */
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

/** @file LineQueue.hpp
 *  @brief Declares the thread-safe hand-off of complete lines from a reader to the UI thread.
 *  @author Mustafa Garip
 */

#pragma once

#include <deque>
#include <mutex>
#include <string>

namespace SushiHub
{
namespace Gui
{

/** @brief Carries complete lines from the thread that reads a pipe to the thread that drains it. */
class LineQueue
{
public:
    /** @brief Appends one line to the back of the queue. */
    void push(std::string line);

    /** @brief Moves the front line into @p line and reports whether there was one. */
    bool try_pop(std::string& line);

    /** @brief Marks the writing side finished; queued lines stay poppable. */
    void close();

    /** @brief Reports whether the writing side has finished. */
    bool closed() const;

    /** @brief Reports whether no line is waiting to be popped. */
    bool empty() const;

private:
    /** @brief Guards every member below against the reader and the drainer. */
    mutable std::mutex mutex_;

    /** @brief Holds the lines in the order the reader produced them. */
    std::deque<std::string> lines_;

    /** @brief Records that the writing side will push no more lines. */
    bool closed_ = false;
};

}
}
