/** @file event_test.cpp
 *  @brief Checks that every recorded event line parses to its kind and a bad line does not throw.
 *  @author Mustafa Garip
 */

#include "contract/Event.hpp"

#include "FixtureFile.hpp"

#include <gtest/gtest.h>

#include <set>
#include <string>
#include <variant>
#include <vector>

namespace
{

using SushiHub::Gui::CommandEvent;
using SushiHub::Gui::Event;
using SushiHub::Gui::HeaderEvent;
using SushiHub::Gui::LineEvent;
using SushiHub::Gui::PanelEvent;
using SushiHub::Gui::ParseError;
using SushiHub::Gui::ProgressEvent;
using SushiHub::Gui::PromptEvent;
using SushiHub::Gui::ResultEvent;
using SushiHub::Gui::TableEvent;
using SushiHub::Gui::parse_event;
using SushiHub::GuiTests::fixture_lines;

/** @brief Returns the kind name of the alternative @p event holds. */
std::string kind_of(const Event& event)
{
    if (std::holds_alternative<LineEvent>(event))
    {
        return "line";
    }
    if (std::holds_alternative<CommandEvent>(event))
    {
        return "command";
    }
    if (std::holds_alternative<HeaderEvent>(event))
    {
        return "header";
    }
    if (std::holds_alternative<PanelEvent>(event))
    {
        return "panel";
    }
    if (std::holds_alternative<TableEvent>(event))
    {
        return "table";
    }
    if (std::holds_alternative<ProgressEvent>(event))
    {
        return "progress";
    }
    if (std::holds_alternative<ResultEvent>(event))
    {
        return "result";
    }
    return "prompt";
}

/** @brief Parses @p line and fails the test with the reason when it is not an event. */
Event parsed(const std::string& line)
{
    const std::variant<Event, ParseError> outcome = parse_event(line);
    if (std::holds_alternative<ParseError>(outcome))
    {
        ADD_FAILURE() << std::get<ParseError>(outcome).reason << " in: " << line;
        return Event(LineEvent{});
    }
    return std::get<Event>(outcome);
}

}

TEST(EventTest, EveryRecordedLineParses)
{
    for (const char* name : {"events/status.jsonl", "events/doctor.jsonl"})
    {
        const std::vector<std::string> lines = fixture_lines(name);
        ASSERT_FALSE(lines.empty()) << name;
        for (const std::string& line : lines)
        {
            EXPECT_TRUE(std::holds_alternative<Event>(parse_event(line))) << name << ": " << line;
        }
    }
}

TEST(EventTest, EveryHandWrittenLineParsesAndTheEightKindsAppear)
{
    const std::vector<std::string> lines = fixture_lines("events/all_kinds.jsonl");
    ASSERT_FALSE(lines.empty());

    std::set<std::string> kinds;
    for (const std::string& line : lines)
    {
        kinds.insert(kind_of(parsed(line)));
    }

    const std::set<std::string> expected{"line", "command", "header", "panel",
                                         "table", "progress", "result", "prompt"};
    EXPECT_EQ(kinds, expected);
}

TEST(EventTest, ReadsATableWithItsColumnsAndRows)
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

TEST(EventTest, ReadsAProgressFractionAndItsAbsence)
{
    const Event known = parsed(
        R"({"event":"progress","label":"install","index":2,"count":4,"fraction":0.5})");
    const ProgressEvent& measured = std::get<ProgressEvent>(known);
    EXPECT_EQ(measured.label, "install");
    EXPECT_EQ(measured.index, 2);
    EXPECT_EQ(measured.count, 4);
    ASSERT_TRUE(measured.fraction.has_value());
    EXPECT_DOUBLE_EQ(measured.fraction.value(), 0.5);

    const Event unknown = parsed(
        R"({"event":"progress","label":"install","index":2,"count":4,"fraction":null})");
    EXPECT_FALSE(std::get<ProgressEvent>(unknown).fraction.has_value());
}

TEST(EventTest, ReadsAPromptDefaultAndItsAbsence)
{
    const Event with_default = parsed(
        R"({"event":"prompt","id":"prompt-1","message":"Clone?","default":"n"})");
    const PromptEvent& prompt = std::get<PromptEvent>(with_default);
    EXPECT_EQ(prompt.id, "prompt-1");
    ASSERT_TRUE(prompt.default_answer.has_value());
    EXPECT_EQ(prompt.default_answer.value(), "n");

    const Event without_default = parsed(
        R"({"event":"prompt","id":"prompt-2","message":"Path?","default":null})");
    EXPECT_FALSE(std::get<PromptEvent>(without_default).default_answer.has_value());
}

TEST(EventTest, ReadsAResultPayloadAsAnObject)
{
    const Event event = parsed(R"({"event":"result","ok":true,"payload":{"modules":["a"]}})");
    const ResultEvent& result = std::get<ResultEvent>(event);

    EXPECT_TRUE(result.ok);
    ASSERT_TRUE(result.payload.contains("modules"));
    EXPECT_EQ(result.payload["modules"][0].get<std::string>(), "a");
}

TEST(EventTest, RefusesABadLineWithAReasonInsteadOfThrowing)
{
    const std::vector<std::string> refused{
        "not json at all",
        "[1, 2, 3]",
        R"({"level":"info","message":"no kind"})",
        R"({"event":"spinner","frame":3})",
        R"({"event":"line","level":"shout","message":"unknown level"})",
        R"({"event":"line","level":"info"})",
        R"({"event":"table","title":"t","columns":["A"],"rows":[[1]]})",
        R"({"event":"progress","label":"l","index":"two","count":4,"fraction":null})",
        R"({"event":"result","ok":true,"payload":[]})"};

    for (const std::string& line : refused)
    {
        const std::variant<Event, ParseError> outcome = parse_event(line);
        ASSERT_TRUE(std::holds_alternative<ParseError>(outcome)) << "accepted: " << line;
        EXPECT_FALSE(std::get<ParseError>(outcome).reason.empty()) << "silent on: " << line;
    }
}

TEST(EventTest, RefusesAnEmptyLine)
{
    const std::variant<Event, ParseError> outcome = parse_event("");
    EXPECT_TRUE(std::holds_alternative<ParseError>(outcome));
}
