/**************************************************************************/
/* bridge_test.cpp                                                        */
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

/** @file bridge_test.cpp
 *  @brief Checks that a spawned child's stdout arrives as lines and its stdin takes an answer.
 *  @author Mustafa Garip
 */

#include "bridge/LineQueue.hpp"
#include "bridge/Process.hpp"

#include <gtest/gtest.h>

#include <string>
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

/** @brief Pops every line @p queue holds; the caller has already waited for the writer. */
std::vector<std::string> take_all(LineQueue& queue)
{
    std::vector<std::string> collected;
    std::string line;
    while (queue.try_pop(line))
    {
        collected.push_back(line);
    }
    return collected;
}

}

TEST(Small_LineQueueTest, PopsInPushOrder)
{
    LineQueue queue;
    std::string line;

    queue.push("first");
    queue.push("second");

    ASSERT_TRUE(queue.try_pop(line));
    EXPECT_EQ(line, "first");
    ASSERT_TRUE(queue.try_pop(line));
    EXPECT_EQ(line, "second");
    EXPECT_FALSE(queue.try_pop(line));
}

TEST(Small_LineQueueTest, ReportsClosureOnlyAfterClose)
{
    LineQueue queue;
    EXPECT_FALSE(queue.closed());

    queue.close();

    EXPECT_TRUE(queue.closed());
}

TEST(Medium_ProcessTest, ReadsTwoLinesAndExitsZero)
{
    LineQueue queue;
    const std::vector<std::string> argv{python_executable(), "-c", "print('a');print('b')"};

    auto process = Process::start(argv, queue);
    ASSERT_NE(process, nullptr);

    // exit_code() waits for the child and joins the reader, so every line is queued after it.
    EXPECT_EQ(process->exit_code(), 0);

    const std::vector<std::string> lines = take_all(queue);
    ASSERT_EQ(lines.size(), 2U);
    EXPECT_EQ(lines[0], "a");
    EXPECT_EQ(lines[1], "b");
}

TEST(Medium_ProcessTest, EchoesALineWrittenToStandardInput)
{
    LineQueue queue;
    const std::vector<std::string> argv{python_executable(), "-c",
                                        "import sys;print(sys.stdin.readline().strip())"};

    auto process = Process::start(argv, queue);
    ASSERT_NE(process, nullptr);

    process->write_line("hello");
    EXPECT_EQ(process->exit_code(), 0);

    const std::vector<std::string> lines = take_all(queue);
    ASSERT_EQ(lines.size(), 1U);
    EXPECT_EQ(lines[0], "hello");
}

TEST(Medium_ProcessTest, ReturnsAChildsNonZeroExitCode)
{
    LineQueue queue;
    const std::vector<std::string> argv{python_executable(), "-c", "import sys;sys.exit(3)"};

    auto process = Process::start(argv, queue);
    ASSERT_NE(process, nullptr);

    EXPECT_EQ(process->exit_code(), 3);
}

TEST(Medium_ProcessTest, ReportsFailureForAProgramThatIsNotThere)
{
    LineQueue queue;
    const std::vector<std::string> argv{"sushihub_gui_no_such_program"};

    EXPECT_EQ(Process::start(argv, queue), nullptr);
}
