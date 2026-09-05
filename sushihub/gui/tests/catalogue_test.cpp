/** @file catalogue_test.cpp
 *  @brief Checks that the recorded catalogue parses and every parameter type maps.
 *  @author Mustafa Garip
 */

#include "contract/Catalogue.hpp"

#include "FixtureFile.hpp"

#include <gtest/gtest.h>

#include <algorithm>
#include <set>
#include <string>
#include <variant>
#include <vector>

namespace
{

using SushiHub::Gui::Catalogue;
using SushiHub::Gui::Command;
using SushiHub::Gui::Parameter;
using SushiHub::Gui::ParameterType;
using SushiHub::Gui::ParseError;
using SushiHub::Gui::parse_catalogue;
using SushiHub::Gui::parse_parameter_type;
using SushiHub::GuiTests::fixture_text;

/** @brief Parses the recorded catalogue and fails the test with the reason when it will not. */
Catalogue recorded_catalogue()
{
    const std::variant<Catalogue, ParseError> outcome =
        parse_catalogue(fixture_text("describe.json"));
    if (std::holds_alternative<ParseError>(outcome))
    {
        ADD_FAILURE() << std::get<ParseError>(outcome).reason;
        return Catalogue{};
    }
    return std::get<Catalogue>(outcome);
}

/** @brief Returns the command named @p name, or a default one when it is not there. */
Command command_named(const Catalogue& catalogue, const std::string& name)
{
    const auto found = std::find_if(catalogue.commands.begin(), catalogue.commands.end(),
                                    [&name](const Command& command)
                                    {
                                        return command.name == name;
                                    });
    if (found == catalogue.commands.end())
    {
        ADD_FAILURE() << "no command named " << name;
        return Command{};
    }
    return *found;
}

/** @brief Returns the parameter named @p name, or a default one when it is not there. */
Parameter parameter_named(const Command& command, const std::string& name)
{
    const auto found = std::find_if(command.parameters.begin(), command.parameters.end(),
                                    [&name](const Parameter& parameter)
                                    {
                                        return parameter.name == name;
                                    });
    if (found == command.parameters.end())
    {
        ADD_FAILURE() << "no parameter named " << name << " on " << command.name;
        return Parameter{};
    }
    return *found;
}

}

TEST(CatalogueTest, ReadsTheProgramVersionAndContract)
{
    const Catalogue catalogue = recorded_catalogue();

    EXPECT_EQ(catalogue.program, "ss");
    EXPECT_FALSE(catalogue.version.empty());
    EXPECT_EQ(catalogue.contract, "1");
    EXPECT_FALSE(catalogue.commands.empty());
}

TEST(CatalogueTest, MapsEveryParameterTypeTheContractAllows)
{
    ParameterType type = ParameterType::string;
    const char* names[] = {"string", "boolean", "integer", "number", "path", "choice"};
    const ParameterType expected[] = {ParameterType::string, ParameterType::boolean,
                                      ParameterType::integer, ParameterType::number,
                                      ParameterType::path, ParameterType::choice};

    for (std::size_t index = 0; index < 6; ++index)
    {
        ASSERT_TRUE(parse_parameter_type(names[index], type)) << names[index];
        EXPECT_EQ(type, expected[index]);
    }

    EXPECT_FALSE(parse_parameter_type("colour", type));
}

TEST(CatalogueTest, TheRecordedCatalogueCarriesEveryParameterType)
{
    const Catalogue catalogue = recorded_catalogue();

    std::set<ParameterType> seen;
    for (const Command& command : catalogue.commands)
    {
        for (const Parameter& parameter : command.parameters)
        {
            seen.insert(parameter.type);
        }
    }

    const std::set<ParameterType> expected{ParameterType::string, ParameterType::boolean,
                                           ParameterType::integer, ParameterType::number,
                                           ParameterType::path, ParameterType::choice};
    EXPECT_EQ(seen, expected);
}

TEST(CatalogueTest, ReadsAnArgumentAndAnOptionOfTheSameCommand)
{
    const Command add = command_named(recorded_catalogue(), "add");

    const Parameter modules = parameter_named(add, "modules");
    EXPECT_TRUE(modules.is_argument);
    EXPECT_TRUE(modules.multiple);
    EXPECT_TRUE(modules.required);
    EXPECT_TRUE(modules.flags.empty());
    EXPECT_FALSE(modules.help.empty());

    const Parameter dry_run = parameter_named(add, "dry_run");
    EXPECT_FALSE(dry_run.is_argument);
    EXPECT_EQ(dry_run.type, ParameterType::boolean);
    ASSERT_EQ(dry_run.flags.size(), 1U);
    EXPECT_EQ(dry_run.flags[0], "--dry-run");
    EXPECT_FALSE(dry_run.default_value.get<bool>());
}

TEST(CatalogueTest, ReadsAChoiceWithItsValuesAndLeavesOthersEmpty)
{
    const Command install = command_named(recorded_catalogue(), "install");

    const Parameter profile = parameter_named(install, "profile");
    EXPECT_EQ(profile.type, ParameterType::choice);
    ASSERT_EQ(profile.choices.size(), 3U);
    EXPECT_EQ(profile.choices[0], "debug");
    EXPECT_EQ(profile.default_value.get<std::string>(), "release");

    const Parameter prefix = parameter_named(install, "prefix");
    EXPECT_EQ(prefix.type, ParameterType::path);
    EXPECT_TRUE(prefix.choices.empty());
    EXPECT_TRUE(prefix.default_value.is_null());
}

TEST(CatalogueTest, ReadsACommandWithNoParameters)
{
    const Command status = command_named(recorded_catalogue(), "status");

    EXPECT_TRUE(status.parameters.empty());
    EXPECT_FALSE(status.applies_to.empty());
}

TEST(CatalogueTest, RefusesABadCatalogueWithAReasonInsteadOfThrowing)
{
    const std::vector<std::string> refused{
        "not json at all",
        "[]",
        R"({"program":"ss","version":"1","contract":"1"})",
        R"({"program":"ss","version":"1","contract":"1","commands":{}})",
        R"({"program":"ss","version":"1","contract":"1","commands":[{"name":"a","help":"h","applies_to":[],"params":[{"name":"p","kind":"flag","type":"string","multiple":false,"required":false,"default":null,"choices":null,"flags":[],"help":""}]}]})",
        R"({"program":"ss","version":"1","contract":"1","commands":[{"name":"a","help":"h","applies_to":[],"params":[{"name":"p","kind":"option","type":"colour","multiple":false,"required":false,"default":null,"choices":null,"flags":[],"help":""}]}]})"};

    for (const std::string& document : refused)
    {
        const std::variant<Catalogue, ParseError> outcome = parse_catalogue(document);
        ASSERT_TRUE(std::holds_alternative<ParseError>(outcome)) << "accepted: " << document;
        EXPECT_FALSE(std::get<ParseError>(outcome).reason.empty());
    }
}
