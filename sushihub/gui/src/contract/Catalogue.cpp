/** @file Catalogue.cpp
 *  @brief Defines the reading of `ss --describe` output against the catalogue schema.
 *  @author Mustafa Garip
 */

#include "contract/Catalogue.hpp"

#include <optional>
#include <utility>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Builds the error for a key that is missing or holds the wrong type. */
ParseError bad_field(const std::string& owner, const char* key, const char* expected)
{
    return ParseError{owner + " needs a " + expected + " \"" + key + "\""};
}

/** @brief Reads the string at @p key into @p out and reports whether it was there. */
bool read_string(const nlohmann::json& object, const char* key, std::string& out)
{
    const auto found = object.find(key);
    if (found == object.end() || !found->is_string())
    {
        return false;
    }
    out = found->get<std::string>();
    return true;
}

/** @brief Reads the boolean at @p key into @p out and reports whether it was there. */
bool read_boolean(const nlohmann::json& object, const char* key, bool& out)
{
    const auto found = object.find(key);
    if (found == object.end() || !found->is_boolean())
    {
        return false;
    }
    out = found->get<bool>();
    return true;
}

/** @brief Reads the array of strings or null at @p key into @p out. */
bool read_string_array_or_null(const nlohmann::json& object, const char* key,
                               std::vector<std::string>& out)
{
    const auto found = object.find(key);
    if (found == object.end())
    {
        return false;
    }

    out.clear();
    if (found->is_null())
    {
        return true;
    }
    if (!found->is_array())
    {
        return false;
    }

    out.reserve(found->size());
    for (const nlohmann::json& element : *found)
    {
        if (!element.is_string())
        {
            return false;
        }
        out.push_back(element.get<std::string>());
    }
    return true;
}

/** @brief Reads one parameter record out of @p object into @p parameter. */
std::optional<ParseError> read_parameter(const nlohmann::json& object, const std::string& owner,
                                         Parameter& parameter)
{
    if (!object.is_object())
    {
        return ParseError{owner + " has a parameter that is not an object"};
    }
    if (!read_string(object, "name", parameter.name))
    {
        return bad_field(owner, "name", "string");
    }

    const std::string where = owner + " parameter \"" + parameter.name + "\"";

    std::string kind;
    if (!read_string(object, "kind", kind))
    {
        return bad_field(where, "kind", "string");
    }
    if (kind != "argument" && kind != "option")
    {
        return ParseError{where + " has an unknown kind \"" + kind + "\""};
    }
    parameter.is_argument = kind == "argument";

    std::string type_name;
    if (!read_string(object, "type", type_name))
    {
        return bad_field(where, "type", "string");
    }
    if (!parse_parameter_type(type_name, parameter.type))
    {
        return ParseError{where + " has an unknown type \"" + type_name + "\""};
    }

    if (!read_boolean(object, "multiple", parameter.multiple))
    {
        return bad_field(where, "multiple", "boolean");
    }
    if (!read_boolean(object, "required", parameter.required))
    {
        return bad_field(where, "required", "boolean");
    }

    const auto default_value = object.find("default");
    if (default_value == object.end())
    {
        return bad_field(where, "default", "value or null");
    }
    parameter.default_value = *default_value;

    if (!read_string_array_or_null(object, "choices", parameter.choices))
    {
        return bad_field(where, "choices", "array of strings or null");
    }
    if (!read_string_array_or_null(object, "flags", parameter.flags))
    {
        return bad_field(where, "flags", "array of strings");
    }
    if (!read_string(object, "help", parameter.help))
    {
        return bad_field(where, "help", "string");
    }

    return std::nullopt;
}

/** @brief Reads one command record out of @p object into @p command. */
std::optional<ParseError> read_command(const nlohmann::json& object, Command& command)
{
    if (!object.is_object())
    {
        return ParseError{"the catalogue has a command that is not an object"};
    }
    if (!read_string(object, "name", command.name))
    {
        return bad_field("a catalogue command", "name", "string");
    }

    const std::string owner = "command \"" + command.name + "\"";
    if (!read_string(object, "help", command.help))
    {
        return bad_field(owner, "help", "string");
    }
    if (!read_string_array_or_null(object, "applies_to", command.applies_to))
    {
        return bad_field(owner, "applies_to", "array of strings");
    }

    const auto params = object.find("params");
    if (params == object.end() || !params->is_array())
    {
        return bad_field(owner, "params", "array");
    }

    command.parameters.clear();
    command.parameters.reserve(params->size());
    for (const nlohmann::json& element : *params)
    {
        Parameter parameter;
        std::optional<ParseError> failure = read_parameter(element, owner, parameter);
        if (failure.has_value())
        {
            return failure;
        }
        command.parameters.push_back(std::move(parameter));
    }

    return std::nullopt;
}

}

bool parse_parameter_type(std::string_view name, ParameterType& type)
{
    if (name == "string")
    {
        type = ParameterType::string;
    }
    else if (name == "boolean")
    {
        type = ParameterType::boolean;
    }
    else if (name == "integer")
    {
        type = ParameterType::integer;
    }
    else if (name == "number")
    {
        type = ParameterType::number;
    }
    else if (name == "path")
    {
        type = ParameterType::path;
    }
    else if (name == "choice")
    {
        type = ParameterType::choice;
    }
    else
    {
        return false;
    }
    return true;
}

std::variant<Catalogue, ParseError> parse_catalogue(std::string_view json)
{
    const nlohmann::json document = nlohmann::json::parse(json.begin(), json.end(), nullptr, false);
    if (document.is_discarded())
    {
        return ParseError{"the catalogue is not JSON"};
    }
    if (!document.is_object())
    {
        return ParseError{"the catalogue is not a JSON object"};
    }

    Catalogue catalogue;
    if (!read_string(document, "program", catalogue.program))
    {
        return bad_field("the catalogue", "program", "string");
    }
    if (!read_string(document, "version", catalogue.version))
    {
        return bad_field("the catalogue", "version", "string");
    }
    if (!read_string(document, "contract", catalogue.contract))
    {
        return bad_field("the catalogue", "contract", "string");
    }

    const auto commands = document.find("commands");
    if (commands == document.end() || !commands->is_array())
    {
        return bad_field("the catalogue", "commands", "array");
    }

    catalogue.commands.reserve(commands->size());
    for (const nlohmann::json& element : *commands)
    {
        Command command;
        std::optional<ParseError> failure = read_command(element, command);
        if (failure.has_value())
        {
            return failure.value();
        }
        catalogue.commands.push_back(std::move(command));
    }

    return catalogue;
}

}
}
