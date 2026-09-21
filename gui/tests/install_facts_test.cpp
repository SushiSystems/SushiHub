/** @file install_facts_test.cpp
 *  @brief Checks the sentences an install card derives from the status payload.
 *  @author Mustafa Garip
 */

#include "contract/Event.hpp"
#include "model/InstallFacts.hpp"

#include "FixtureFile.hpp"

#include <gtest/gtest.h>

#include <nlohmann/json.hpp>

#include <string>
#include <variant>

namespace
{

using SushiHub::Gui::Event;
using SushiHub::Gui::ParseError;
using SushiHub::Gui::ResultEvent;
using SushiHub::Gui::parse_event;
using SushiHub::GuiTests::fixture_lines;

namespace InstallFacts = SushiHub::Gui::InstallFacts;

/** @brief Returns the payload of the recorded status run's result event. */
nlohmann::json recorded_status_payload()
{
    for (const std::string& line : fixture_lines("events/status.jsonl"))
    {
        const std::variant<Event, ParseError> outcome = parse_event(line);
        if (std::holds_alternative<Event>(outcome) &&
            std::holds_alternative<ResultEvent>(std::get<Event>(outcome)))
        {
            return std::get<ResultEvent>(std::get<Event>(outcome)).payload;
        }
    }
    ADD_FAILURE() << "the recorded status run has no result event";
    return nlohmann::json::object();
}

}

TEST(InstallFactsTest, TheRecordedPayloadCarriesTheEngineAndTheHubBlock)
{
    const nlohmann::json payload = recorded_status_payload();

    const nlohmann::json* engine = InstallFacts::find_module(payload, "sushiengine");
    ASSERT_NE(engine, nullptr);
    EXPECT_TRUE(engine->contains("source"));
    EXPECT_TRUE(engine->contains("binary"));
    ASSERT_TRUE(payload.contains("hub"));
    EXPECT_EQ(InstallFacts::text(payload["hub"], "command", ""), "hub");
    EXPECT_EQ(InstallFacts::find_module(payload, "nothing-called-this"), nullptr);
}

TEST(InstallFactsTest, WritesTheDistanceOrThatThereIsNoUpstream)
{
    EXPECT_EQ(InstallFacts::distance(nlohmann::json{{"ahead", 2}, {"behind", 0}}), "+2 / -0");
    EXPECT_EQ(InstallFacts::distance(nlohmann::json{{"ahead", nullptr}, {"behind", nullptr}}),
              "no upstream");
}

TEST(InstallFactsTest, CountsTheLastFetchInWholeDays)
{
    const long today = InstallFacts::days_from_iso("2026-09-15");
    const auto fetched = [](const char* iso) { return nlohmann::json{{"last_fetch", iso}}; };

    EXPECT_EQ(InstallFacts::last_fetch(fetched("2026-09-15T10:36:15Z"), today), "fetched today");
    EXPECT_EQ(InstallFacts::last_fetch(fetched("2026-09-14T23:59:59Z"), today),
              "fetched 1 day ago");
    EXPECT_EQ(InstallFacts::last_fetch(fetched("2026-08-16T00:00:00Z"), today),
              "fetched 30 days ago");
    EXPECT_EQ(InstallFacts::last_fetch(nlohmann::json{{"last_fetch", nullptr}}, today),
              "never fetched");
}

TEST(InstallFactsTest, CountsDaysAcrossALeapDay)
{
    EXPECT_EQ(InstallFacts::days_from_iso("1970-01-01"), 0);
    EXPECT_EQ(InstallFacts::days_from_iso("2024-03-01") - InstallFacts::days_from_iso("2024-02-28"),
              2);
    EXPECT_EQ(InstallFacts::days_from_iso("not a date"), -1);
}

TEST(InstallFactsTest, SaysWhetherANewerReleaseExistsOnlyAfterACheck)
{
    const nlohmann::json current{{"version", "1.4.2"}, {"latest_version", "1.4.2"}};
    const nlohmann::json behind{{"version", "1.4.0"}, {"latest_version", "1.4.2"}};
    const nlohmann::json unanswered{{"version", "1.4.0"}, {"latest_version", nullptr}};

    EXPECT_EQ(InstallFacts::newer_release(behind, false), "not checked");
    EXPECT_EQ(InstallFacts::newer_release(current, true), "up to date");
    EXPECT_EQ(InstallFacts::newer_release(behind, true), "1.4.2 available");
    EXPECT_EQ(InstallFacts::newer_release(unanswered, true), "could not check");
}

TEST(InstallFactsTest, ReadsTheLicenceExpiryAsADate)
{
    const nlohmann::json licensed{
        {"binary", {{"platform", "windows-x64"}, {"licence_expires_at", "2027-03-01T00:00:00Z"}}}};
    const nlohmann::json unlicensed{
        {"binary", {{"platform", "windows-x64"}, {"licence_expires_at", nullptr}}}};

    EXPECT_EQ(InstallFacts::licence(licensed), "until 2027-03-01");
    EXPECT_EQ(InstallFacts::licence(unlicensed), "no licence file");
}

TEST(InstallFactsTest, NamesTheAliasAndTheHubsCurrency)
{
    const nlohmann::json hub{{"alias", {{"name", "sh"}, {"defined_in", "/home/u/.bashrc"}}},
                             {"source", {{"branch", "main"}, {"ahead", 0}, {"behind", 3},
                                         {"last_fetch", nullptr}}}};
    const nlohmann::json bare{{"alias", nullptr}, {"source", nullptr}};

    EXPECT_EQ(InstallFacts::alias(hub), "sh, in /home/u/.bashrc");
    EXPECT_EQ(InstallFacts::alias(bare), "not defined");
    EXPECT_EQ(InstallFacts::hub_currency(hub, true), "3 commits behind");
    EXPECT_EQ(InstallFacts::hub_currency(bare, true), "unknown");
}
