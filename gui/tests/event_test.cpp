/**************************************************************************/
/* event_test.cpp                                                         */
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

/** @file event_test.cpp
 *  @brief Checks that every recorded event line parses to its kind and a bad line does not throw.
 *  @author Mustafa Garip
 */

#include "contract/Event.hpp"

#include "FixtureFile.hpp"

#include <gtest/gtest.h>

#include <string>
#include <variant>
#include <vector>

namespace
{

using SushiHub::Gui::Event;
using SushiHub::Gui::ParseError;
using SushiHub::Gui::ProgressEvent;
using SushiHub::Gui::PromptEvent;
using SushiHub::Gui::ResultEvent;
using SushiHub::Gui::TableEvent;
using SushiHub::Gui::parse_event;
using SushiHub::GuiTests::fixture_lines;

/** @brief Parses @p line and fails the test with the reason when it is not an event. */
Event parsed(const std::string& line)
{
    const std::variant<Event, ParseError> outcome = parse_event(line);
    if (std::holds_alternative<ParseError>(outcome))
    {
        ADD_FAILURE() << std::get<ParseError>(outcome).reason << " in: " << line;
        return Event(SushiHub::Gui::LineEvent{});
    }
    return std::get<Event>(outcome);
}

/** @brief Returns every non-empty line of the recorded status and doctor runs, in file order. */
std::vector<std::string> recorded_lines()
{
    std::vector<std::string> lines = fixture_lines("events/status.jsonl");
    const std::vector<std::string> doctor = fixture_lines("events/doctor.jsonl");
    lines.insert(lines.end(), doctor.begin(), doctor.end());
    return lines;
}

/** @brief Runs the parse check once per recorded line. */
class Medium_RecordedEventTest : public ::testing::TestWithParam<std::string>
{
};

/** @brief Runs the refusal check once per malformed line. */
class Small_EventRefusalTest : public ::testing::TestWithParam<std::string>
{
};

}

TEST_P(Medium_RecordedEventTest, ParsesTheRecordedLine)
{
    EXPECT_TRUE(std::holds_alternative<Event>(parse_event(GetParam()))) << GetParam();
}

INSTANTIATE_TEST_SUITE_P(StatusAndDoctorRuns, Medium_RecordedEventTest,
                         ::testing::ValuesIn(recorded_lines()));

TEST(Small_EventTest, ReadsATableWithItsColumnsAndRows)
{
    const Event event = parsed(
        R"({"event":"table","title":"Modules","columns":["A","B"],"rows":[["a1","b1"],["a2","b2"]]})");
    const TableEvent& table = std::get<TableEvent>(event);

    EXPECT_EQ(table.title, "Modules");
    ASSERT_EQ(table.columns.size(), 2U);
    EXPECT_EQ(table.columns[1], "B");
    ASSERT_EQ(table.rows.size(), 2U);
    ASSERT_EQ(table.rows[1].size(), 2U);
    EXPECT_EQ(table.rows[1][0], "a2");
}

TEST(Small_EventTest, ReadsAProgressFraction)
{
    const Event event = parsed(
        R"({"event":"progress","label":"install","index":2,"count":4,"fraction":0.5})");
    const ProgressEvent& progress = std::get<ProgressEvent>(event);

    EXPECT_EQ(progress.label, "install");
    EXPECT_EQ(progress.index, 2);
    EXPECT_EQ(progress.count, 4);
    ASSERT_TRUE(progress.fraction.has_value());
    EXPECT_DOUBLE_EQ(progress.fraction.value(), 0.5);
}

TEST(Small_EventTest, ReadsAProgressWithoutAFraction)
{
    const Event event = parsed(
        R"({"event":"progress","label":"install","index":2,"count":4,"fraction":null})");

    EXPECT_FALSE(std::get<ProgressEvent>(event).fraction.has_value());
}

TEST(Small_EventTest, ReadsAPromptDefault)
{
    const Event event = parsed(
        R"({"event":"prompt","id":"prompt-1","message":"Clone?","default":"n"})");
    const PromptEvent& prompt = std::get<PromptEvent>(event);

    EXPECT_EQ(prompt.id, "prompt-1");
    ASSERT_TRUE(prompt.default_answer.has_value());
    EXPECT_EQ(prompt.default_answer.value(), "n");
}

TEST(Small_EventTest, ReadsAPromptWithoutADefault)
{
    const Event event = parsed(
        R"({"event":"prompt","id":"prompt-2","message":"Path?","default":null})");

    EXPECT_FALSE(std::get<PromptEvent>(event).default_answer.has_value());
}

TEST(Small_EventTest, ReadsAResultPayloadAsAnObject)
{
    const Event event = parsed(R"({"event":"result","ok":true,"payload":{"modules":["a"]}})");
    const ResultEvent& result = std::get<ResultEvent>(event);

    EXPECT_TRUE(result.ok);
    ASSERT_TRUE(result.payload.contains("modules"));
    EXPECT_EQ(result.payload["modules"][0].get<std::string>(), "a");
}

TEST_P(Small_EventRefusalTest, RefusesTheLineWithAReasonInsteadOfThrowing)
{
    const std::variant<Event, ParseError> outcome = parse_event(GetParam());

    ASSERT_TRUE(std::holds_alternative<ParseError>(outcome));
    EXPECT_FALSE(std::get<ParseError>(outcome).reason.empty());
}

INSTANTIATE_TEST_SUITE_P(
    BadLines, Small_EventRefusalTest,
    ::testing::Values(
        std::string(""), std::string("not json at all"), std::string("[1, 2, 3]"),
        std::string(R"({"level":"info","message":"no kind"})"),
        std::string(R"({"event":"spinner","frame":3})"),
        std::string(R"({"event":"line","level":"shout","message":"unknown level"})"),
        std::string(R"({"event":"line","level":"info"})"),
        std::string(R"({"event":"table","title":"t","columns":["A"],"rows":[[1]]})"),
        std::string(
            R"({"event":"progress","label":"l","index":"two","count":4,"fraction":null})"),
        std::string(R"({"event":"result","ok":true,"payload":[]})")));
