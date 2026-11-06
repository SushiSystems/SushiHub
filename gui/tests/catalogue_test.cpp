/**************************************************************************/
/* catalogue_test.cpp                                                     */
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

/** @file catalogue_test.cpp
 *  @brief Checks that catalogue documents parse, every parameter type maps and bad ones refuse.
 *  @author Mustafa Garip
 */

#include "contract/Catalogue.hpp"

#include "FixtureFile.hpp"

#include <gtest/gtest.h>

#include <algorithm>
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

/** @brief Holds the command with one required multiple argument and one boolean option. */
const char* const ADD_COMMAND = R"json({"name": "add", "help": "Clone modules.", "params": [
    {"name": "modules", "kind": "argument", "type": "string", "multiple": true, "required": true,
     "default": null, "choices": null, "flags": [], "help": "Modules to clone."},
    {"name": "dry_run", "kind": "option", "type": "boolean", "multiple": false, "required": false,
     "default": false, "choices": null, "flags": ["--dry-run"], "help": "Show only."}
  ], "applies_to": ["cloned", "linked", "binary"]})json";

/** @brief Holds the command with one choice option and one path option. */
const char* const INSTALL_COMMAND = R"json({"name": "install", "help": "Provision.", "params": [
    {"name": "prefix", "kind": "option", "type": "path", "multiple": false, "required": false,
     "default": null, "choices": null, "flags": ["--prefix"], "help": "Where to write."},
    {"name": "profile", "kind": "option", "type": "choice", "multiple": false, "required": false,
     "default": "release", "choices": ["debug", "release", "relwithdebinfo"],
     "flags": ["--profile"], "help": "Which profile."}
  ], "applies_to": ["cloned", "linked", "binary"]})json";

/** @brief Holds the command that takes no parameters. */
const char* const STATUS_COMMAND = R"json({"name": "status", "help": "Show modules.",
  "params": [], "applies_to": ["cloned", "linked", "binary"]})json";

/** @brief Wraps @p commands, a comma-separated list of command objects, into a whole document. */
std::string document_with(const std::string& commands)
{
    const std::string head =
        R"json({"program": "hub", "version": "1.0.0", "contract": "1", "commands": [)json";
    return head + commands + "]}";
}

/** @brief Parses @p document and fails the test with the reason when it will not parse. */
Catalogue catalogue_from_text(const std::string& document)
{
    const std::variant<Catalogue, ParseError> outcome = parse_catalogue(document);
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

/** @brief Pairs a type name the contract allows with the enumerator it must map to. */
struct TypeRow
{
    /** @brief Holds the name as the catalogue spells it. */
    const char* name;

    /** @brief Holds the enumerator the name maps to. */
    ParameterType type;
};

/** @brief Runs the name-to-type map once per row of TypeRow. */
class Small_ParameterTypeTest : public ::testing::TestWithParam<TypeRow>
{
};

/** @brief Runs the refusal check once per malformed document. */
class Small_CatalogueRefusalTest : public ::testing::TestWithParam<std::string>
{
};

}

TEST(Small_CatalogueTest, ReadsTheProgramVersionAndContract)
{
    const Catalogue catalogue = catalogue_from_text(document_with(STATUS_COMMAND));

    EXPECT_EQ(catalogue.program, "hub");
    EXPECT_EQ(catalogue.version, "1.0.0");
    EXPECT_EQ(catalogue.contract, "1");
    EXPECT_EQ(catalogue.commands.size(), 1U);
}

TEST_P(Small_ParameterTypeTest, MapsTheNameToItsEnumerator)
{
    ParameterType type = ParameterType::string;

    ASSERT_TRUE(parse_parameter_type(GetParam().name, type));
    EXPECT_EQ(type, GetParam().type);
}

INSTANTIATE_TEST_SUITE_P(ContractTypes, Small_ParameterTypeTest,
                         ::testing::Values(TypeRow{"string", ParameterType::string},
                                           TypeRow{"boolean", ParameterType::boolean},
                                           TypeRow{"integer", ParameterType::integer},
                                           TypeRow{"number", ParameterType::number},
                                           TypeRow{"path", ParameterType::path},
                                           TypeRow{"choice", ParameterType::choice}));

TEST(Small_CatalogueTest, RefusesAParameterTypeTheContractDoesNotAllow)
{
    ParameterType type = ParameterType::string;

    EXPECT_FALSE(parse_parameter_type("colour", type));
}

TEST(Small_CatalogueTest, ReadsAnArgumentsFields)
{
    const Command add = command_named(catalogue_from_text(document_with(ADD_COMMAND)), "add");

    const Parameter modules = parameter_named(add, "modules");
    EXPECT_TRUE(modules.is_argument);
    EXPECT_TRUE(modules.multiple);
    EXPECT_TRUE(modules.required);
    EXPECT_TRUE(modules.flags.empty());
    EXPECT_EQ(modules.help, "Modules to clone.");
}

TEST(Small_CatalogueTest, ReadsAnOptionsFields)
{
    const Command add = command_named(catalogue_from_text(document_with(ADD_COMMAND)), "add");

    const Parameter dry_run = parameter_named(add, "dry_run");
    EXPECT_FALSE(dry_run.is_argument);
    EXPECT_EQ(dry_run.type, ParameterType::boolean);
    ASSERT_EQ(dry_run.flags.size(), 1U);
    EXPECT_EQ(dry_run.flags[0], "--dry-run");
    EXPECT_FALSE(dry_run.default_value.get<bool>());
}

TEST(Small_CatalogueTest, ReadsAChoiceWithItsValuesAndDefault)
{
    const Command install =
        command_named(catalogue_from_text(document_with(INSTALL_COMMAND)), "install");

    const Parameter profile = parameter_named(install, "profile");
    EXPECT_EQ(profile.type, ParameterType::choice);
    ASSERT_EQ(profile.choices.size(), 3U);
    EXPECT_EQ(profile.choices[0], "debug");
    EXPECT_EQ(profile.default_value.get<std::string>(), "release");
}

TEST(Small_CatalogueTest, LeavesChoicesAndDefaultEmptyOnAParameterThatHasNone)
{
    const Command install =
        command_named(catalogue_from_text(document_with(INSTALL_COMMAND)), "install");

    const Parameter prefix = parameter_named(install, "prefix");
    EXPECT_EQ(prefix.type, ParameterType::path);
    EXPECT_TRUE(prefix.choices.empty());
    EXPECT_TRUE(prefix.default_value.is_null());
}

TEST(Small_CatalogueTest, ReadsACommandWithNoParameters)
{
    const Command status =
        command_named(catalogue_from_text(document_with(STATUS_COMMAND)), "status");

    EXPECT_TRUE(status.parameters.empty());
    EXPECT_EQ(status.applies_to.size(), 3U);
}

TEST(Medium_CatalogueTest, TheRecordedCatalogueOffersTheUpdateCheck)
{
    const Command status =
        command_named(catalogue_from_text(fixture_text("describe.json")), "status");

    const Parameter check = parameter_named(status, "check_updates");
    EXPECT_EQ(check.type, ParameterType::boolean);
    ASSERT_EQ(check.flags.size(), 1U);
    EXPECT_EQ(check.flags[0], "--check-updates");
}

TEST_P(Small_CatalogueRefusalTest, RefusesTheDocumentWithAReasonInsteadOfThrowing)
{
    const std::variant<Catalogue, ParseError> outcome = parse_catalogue(GetParam());

    ASSERT_TRUE(std::holds_alternative<ParseError>(outcome));
    EXPECT_FALSE(std::get<ParseError>(outcome).reason.empty());
}

INSTANTIATE_TEST_SUITE_P(
    BadDocuments, Small_CatalogueRefusalTest,
    ::testing::Values(
        std::string("not json at all"), std::string("[]"),
        std::string(R"json({"program":"hub","version":"1","contract":"1"})json"),
        std::string(R"json({"program":"hub","version":"1","contract":"1","commands":{}})json"),
        std::string(R"json({"program":"hub","version":"1","contract":"1","commands":[{"name":"a","help":"h","applies_to":[],"params":[{"name":"p","kind":"flag","type":"string","multiple":false,"required":false,"default":null,"choices":null,"flags":[],"help":""}]}]})json"),
        std::string(R"json({"program":"hub","version":"1","contract":"1","commands":[{"name":"a","help":"h","applies_to":[],"params":[{"name":"p","kind":"option","type":"colour","multiple":false,"required":false,"default":null,"choices":null,"flags":[],"help":""}]}]})json")));
