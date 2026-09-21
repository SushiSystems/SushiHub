/** @file CommandRun.cpp
 *  @brief Defines the spawn, the drain and the fold of one command's event lines.
 *  @author Mustafa Garip
 */

#include "model/CommandRun.hpp"

#include "contract/Event.hpp"

#include <utility>
#include <variant>

namespace SushiHub
{
namespace Gui
{

CommandRun::CommandRun(std::vector<std::string> ss_argv)
    : argv_(std::move(ss_argv)),
      queue_(owned_queue_),
      spawns_(true)
{
}

CommandRun::CommandRun(std::vector<std::string> ss_argv, LineQueue& queue)
    : argv_(std::move(ss_argv)),
      queue_(queue),
      spawns_(false)
{
}

bool CommandRun::start()
{
    if (started_)
    {
        return false;
    }
    started_ = true;

    if (!spawns_)
    {
        return true;
    }

    process_ = Process::start(argv_, queue_);
    if (process_ == nullptr)
    {
        const std::string program = argv_.empty() ? std::string("the command") : argv_.front();
        state_.lines.push_back(LineEvent{"error", "could not start " + program});
        state_.finished = true;
        return false;
    }

    return true;
}

void CommandRun::poll()
{
    std::string line;
    while (queue_.try_pop(line))
    {
        std::variant<Event, ParseError> outcome = parse_event(line);
        if (std::holds_alternative<ParseError>(outcome))
        {
            state_.errors.push_back(std::move(std::get<ParseError>(outcome)));
            continue;
        }
        fold(std::move(std::get<Event>(outcome)));
    }

    if (queue_.closed() && queue_.empty())
    {
        state_.finished = true;
    }
}

void CommandRun::answer_prompt(std::string_view answer)
{
    if (process_ != nullptr)
    {
        process_->write_line(answer);
    }
    state_.pending_prompt.reset();
}

const RunState& CommandRun::state() const
{
    return state_;
}

const std::vector<std::string>& CommandRun::argv() const
{
    return argv_;
}

bool CommandRun::started() const
{
    return started_;
}

void CommandRun::fold(Event event)
{
    if (const LineEvent* line = std::get_if<LineEvent>(&event))
    {
        state_.lines.push_back(*line);
    }
    else if (const TableEvent* table = std::get_if<TableEvent>(&event))
    {
        state_.tables.push_back(*table);
    }
    else if (const ProgressEvent* progress = std::get_if<ProgressEvent>(&event))
    {
        state_.progress = *progress;
    }
    else if (const PromptEvent* prompt = std::get_if<PromptEvent>(&event))
    {
        state_.pending_prompt = *prompt;
    }
    else if (const ResultEvent* result = std::get_if<ResultEvent>(&event))
    {
        state_.result = *result;
    }

    state_.events.push_back(std::move(event));
}

}
}
