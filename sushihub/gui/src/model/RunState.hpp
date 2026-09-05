/** @file RunState.hpp
 *  @brief Declares everything one command run has produced so far, as the UI reads it each frame.
 *  @author Mustafa Garip
 */

#pragma once

#include "contract/Event.hpp"

#include <optional>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Holds one command run's events, both in order and projected by kind. */
struct RunState
{
    /** @brief Holds every event in the order the command produced it. */
    std::vector<Event> events;

    /** @brief Holds the message events, for the log the UI scrolls. */
    std::vector<LineEvent> lines;

    /** @brief Holds every table the command emitted. */
    std::vector<TableEvent> tables;

    /** @brief Holds the latest step, or nothing when the command reported none. */
    std::optional<ProgressEvent> progress;

    /** @brief Holds the question waiting for an answer, or nothing when none is. */
    std::optional<PromptEvent> pending_prompt;

    /** @brief Holds the command's outcome, or nothing until the result event arrives. */
    std::optional<ResultEvent> result;

    /** @brief Holds the reason for each line that could not be read. */
    std::vector<ParseError> errors;

    /** @brief Records that the command's output has ended. */
    bool finished = false;
};

}
}
