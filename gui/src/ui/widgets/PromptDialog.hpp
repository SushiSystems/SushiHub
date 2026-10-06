/**************************************************************************/
/* PromptDialog.hpp                                                       */
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

/** @file PromptDialog.hpp
 *  @brief Declares the modal that asks a prompt event's question and collects one line.
 *  @author Mustafa Garip
 */

#pragma once

#include "contract/Event.hpp"

#include <array>
#include <cstddef>
#include <string>

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

/** @brief Asks the question a run stopped on and holds the line being typed in answer. */
class PromptDialog
{
public:
    /**
     * @brief Draws the modal for @p prompt and reports whether it was answered this frame.
     * @param answer Receives the line the run's stdin is to be given.
     * @return Whether @p answer was filled; the caller then clears the pending prompt.
     */
    bool draw(const PromptEvent& prompt, std::string& answer);

private:
    /** @brief Seeds the buffer with @p prompt's default the first time that prompt is seen. */
    void adopt(const PromptEvent& prompt);

    /** @brief Holds how many characters an answer may have, the terminator included. */
    static constexpr std::size_t CAPACITY = 256;

    /** @brief Holds the identifier of the prompt the buffer belongs to. */
    std::string prompt_id_;

    /** @brief Holds the line being typed, null-terminated. */
    std::array<char, CAPACITY> answer_{};
};

}
}
}
