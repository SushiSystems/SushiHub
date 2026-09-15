/** @file model_test.cpp
 *  @brief Checks that a scripted line queue folds into the RunState the UI reads,
 *         and that the run log points at whichever run the strip was handed.
 *  @author Mustafa Garip
 */

#include "bridge/LineQueue.hpp"
#include "model/CommandRun.hpp"
#include "model/RunLog.hpp"
#include "model/RunState.hpp"

#include "FixtureFile.hpp"

#include <gtest/gtest.h>

#include <string>
#include <vector>

namespace
{

using SushiHub::Gui::CommandRun;
using SushiHub::Gui::LineQueue;
using SushiHub::Gui::RunLog;
using SushiHub::Gui::RunState;
using SushiHub::GuiTests::fixture_lines;

/** @brief Holds a started run whose lines the test pushes by hand. */
class ScriptedRun : public ::testing::Test
{
protected:
    /** @brief Starts the run before the test body pushes its first line. */
    void SetUp() override
    {
        ASSERT_TRUE(run_.start());
    }

    /** @brief Holds the queue the test pushes lines into. */
    LineQueue queue_;

    /** @brief Holds the run that folds queue_ and spawns nothing. */
    CommandRun run_{{"hub", "--json", "status"}, queue_};
};

}

TEST_F(ScriptedRun, FoldsTheHandWrittenStreamIntoEveryProjection)
{
    for (const std::string& line : fixture_lines("events/all_kinds.jsonl"))
    {
        queue_.push(line);
    }
    queue_.close();
    run_.poll();

    const RunState& state = run_.state();
    EXPECT_TRUE(state.finished);
    EXPECT_TRUE(state.errors.empty());
    EXPECT_EQ(state.events.size(), 11U);

    ASSERT_EQ(state.lines.size(), 3U);
    EXPECT_EQ(state.lines.front().level, "info");

    ASSERT_EQ(state.tables.size(), 1U);
    EXPECT_EQ(state.tables.front().title, "Modules");
    EXPECT_EQ(state.tables.front().rows.size(), 3U);

    ASSERT_TRUE(state.progress.has_value());
    EXPECT_EQ(state.progress->label, "read-dependencies");
    EXPECT_FALSE(state.progress->fraction.has_value());

    ASSERT_TRUE(state.pending_prompt.has_value());
    EXPECT_EQ(state.pending_prompt->id, "prompt-1");

    ASSERT_TRUE(state.result.has_value());
    EXPECT_TRUE(state.result->ok);
    EXPECT_TRUE(state.result->payload.contains("modules"));
}

TEST_F(ScriptedRun, FoldsInStagesAndOnlyFinishesWhenTheQueueCloses)
{
    run_.poll();
    EXPECT_FALSE(run_.state().finished);
    EXPECT_TRUE(run_.state().events.empty());

    queue_.push(R"({"event":"header","title":"SushiStack Status"})");
    run_.poll();
    EXPECT_EQ(run_.state().events.size(), 1U);
    EXPECT_FALSE(run_.state().finished);

    queue_.push(R"({"event":"line","level":"info","message":"one"})");
    queue_.push(R"({"event":"result","ok":false,"payload":{}})");
    queue_.close();
    run_.poll();

    EXPECT_TRUE(run_.state().finished);
    EXPECT_EQ(run_.state().events.size(), 3U);
    ASSERT_TRUE(run_.state().result.has_value());
    EXPECT_FALSE(run_.state().result->ok);
}

TEST_F(ScriptedRun, KeepsTheLatestProgressAndTheLatestPrompt)
{
    queue_.push(R"({"event":"progress","label":"first","index":1,"count":2,"fraction":0.5})");
    queue_.push(R"({"event":"progress","label":"second","index":2,"count":2,"fraction":1.0})");
    queue_.push(R"({"event":"prompt","id":"prompt-1","message":"a?","default":null})");
    queue_.push(R"({"event":"prompt","id":"prompt-2","message":"b?","default":"y"})");
    run_.poll();

    ASSERT_TRUE(run_.state().progress.has_value());
    EXPECT_EQ(run_.state().progress->label, "second");
    ASSERT_TRUE(run_.state().pending_prompt.has_value());
    EXPECT_EQ(run_.state().pending_prompt->id, "prompt-2");
}

TEST_F(ScriptedRun, RecordsABadLineAsAnErrorAndKeepsFolding)
{
    queue_.push("this is not JSON");
    queue_.push(R"({"event":"line","level":"info","message":"after the bad line"})");
    run_.poll();

    ASSERT_EQ(run_.state().errors.size(), 1U);
    EXPECT_FALSE(run_.state().errors.front().reason.empty());
    ASSERT_EQ(run_.state().lines.size(), 1U);
    EXPECT_EQ(run_.state().lines.front().message, "after the bad line");
}

TEST_F(ScriptedRun, ClearsThePendingPromptWhenItIsAnswered)
{
    queue_.push(R"({"event":"prompt","id":"prompt-1","message":"Clone?","default":"n"})");
    run_.poll();
    ASSERT_TRUE(run_.state().pending_prompt.has_value());

    run_.answer_prompt("y");
    EXPECT_FALSE(run_.state().pending_prompt.has_value());
}

TEST_F(ScriptedRun, RefusesASecondStart)
{
    EXPECT_TRUE(run_.started());
    EXPECT_FALSE(run_.start());
}

TEST(CommandRunTest, ReportsAProgramThatCannotBeSpawned)
{
    CommandRun run({"sushihub_gui_no_such_program", "--json", "status"});

    EXPECT_FALSE(run.start());
    EXPECT_TRUE(run.state().finished);
    ASSERT_EQ(run.state().lines.size(), 1U);
    EXPECT_EQ(run.state().lines.front().level, "error");
}

TEST(RunLogTest, HoldsNoRunBeforeTheFirstAdoption)
{
    RunLog log;

    EXPECT_FALSE(log.has_run());
    EXPECT_TRUE(log.label().empty());
}

TEST(RunLogTest, PointsAtTheRunItAdoptedAndKeepsItsLabel)
{
    LineQueue queue;
    CommandRun run({"hub", "--json", "status"}, queue);
    RunLog log;

    log.adopt(run, "hub status");

    ASSERT_TRUE(log.has_run());
    EXPECT_EQ(&log.run(), &run);
    EXPECT_EQ(log.label(), "hub status");
}

TEST(RunLogTest, FollowsTheRunAdoptedLast)
{
    LineQueue first_queue;
    LineQueue second_queue;
    CommandRun first({"hub", "--json", "status"}, first_queue);
    CommandRun second({"hub", "--json", "doctor"}, second_queue);
    RunLog log;

    log.adopt(first, "hub status");
    log.adopt(second, "hub doctor");

    EXPECT_EQ(&log.run(), &second);
    EXPECT_EQ(log.label(), "hub doctor");
}
