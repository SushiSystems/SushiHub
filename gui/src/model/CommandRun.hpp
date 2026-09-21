/** @file CommandRun.hpp
 *  @brief Declares one run of one `hub` command and the fold from its lines into a RunState.
 *  @author Mustafa Garip
 */

#pragma once

#include "bridge/LineQueue.hpp"
#include "bridge/Process.hpp"
#include "model/RunState.hpp"

#include <memory>
#include <string>
#include <string_view>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Runs one command through the bridge and folds its event lines into a RunState. */
class CommandRun
{
public:
    /** @brief Prepares a run of @p ss_argv over a queue this run owns and a process it spawns. */
    explicit CommandRun(std::vector<std::string> ss_argv);

    /** @brief Prepares a run that folds @p queue and spawns nothing, for a scripted stream. */
    CommandRun(std::vector<std::string> ss_argv, LineQueue& queue);

    CommandRun(const CommandRun&) = delete;
    CommandRun& operator=(const CommandRun&) = delete;

    /**
     * @brief Spawns the command, or accepts the supplied queue as already running.
     * @return Whether the run is now producing lines; a failed spawn leaves a message in state().
     */
    bool start();

    /** @brief Drains every queued line into state(), parsing each one. */
    void poll();

    /** @brief Writes @p answer to the command's stdin and clears the pending prompt. */
    void answer_prompt(std::string_view answer);

    /** @brief Returns everything the run has produced so far. */
    const RunState& state() const;

    /** @brief Returns the command line this run was built for. */
    const std::vector<std::string>& argv() const;

    /** @brief Reports whether start() has been called and did not fail. */
    bool started() const;

private:
    /** @brief Adds one parsed event to every projection of the state it belongs to. */
    void fold(Event event);

    /** @brief Holds the command and its arguments, the program first. */
    std::vector<std::string> argv_;

    /** @brief Holds the queue this run fills when it spawns its own process. */
    LineQueue owned_queue_;

    /** @brief References the queue poll() drains, owned or supplied. */
    LineQueue& queue_;

    /** @brief Holds the spawned command while it runs, null when none was spawned. */
    std::unique_ptr<Process> process_;

    /** @brief Records that this run spawns a process rather than folding a supplied queue. */
    bool spawns_;

    /** @brief Records that start() has been called. */
    bool started_ = false;

    /** @brief Holds everything the run has produced so far. */
    RunState state_;
};

}
}
