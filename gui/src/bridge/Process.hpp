/** @file Process.hpp
 *  @brief Declares the child process whose stdout arrives as lines and whose stdin takes answers.
 *  @author Mustafa Garip
 */

#pragma once

#include "bridge/LineQueue.hpp"

#include <memory>
#include <mutex>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Runs one child process and pushes each complete stdout line into a LineQueue. */
class Process
{
public:
    /**
     * @brief Spawns @p argv with piped stdin and stdout and starts the reader thread.
     * @param argv The program and its arguments, the program first.
     * @param out The queue the reader fills; it outlives the returned process.
     * @return The running process, or nullptr when the spawn failed.
     */
    static std::unique_ptr<Process> start(const std::vector<std::string>& argv, LineQueue& out);

    /** @brief Waits for the child and joins the reader thread. */
    ~Process();

    Process(const Process&) = delete;
    Process& operator=(const Process&) = delete;

    /** @brief Writes @p line to the child's stdin with a newline appended. */
    void write_line(std::string_view line);

    /** @brief Reports whether the child has not yet exited. */
    bool running() const;

    /** @brief Waits for the child, closes the queue, and returns the child's exit code. */
    int exit_code();

private:
    /** @brief Holds the operating system's handles for one spawned child. */
    struct Native;

    /** @brief Takes ownership of the spawned handles and binds the queue the reader fills. */
    Process(std::unique_ptr<Native> native, LineQueue& out);

    /** @brief Reads stdout until end of file, pushing each complete line and then closing. */
    void read_until_end();

    /** @brief Pushes every newline-terminated line in @p pending and keeps the remainder. */
    void emit_complete_lines(std::string& pending);

    /** @brief Pushes any unterminated remainder of @p pending and closes the queue. */
    void flush_pending(std::string& pending);

    /** @brief Closes the child's stdin so a child waiting on an answer sees end of file. */
    void close_input();

    /** @brief Records the child's exit code once and marks it exited. */
    void remember_exit(int code) const;

    /** @brief Holds the platform handles for the child and its two pipes. */
    std::unique_ptr<Native> native_;

    /** @brief References the queue the reader thread fills. */
    LineQueue& lines_;

    /** @brief Runs read_until_end for the life of the child's stdout. */
    std::thread reader_;

    /** @brief Guards exited_ and exit_code_ against the caller and the waiter. */
    mutable std::mutex state_mutex_;

    /** @brief Records that the child has been waited for. */
    mutable bool exited_ = false;

    /** @brief Holds the code the child exited with once exited_ is set. */
    mutable int exit_code_ = 0;
};

}
}
