/** @file bridge_test.cpp
 *  @brief Checks that a spawned child's stdout arrives as lines and its stdin takes an answer.
 *  @author Mustafa Garip
 */

#include "bridge/LineQueue.hpp"
#include "bridge/Process.hpp"

#include <gtest/gtest.h>

#include <chrono>
#include <string>
#include <thread>
#include <vector>

namespace
{

using SushiHub::Gui::LineQueue;
using SushiHub::Gui::Process;

/** @brief Returns the interpreter name this platform spawns Python under. */
const char* python_executable()
{
#ifdef _WIN32
    return "python";
#else
    return "python3";
#endif
}

/** @brief Drains @p queue into a vector once the writing side has closed it. */
std::vector<std::string> drain_until_closed(LineQueue& queue)
{
    std::vector<std::string> collected;
    std::string line;
    while (!queue.closed() || !queue.empty())
    {
        if (queue.try_pop(line))
        {
            collected.push_back(line);
            continue;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    while (queue.try_pop(line))
    {
        collected.push_back(line);
    }
    return collected;
}

}

TEST(LineQueueTest, PopsInPushOrderAndReportsClosure)
{
    LineQueue queue;
    std::string line;

    EXPECT_FALSE(queue.try_pop(line));
    EXPECT_FALSE(queue.closed());

    queue.push("first");
    queue.push("second");

    ASSERT_TRUE(queue.try_pop(line));
    EXPECT_EQ(line, "first");
    ASSERT_TRUE(queue.try_pop(line));
    EXPECT_EQ(line, "second");
    EXPECT_FALSE(queue.try_pop(line));

    queue.close();
    EXPECT_TRUE(queue.closed());
}

TEST(ProcessTest, ReadsTwoLinesAndExitsZero)
{
    LineQueue queue;
    const std::vector<std::string> argv{python_executable(), "-c", "print('a');print('b')"};

    auto process = Process::start(argv, queue);
    ASSERT_NE(process, nullptr);

    const std::vector<std::string> lines = drain_until_closed(queue);
    EXPECT_EQ(process->exit_code(), 0);

    ASSERT_EQ(lines.size(), 2U);
    EXPECT_EQ(lines[0], "a");
    EXPECT_EQ(lines[1], "b");
}

TEST(ProcessTest, EchoesALineWrittenToStandardInput)
{
    LineQueue queue;
    const std::vector<std::string> argv{python_executable(), "-c",
                                        "import sys;print(sys.stdin.readline().strip())"};

    auto process = Process::start(argv, queue);
    ASSERT_NE(process, nullptr);

    process->write_line("hello");

    const std::vector<std::string> lines = drain_until_closed(queue);
    EXPECT_EQ(process->exit_code(), 0);

    ASSERT_EQ(lines.size(), 1U);
    EXPECT_EQ(lines[0], "hello");
}

TEST(ProcessTest, ReportsFailureForAProgramThatIsNotThere)
{
    LineQueue queue;
    const std::vector<std::string> argv{"sushihub_gui_no_such_program"};

    EXPECT_EQ(Process::start(argv, queue), nullptr);
}
