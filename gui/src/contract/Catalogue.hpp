/** @file Catalogue.hpp
 *  @brief Declares the command catalogue `hub --describe` prints and its parameter records.
 *  @author Mustafa Garip
 */

#pragma once

#include "contract/Event.hpp"

#include <nlohmann/json.hpp>

#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Names the six value kinds a parameter can take. */
enum class ParameterType
{
    string,
    boolean,
    integer,
    number,
    path,
    choice
};

/** @brief Describes one argument or option of one command. */
struct Parameter
{
    /** @brief Holds the parameter's name as the catalogue spells it. */
    std::string name;

    /** @brief Holds the help text shown beside the widget. */
    std::string help;

    /** @brief Records whether this is a positional argument rather than an option. */
    bool is_argument = false;

    /** @brief Records whether the parameter takes more than one value. */
    bool multiple = false;

    /** @brief Records whether the command refuses to run without it. */
    bool required = false;

    /** @brief Holds the value kind the widget must offer. */
    ParameterType type = ParameterType::string;

    /** @brief Holds the value used when the caller gives none, null when there is none. */
    nlohmann::json default_value;

    /** @brief Holds the allowed values of a choice parameter, empty for every other kind. */
    std::vector<std::string> choices;

    /** @brief Holds the option's spellings on the command line, empty for an argument. */
    std::vector<std::string> flags;
};

/** @brief Describes one command a form can be generated from. */
struct Command
{
    /** @brief Holds the subcommand name as `hub` accepts it. */
    std::string name;

    /** @brief Holds the command's first help paragraph. */
    std::string help;

    /** @brief Holds the arguments and options in the order the catalogue lists them. */
    std::vector<Parameter> parameters;

    /** @brief Holds the forms of module presence the command works on. */
    std::vector<std::string> applies_to;
};

/** @brief Holds one program's whole command catalogue. */
struct Catalogue
{
    /** @brief Holds the program name, `hub` for this contract. */
    std::string program;

    /** @brief Holds the installed distribution's version, "0" when it runs from a source tree. */
    std::string version;

    /** @brief Holds the contract version the schemas carry. */
    std::string contract;

    /** @brief Holds every command, sorted by name as the catalogue emits them. */
    std::vector<Command> commands;
};

/**
 * @brief Reads the object `hub --describe` prints into a catalogue.
 * @param json The whole catalogue document, not a stream of event lines.
 * @return The catalogue, or the reason it could not be read. Never throws.
 */
std::variant<Catalogue, ParseError> parse_catalogue(std::string_view json);

/**
 * @brief Reads a catalogue type name into the enumerator it spells.
 * @param name One of string, boolean, integer, number, path or choice.
 * @param type Receives the enumerator when the name is known.
 * @return Whether the name was one of the six the contract allows.
 */
bool parse_parameter_type(std::string_view name, ParameterType& type);

}
}
